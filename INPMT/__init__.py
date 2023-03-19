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
# Built-ins
import os
import sys

# 3rd party
import alive_progress

# 1st party
try:
    from __main__ import run
    from _version import __version__
except ImportError:
    from INPMT.__main__ import run
    from INPMT._version import __version__


# If the python version is too old, the code will not execute
if f"{sys.version_info[0]}.{sys.version_info[1]}" != "3.10":
    raise Exception("Python 3.10 is required.")

# To avoid writing venv's python path everytime
# Might be overridden by the setup.py entry points
os.environ["PATH"] = sys.executable

__file__ = sys.modules[__name__]
__doc__ = sys.modules[__name__].__doc__

__all__ = (
    "__doc__",
    "__version__",
    "run",
)

# Progress bar settings
alive_progress.config_handler.set_global(length=20, force_tty=True)
