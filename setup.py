# -*-coding: utf8 -*
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

    install_requires=requirements,
    dependency_links=[''.join(['file:\\', path.join(getcwd(), 'dependencies')])],
    packages=find_packages(),
    requirements=requirements,
)
# # TODO Installer les dependencies de GDAL
# https://stackoverflow.com/a/45262430
