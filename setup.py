# -*-coding: utf8 -*
"""
PAIA
A tool to process data to learn more about Protected Areas Impact on Malaria Transmission

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
from os import path, getcwd
from setuptools import find_packages
from distutils.core import setup
from configparser import ConfigParser

with open("README.md", "r") as ld,\
        open("dependencies/requirements.txt", "r") as r:
    long_description = ld.read()
    requirements = r.read()

cfgparser = ConfigParser()
cfgparser.read('setup.cfg')

setup(
    name=cfgparser.get('setup', 'name'),
    version=cfgparser.get('setup', 'version'),

    author=cfgparser.get('setup', 'author'),
    author_email=cfgparser.get('setup', 'author_email'),
    url=cfgparser.get('setup', 'url'),

    description=cfgparser.get('setup', 'description'),
    long_description=long_description,
    long_description_content_type="text/markdown",

    # https://stackoverflow.com/a/26082635
    entry_points={'console_scripts': [
        'PAIA = PAIA.__main__:main',
    ]},

    install_requires=requirements,
    dependency_links=[''.join(['file:\\', path.join(getcwd(), 'dependencies')])],
    packages=find_packages(),
    requirements=requirements,
)
# # TODO Installer les dependencies de GDAL
# https://stackoverflow.com/a/45262430
