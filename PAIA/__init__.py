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
# Built-ins
import os
import sys
from alive_progress import config_handler
from shapely import speedups

try:
    from __main__ import run
except ImportError:
    from .__main__ import run

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Workaround but not a permanent solution
# https://github.com/Toblerity/Shapely/issues/1005#issuecomment-709982861
# I don't know specifically why but it appears to have resolved itself (I recall deleting and reinstalling cleanly all
# of the dependencies but i already tried that back when i got that error so i doubt this fixed it.)
if speedups.available:
    speedups.enable()
    print('Speedups enabled')
else:
    speedups.disable()
    print('Speedups disabled')

# PRogress bar
config_handler.set_global(length=20,
                          spinner='dots_reverse',
                          unknown='long_message',
                          force_tty=True)

# Modify environement variables so shapely finds the correct proj.db file (the one from the GDAL install and not the
# POSTGRES SQL install or either one it founds)
# https://gis.stackexchange.com/questions/326968/ogr2ogr-error-1-proj-pj-obj-create-cannot-find-proj-db/334346
# TODO adapt GDAL path based on the os?
os.environ['PROJ_LIB'] = r'C:\Program Files\GDAL\projlib'
os.environ['GDAL_DATA'] = r'C:\Program Files\GDAL\gdal-data'
os.environ['GDAL_DRIVER_PATH'] = r'C:\Program Files\GDAL\gdalplugins'
os.environ['PYTHONPATH'] = r'C:\Program Files\GDAL'
