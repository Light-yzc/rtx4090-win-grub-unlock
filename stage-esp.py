"""Stage ESP directory tree and GRUB configuration for RTX 4090 Windows UEFI Unlock.

Validates all 5 firmware asset SHA-256 digests against source/unlock/app_io.c pins,
copies the compiled BOOTX64.EFI and firmware assets into dist/esp/, and generates
dist/grub/grub-unlock-entry.cfg and dist/grub/five-entry-menu.cfg.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

EXPECTED_ASSETS = {
    "booter_load_ad102.bin": (
        57672,
        "6ee05b20e1dc244c08c052f36ef28469b8d09f4955d1fe33e48a179e11a7fd49",
    ),
    "v67-ad102-610.43.03-four-plm.bin": (
        64000,
        "44c36b2d6b3424e53e18f3e55db85c833655de071ce66ce42749588a4a7dc8cb",
    ),
    "gsp_ga10x.bin": (
        84277400,
        "572373620a37418f24dc16b5031c39338778c3257e48e8408de9a57291b24f3a",
    ),
    "gsp_boot_ad102.bin": (
        36864,
        "45d6335a8185d6ff13e8d1484cea73f68d3d13aa1c19dc080ed1c3482dd5bac0",
    ),
    "gsp_boot_desc_ad102.bin": (
        84,
        "83f8f3f1f5f9496e0ea8fc7103c2beb64d0b6de2f5ffe725f13514de5a95fa42",
    ),
}

GRUB_ENTRY_TEMPLATE = """menuentry 'Windows Boot Manager - RTX 4090 FP32ACC Unlock (on /dev/nvme0n1p3)' --class windows --class os --id rtx4090-windows-unlock {{
    insmod part_gpt
    insmod fat
    insmod chain
    search --no-floppy --fs-uuid --set=unlock {esp_uuid}
    chainloader ($unlock)/EFI/RTX4090-UNLOCK/BOOTX64.EFI
}}
"""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--efi",
        type=Path,
        default=here / "source" / "build" / "BOOTX64.EFI",
        help="Path to compiled BOOTX64.EFI",
    )
    parser.add_argument(
        "--assets",
        type=Path,
        default=here.parent / "private-assets",
        help="Directory containing the 5 required firmware assets",
    )
    parser.add_argument(
        "--esp-uuid",
        default="04BD-5D39",
        help="FAT32 volume serial / UUID of the target ESP partition",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=here / "dist",
        help="Output staging directory",
    )
    args = parser.parse_args()

    if not args.efi.exists():
        raise SystemExit(
            f"Missing {args.efi}. Build first with: python build.py --enable-experiment"
        )

    esp_root = args.out / "esp"
    efi_dst = esp_root / "EFI" / "RTX4090-UNLOCK" / "BOOTX64.EFI"
    assets_dst = esp_root / "RTX4090-UNLOCK" / "ASSETS"
    grub_dst = args.out / "grub"

    efi_dst.parent.mkdir(parents=True, exist_ok=True)
    assets_dst.mkdir(parents=True, exist_ok=True)
    grub_dst.mkdir(parents=True, exist_ok=True)

    shutil.copy2(args.efi, efi_dst)

    manifest = {
        "efi": {
            "path": "EFI/RTX4090-UNLOCK/BOOTX64.EFI",
            "size": efi_dst.stat().st_size,
            "sha256": sha256_file(efi_dst),
        },
        "assets": {},
    }

    for name, (expected_size, expected_hash) in EXPECTED_ASSETS.items():
        src = args.assets / name
        if not src.exists():
            raise SystemExit(f"Missing required firmware asset: {src}")
        actual_size = src.stat().st_size
        actual_hash = sha256_file(src)
        if actual_size != expected_size or actual_hash != expected_hash:
            raise SystemExit(
                f"Asset mismatch for {name}: got size={actual_size} sha256={actual_hash}, "
                f"expected size={expected_size} sha256={expected_hash}"
            )
        dst = assets_dst / name
        shutil.copy2(src, dst)
        manifest["assets"][name] = {
            "path": f"RTX4090-UNLOCK/ASSETS/{name}",
            "size": actual_size,
            "sha256": actual_hash,
        }

    entry_text = GRUB_ENTRY_TEMPLATE.format(esp_uuid=args.esp_uuid)
    (grub_dst / "grub-unlock-entry.cfg").write_text(
        entry_text, encoding="utf-8", newline="\n"
    )
    (grub_dst / "40_custom_rtx4090_unlock").write_text(
        "#!/bin/sh\nexec tail -n +3 $0\n# This file provides the RTX 4090 Windows UEFI Unlock menuentry.\n"
        + entry_text,
        encoding="utf-8",
        newline="\n",
    )

    four_entry = here.parent / "probe-internal" / "four-entry-menu.cfg"
    if four_entry.exists():
        base_cfg = four_entry.read_text(encoding="utf-8")
        if "rtx4090-windows-unlock" not in base_cfg:
            five_cfg = base_cfg.rstrip() + "\n" + entry_text
        else:
            five_cfg = base_cfg
        (grub_dst / "five-entry-menu.cfg").write_text(
            five_cfg, encoding="utf-8", newline="\n"
        )

    (args.out / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
