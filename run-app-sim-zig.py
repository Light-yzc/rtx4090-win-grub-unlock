"""Run the application integration suite with fake UEFI and GPU services."""
import subprocess
from pathlib import Path

here = Path(__file__).resolve().parent
source = here / 'source'
zig = here.parent / 'toolchain' / 'ziglang' / 'zig.exe'
out = source / 'test-build'
out.mkdir(exist_ok=True)
flags = ['-target','x86_64-windows-gnu','-std=c11','-fshort-wchar','-O1','-Wall','-Wextra','-Werror',
         '-Wno-unused-parameter','-Wno-unused-function','-Wno-unused-variable','-Wno-misleading-indentation',
         '-Wno-format','-D__KERNEL__','-DGU_UEFI_PORT','-DKOH_ENABLE_EXPERIMENT=1','-DKOH_HOST_TEST=1',
         '-DGU_TARGET_PCI_ID=0x268410deU','-Iunlock','-Iunlock/compat',
         '-Ideps/edk2/MdePkg/Include','-Ideps/edk2/MdePkg/Include/X64']
names = ['app','app_io','ownership','format','sha256','checks','port','compat','vendor/unlock_610',
         'vendor/prep_610','vendor/layout_610','vendor/vbios_610','vendor/gfw_eval']
exe = out / 'app.exe'
subprocess.run([str(zig),'cc',*flags,'unlock/tests/test_ad103_app.c',
                *['unlock/'+name+'.c' for name in names],'-o',str(exe)],cwd=source,check=True)
base = here.parent
args = [base/'private-captures/profile-inputs/physical-prom.bin',base/'private-assets',
        base/'private-captures/profile-inputs/pci-config-256.bin',base/'private-captures/profile-inputs']
result = subprocess.run([str(exe),*map(str,args)],cwd=source,text=True,
                        stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(out/'app-sim.log').write_text(result.stdout,encoding='utf-8')
if result.returncode:
    print(result.stdout[-10000:])
    raise SystemExit(result.returncode)
print(result.stdout.splitlines()[-1])
