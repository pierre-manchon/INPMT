import subprocess
import setuptools
print('Installing dependencies...')
# https://stackoverflow.com/a/4038991
subprocess.run(['powershell.exe', 'Set-ExecutionPolicy RemoteSigned -Scope CurrentUser'])
subprocess.run(['powershell.exe', 'dependencies/install.ps1'])
subprocess.run(['powershell.exe', 'Set-ExecutionPolicy Restricted'])
print('Done')
setuptools.setup()
