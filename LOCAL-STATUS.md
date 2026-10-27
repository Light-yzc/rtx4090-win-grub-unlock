# AD102 Port Verification Status

## 1. Current Readiness Summary

The Windows UEFI + GRUB unlock port for RTX 4090 (`10de:2684`) is feature-complete, verified against the full offline simulation suite, and hardware-validated via cold-boot GRUB handoff to Windows.

- **Target GPU**: NVIDIA GeForce RTX 4090 (`10de:2684`, subsystem `10de:xxxx`, rev `a1`, PCI `0000:01:00.0`)
- **Secondary Display (iGPU)**: Integrated Graphics (`8086:xxxx`) permitted in `DisplayCheck()`
- **Cached EFI ROM & 1 MiB Physical PROM**: Pinned by SHA-256 in `source/unlock/app.c` and `source/unlock/prom_profile.h`
- **UEFI Driver Ownership & Code Hash Pinning**:
  - Target GPU controller has 1 active child handle with `SimpleTextOut`, `GraphicsOutput`, and `EdidDiscovered` protocols.
  - All 4 UEFI driver PE code sections (`DriverPins[0..3]` in `source/unlock/ownership.c`) are pinned by `ImageSize`, `SizeOfCode`, and SHA-256 digest and verified prior to disconnecting the GOP driver.
- **Target ESP Partition**:
  - Configured locally in gitignored `source/unlock/local/local_profile.h` (public `source/unlock/local_profile.h` stays safe and inert by default).

## 2. Offline & Hardware Verification Results

1. **Core State Machine Simulation (`python run-core-sim-zig.py`)**:
   - **PASS**: 43 / 43 AD102 core scenarios passed (PCI, MMIO, DMA, WPR2, FWSEC-FRTS, Booter Load, SEC2 4-PLM unlock, `SS0=0x88888888`/`SS1=0x8`, and PCIe FLR).
2. **Full UEFI Application Simulation (`python run-app-sim-zig.py`)**:
   - **PASS**: 51 / 51 app + core scenarios, 2 child-graph mutation refusal cases, 4 driver PE code-hash mutation refusal cases, and 7 policy/topology security cases passed.
3. **Hardware Cold-Boot Unlock & Windows Handoff**:
   - **PASS**: `POST-FLR SS0=0x88888888 SS1=0x00000008`, `POST-GOP SS0=0x88888888 SS1=0x00000008`, `FINAL status=0 stage=post-unlock-handoff attempted=1 driver_release=1 clean=1`.
   - **Tensor Core Benchmark (`python bench-gemm.py`)**: Full-rate FP16/BF16 -> FP32 accumulate (~300-327 TFLOPS) and TF32 -> FP32 accumulate (~163.5 TFLOPS) verified on Windows.
