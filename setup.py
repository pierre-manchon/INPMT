import subprocess
import setuptools
print('Installing dependencies...')
subprocess.run(['powershell.exe', 'dependencies/install.ps1'])
print('Done')
setuptools.setup()
