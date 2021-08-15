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
from configparser import ConfigParser as __ConfigParser

# Built-ins
from os import environ as __environ
from sys import executable as __executable
from sys import modules as __modules
from sys import version_info as __version_info
from shapely import speedups

from alive_progress import config_handler as __config_handler

try:
    from __main__ import run
    from __utils.utils import __set_cfg_val as set_config_value
except ImportError:
    from .__main__ import run
    from .__utils.utils import __set_cfg_val as set_config_value


def get_config():
    """
    Open and view the config file
    """
    with open('INPMT/config.cfg', "r") as cfg:
        print(cfg.read())


# Si la version de python est trop ancienne, le code ne s'execute
__current_python_version = "{}.{}".format(__version_info[0], __version_info[1])
if __current_python_version != "3.9":
    raise Exception("Python 3.9 is required.")

# To avoid writing venv's python path everytime
# Might be overridden by the setup.py entry points
__environ["PATH"] = __executable

__cfgparser = __ConfigParser()
__cfgparser.read("setup.cfg")

__package__ = __cfgparser.get("setup", "name")
__file__ = __modules[__name__]
__doc__ = __modules[__name__].__doc__
__version__ = __cfgparser.get("setup", "version")
__license__ = __cfgparser.get("setup", "license")
__author__ = __cfgparser.get("setup", "author")
__email__ = __cfgparser.get("setup", "author_email")

__all__ = (
    "__package__",
    "__doc__",
    "__version__",
    "__license__",
    "__author__",
    "__email__",
    "run",
)

# Workaround but not a permanent solution
# https://github.com/Toblerity/Shapely/issues/1005#issuecomment-709982861
# I don't know specifically why but it appears to have resolved itself (I recall deleting and reinstalling cleanly all
# of the dependencies but i already tried that back when i got that error so i doubt this fixed it.)
# Made as a function to be hidden on import
if speedups.available:
    speedups.enable()
    print("Speedups: {}".format(speedups.available))
else:
    speedups.disable()
    print("Speedups: {}".format(speedups.available))

# Modify environement variables so shapely finds the correct proj.db file (the one from the GDAL install and not the
# POSTGRES SQL install or either one it founds)
# https://gis.stackexchange.com/questions/326968/ogr2ogr-error-1-proj-pj-obj-create-cannot-find-proj-db/334346
# TODO adapt GDAL path based on the os?
__environ["PROJ_LIB"] = r"C:\Program Files\GDAL\projlib"
__environ["GDAL_DATA"] = r"C:\Program Files\GDAL\gdal-data"
__environ["GDAL_DRIVER_PATH"] = r"C:\Program Files\GDAL\gdalplugins"
__environ["PYTHONPATH"] = r"C:\Program Files\GDAL"

# Progress bar settings
__config_handler.set_global(length=20, spinner="dots_reverse", unknown="long_message", force_tty=True)
