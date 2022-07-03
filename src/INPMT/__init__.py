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
import configparser

# Built-ins
import os
import sys

# 3rd party
import alive_progress
from shapely import speedups

# 1st party
try:
    from __main__ import run
    from _version import __version__
    from utils.utils import __set_cfg_val as set_config_value
except ImportError:
    from .__main__ import run
    from ._version import __version__
    from .utils.utils import __set_cfg_val as set_config_value


def get_config():
    """
    Open and view the config file
    """
    with open("INPMT/config.cfg", "r") as cfg:
        print(cfg.read())


# If the python version is too old, the code will not execute
if f"{sys.version_info[0]}.{sys.version_info[1]}" != "3.10":
    raise Exception("Python 3.10 is required.")

# To avoid writing venv's python path everytime
# Might be overridden by the setup.py entry points
os.environ["PATH"] = sys.executable

cfgparser = configparser.ConfigParser()
cfgparser.read("setup.cfg")

__package__ = cfgparser.get("metadata", "name")
__file__ = sys.modules[__name__]
__doc__ = sys.modules[__name__].__doc__
__license__ = cfgparser.get("metadata", "license")
__author__ = cfgparser.get("metadata", "author")
__email__ = cfgparser.get("metadata", "author_email")

__all__ = (
    "__package__",
    "__doc__",
    "__version__",
    "__license__",
    "__author__",
    "__email__",
    "run",
    "get_config",
    "set_config_value",
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

# Modify environment variables so shapely finds the correct proj.db file (the one from the GDAL install and not the
# POSTGRES SQL install or either one it founds)
# https://gis.stackexchange.com/questions/326968/ogr2ogr-error-1-proj-pj-obj-create-cannot-find-proj-db/334346
# TODO adapt GDAL path based on the os?
os.environ["PROJ_LIB"] = r"C:\Program Files\GDAL\projlib"
os.environ["GDAL_DATA"] = r"C:\Program Files\GDAL\gdal-data"
os.environ["GDAL_DRIVER_PATH"] = r"C:\Program Files\GDAL\gdalplugins"
os.environ["PYTHONPATH"] = r"C:\Program Files\GDAL"

# Progress bar settings
alive_progress.config_handler.set_global(length=20, force_tty=True)
