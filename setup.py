import subprocess
import setuptools
subprocess.call(['sh', 'dependencies/install.sh'])
setuptools.setup()
