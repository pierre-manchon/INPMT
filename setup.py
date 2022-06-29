import subprocess
import setuptools

subprocess.call(['sh', './dependencies/install.sh'], shell=True)
setuptools.setup()
