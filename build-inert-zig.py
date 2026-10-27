"""Build the default-inert EFI only. Never enables, installs, or executes it."""
import hashlib
import json
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
root = here / 'source'
zig = here.parent / 'toolchain' / 'ziglang' / 'zig.exe'
out = root / 'build-inert'
out.mkdir(exist_ok=True)
names = ['app','app_io','ownership','format','runtime','sha256','checks','port','compat',
         'vendor/unlock_610','vendor/prep_610','vendor/layout_610','vendor/vbios_610','vendor/gfw_eval']
flags = ['-target','x86_64-windows-gnu','-c','-std=c11','-ffreestanding','-fno-builtin',
         '-fno-stack-protector','-mno-stack-arg-probe','-mno-red-zone','-fshort-wchar',
         '-Os','-Wall','-Wextra','-Werror','-Wno-unused-parameter',
         '-D__KERNEL__','-DGU_UEFI_PORT','-DGU_TARGET_PCI_ID=0x268410deU',
         '-Iunlock','-Iunlock/compat','-Ideps/edk2/MdePkg/Include','-Ideps/edk2/MdePkg/Include/X64']
objects = []
for name in names:
    obj = out / (name.replace('/','_') + '.obj')
    subprocess.run([str(zig),'cc',*flags,'unlock/'+name+'.c','-o',str(obj)], cwd=root, check=True)
    objects.append(str(obj))
efi = out / 'INERT-AD102.EFI'
subprocess.run([str(zig),'cc','-target','x86_64-windows-gnu','-nostdlib',
                '-Wl,--subsystem,efi_application',*objects,'-o',str(efi)], cwd=root, check=True)
print(json.dumps({'sha256':hashlib.sha256(efi.read_bytes()).hexdigest(),
                  'bytes':efi.stat().st_size,'execution_enabled':False,
                  'hardware_tested':False},indent=2))
