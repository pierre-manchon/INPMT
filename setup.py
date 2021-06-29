# -*-coding: utf8 -*
"""
INPMT
A tool to process data to learn more about Impact of National Parks on Malaria Transmission

Copyright (C) <2021>  <Manchon Pierre>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import pip
from configparser import ConfigParser
from setuptools import find_packages
from setuptools.command.install import install as _install

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open("README.md", "r") as ld,\
        open("dependencies/requirements.txt", "r") as r:
    long_description = ld.read()
    requirements = r.read().split('\n')

cfgparser = ConfigParser()
cfgparser.read('setup.cfg')
entry_point = ''.join([cfgparser.get('setup', 'name'), '=', cfgparser.get('setup', 'name'), '.__main__:main'])


def getWheels():
    dependency = []
    for _, _, files in os.walk(os.path.join(os.getcwd(), 'dependencies')):
        for file in files:
            dependency.append(''.join(['file:\\', os.path.join(os.getcwd(), 'dependencies', file)]))
    return dependency


class install(_install):
    """
    Workaround to install local dependencies taken from there:

    https://stackoverflow.com/a/45262430
    """
    def run(self):
        _install.do_egg_install(self)
        for x in getWheels():
            # just go ahead and do it
            pip.main(['install', x])


setup(
    name=cfgparser.get('setup', 'name'),
    version=cfgparser.get('setup', 'version'),
    license=cfgparser.get('setup', 'license'),

    author=cfgparser.get('setup', 'author'),
    author_email=cfgparser.get('setup', 'author_email'),
    url=cfgparser.get('setup', 'url'),

    description=cfgparser.get('setup', 'description'),
    long_description=long_description,
    long_description_content_type="text/markdown",

    classifiers=[
        # How mature is this project? Common values are
        #   1 - Planning
        #   2 - Pre-Alpha
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        #   6 - Mature
        #   7 - Inactive
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Information Technology',
        "Topic :: Scientific/Engineering :: GIS",
        "Topic :: Scientific/Engineering :: Visualization",
        'Topic :: Scientific/Engineering :: Information Analysis',

        'Natural Language :: English',
        'Environment :: Console',
        "Operating System :: OS Independent",

        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3.9"],

    keywords=["gis",
              "gis-utils",
              "tools"],

    # https://stackoverflow.com/a/26082635
    entry_points={'console_scripts': [entry_point]},

    packages=find_packages(),
    requirements=requirements,
    install_requires=requirements,
    python_requires=cfgparser.get('setup', 'python_requires'),
    # https://stackoverflow.com/questions/55208309/installing-data-files-in-setup-py-with-pip-install-e
    # data_files=[('', ['LICENSE'])],
    # dependency_links=getWheels(),
    cmdclass={'install': install}
)
