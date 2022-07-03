import sys
import subprocess
import setuptools
# https://stackoverflow.com/a/4038991
if sys.platform == 'win32' or sys.platform == 'win64':
	subprocess.run(['powershell.exe', 'Set-ExecutionPolicy RemoteSigned -Scope CurrentUser'])
	subprocess.run(['powershell.exe', 'dependencies/install.ps1'])
	subprocess.run(['powershell.exe', 'Set-ExecutionPolicy Restricted'])
else:
	subprocess.run('dependencies/install.sh', shell=True)
setuptools.setup()
