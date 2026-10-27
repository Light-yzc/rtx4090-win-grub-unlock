"""Run CPU-only transaction simulations using private local fixtures."""
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
source = here / 'source'
zig = here.parent / 'toolchain' / 'ziglang' / 'zig.exe'
out = source / 'test-build'
out.mkdir(exist_ok=True)
exe = out / 'core.exe'
flags = ['-target','x86_64-windows-gnu','-std=c11','-fshort-wchar','-O1',
         '-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-unused-function',
         '-Wno-misleading-indentation','-Wno-format','-D__KERNEL__','-DGU_UEFI_PORT',
         '-DKOH_ENABLE_EXPERIMENT=1','-DGU_TARGET_PCI_ID=0x268410deU',
         '-Iunlock','-Iunlock/compat','-Ideps/edk2/MdePkg/Include','-Ideps/edk2/MdePkg/Include/X64']
names = ['port','compat','vendor/unlock_610','vendor/prep_610','vendor/layout_610',
         'vendor/vbios_610','vendor/gfw_eval']
subprocess.run([str(zig),'cc',*flags,'unlock/tests/test_ad102_transaction.c',
                *['unlock/'+name+'.c' for name in names],'-o',str(exe)],cwd=source,check=True)
prom = here.parent / 'private-captures' / 'profile-inputs' / 'physical-prom.bin'
assets = here.parent / 'private-assets'
result = subprocess.run([str(exe),str(prom),str(assets)],cwd=source,check=True,
                        text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(out / 'core-sim.log').write_text(result.stdout,encoding='utf-8')
print(result.stdout.splitlines()[-1])
