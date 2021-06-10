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

Shapely (GEOS)
Fiona (GDAL)
pyproj (PROJ)
rtree (libspatialindex)
psycopg2 (connect_sqlite to Postgis)
Geoalchemy2 (writing to Postgis)
geopy (geocoding)

# Plotting
matplotlib
descartes
PySAL

Geopandas
Folium
Cartopy
Pygis

sentinelsat
rasterio
"""
from os import path, system, name
from sys import argv, stderr, exit
from configparser import ConfigParser
from shlex import quote as shlex_quote
from argparse import ArgumentParser, SUPPRESS, ArgumentTypeError
# from PAIA.utils.utils import getConfigValue, setConfigValue

cfgparser = ConfigParser()
cfgparser.read(r'H:\Logiciels\0_Projets\python\PAIA\setup.cfg')

if __name__ == '__main__':
    # Clean the terminal then print the ascii ascii_art
    system(shlex_quote('cls' if name == 'nt' else 'clear'))

    # Modify the ArgumentParser class so it prints help whenever an error occured (For example, no arguments error)
    class ArgumentParser(ArgumentParser):
        def error(self, message):
            stderr.write('error: %s\n' % message)
            self.print_help()
            exit(2)

    def dir_path(dirpath):
        normalized_dirpath = path.normpath(dirpath)
        if path.isdir(normalized_dirpath):
            return normalized_dirpath
        else:
            raise ArgumentTypeError('"{}" is not a valid path {}'.format(dirpath, '\n'))

    parser = ArgumentParser(prog='$ python {}'.format(cfgparser.get('setup', 'name')),
                            description='',
                            add_help=False,
                            epilog='\n')

    # Create the arguments
    parser.add_argument("-h", "--help",
                        action="help", default=SUPPRESS,
                        help="'Show this help message and exit.")
    parser.add_argument("-d", "--description", dest='description',
                        action="store_true", default=SUPPRESS,
                        help="Show the program's description and exit.")
    parser.add_argument("-l", "--license", dest='license',
                        action="store_true", default=SUPPRESS,
                        help="Show the program's license and exit.")
    parser.add_argument('-c', '--config',
                        nargs='?', type=str,
                        help='Read or overwrite local config file.')
    parser.add_argument('-aoi', '--aoi',
                        nargs='?', type=dir_path,
                        help='Shapefile of the area(s) of interest you want to process')

    # If no arguments are given, print the help
    if len(argv) == 1:
        parser.print_help(stderr)
        exit(1)

    # Parse the arguments
    args = parser.parse_args()

    # Based on the dest vars execute methods with the arguments
    try:
        if args.license:
            print(cfgparser.get('metadata', 'short_license'))
        elif args.description:
            print(cfgparser.get('setup', 'description'))
    except AttributeError:
        parser.print_help(stderr)
        exit(1)
