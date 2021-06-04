# -*-coding: utf8 -*
# Built-ins
from os import environ
from shapely import speedups
from alive_progress import config_handler

# Workaround but not a permanent solution
# https://github.com/Toblerity/Shapely/issues/1005#issuecomment-709982861
# TODO Correct GEOS Error
if speedups.available:
    speedups.enable()
else:
    speedups.disable()

# PRogress bar
config_handler.set_global(length=20,
                          spinner='dots_reverse',
                          unknown='long_message',
                          force_tty=True)

# Modify environement variables so shapely finds the correct proj.db file (the one from the GDAL install and not the
# POSTGRES SQL install or either one it founds)
# https://gis.stackexchange.com/questions/326968/ogr2ogr-error-1-proj-pj-obj-create-cannot-find-proj-db/334346
# TODO adapt GDAL path based on the os?
environ['PROJ_LIB'] = r'C:\Program Files\GDAL\projlib'
environ['GDAL_DATA'] = r'C:\Program Files\GDAL\gdal-data'
environ['GDAL_DRIVER_PATH'] = r'C:\Program Files\GDAL\gdalplugins'
environ['PYTHONPATH'] = r'C:\Program Files\GDAL'
