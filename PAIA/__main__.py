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
import argparse
from os import path, system, name
from sys import argv, stderr, exit
from typing import AnyStr
from configparser import ConfigParser
from shlex import quote as shlex_quote
from argparse import ArgumentTypeError
from utils.utils import setConfigValue
# from categories import app

cfgparser = ConfigParser()
cfgparser.read('setup.cfg')


def main():
    # Clean the terminal then print the ascii ascii_art
    system(shlex_quote('cls' if name == 'nt' else 'clear'))

    class ArgumentParser(argparse.ArgumentParser):
        """Object for parsing command line strings into Python objects.
        Overridden to print the help whenever an error occured (For example, no arguments error)

        Keyword Arguments:
            - prog -- The name of the program (default: sys.argv[0])
            - usage -- A usage message (default: auto-generated from arguments)
            - description -- A description of what the program does
            - epilog -- Text following the argument descriptions
            - parents -- Parsers whose arguments should be copied into this one
            - formatter_class -- HelpFormatter class for printing help messages
            - prefix_chars -- Characters that prefix optional arguments
            - fromfile_prefix_chars -- Characters that prefix files containing
                additional arguments
            - argument_default -- The default value for all arguments
            - conflict_handler -- String indicating how to handle conflicts
            - add_help -- Add a -h/-help option
            - allow_abbrev -- Allow long options to be abbreviated unambiguously
            - exit_on_error -- Determines whether or not ArgumentParser exits with
                error info when an error occurs
        """
        def error(self, message):
            stderr.write('error: %s\n' % message)
            self.print_help()
            exit(2)

    def file_path(dirpath: AnyStr) -> AnyStr:
        """
        Returns a path only if it is a valid one

        :param dirpath:
        :type dirpath AnyStr
        :return: normalized_filepath
        :rtype normalized_filepath AnyStr
        """
        normalized_filepath = path.normpath(dirpath)
        if path.isfile(normalized_filepath):
            return normalized_filepath
        else:
            raise ArgumentTypeError('"{}" is not a valid path {}'.format(dirpath, '\n'))

    parser = ArgumentParser(prog='$ python {}'.format(cfgparser.get('setup', 'name')),
                            description='',
                            add_help=False,
                            epilog='\n')

    # Create the arguments
    parser.add_argument("-h", "--help",
                        action="help",
                        help="Show this help message and exit.")
    parser.add_argument("-d", "--description", dest='description',
                        action="store_true",
                        help="Show the program's description and exit.")
    parser.add_argument("-l", "--license", dest='license',
                        action="store_true",
                        help="Show the program's license and exit.")
    parser.add_argument('-c', '--config',
                        nargs='*', type=str,
                        help='Read or overwrite local config file.')
    parser.add_argument('-aoi', '--aoi',
                        nargs='?', type=file_path,
                        help='Shapefile of the area(s) of interest you want to process')

    # If no arguments are given, print the help
    if len(argv) == 1:
        parser.print_help(stderr)
        exit(1)

    # Parse the arguments
    args = parser.parse_args()

    # Based on the dest vars execute methods with the arguments
    try:
        if args.license is True:
            print(cfgparser.get('metadata', 'short_license'))
        elif args.description is True:
            print(cfgparser.get('setup', 'description'))
        elif args.config is not None:
            if len(args.config) == 2:
                var, value = args.config
                setConfigValue(var, value)
            elif len(args.config) == 0:
                with open('PAIA/config.cfg', 'r') as cfg:
                    print(cfg.read())
        elif args.aoi:
            print(args.aoi)
            # TODO Python pointe vers les modules globauc au lieu de pointer vers les modules de l'environnement virtuel
            # app(aoi=args.aoi)
    except AttributeError:
        parser.print_help(stderr)
        exit(1)


# Execute outside the if __name__ == '__main__' because I the main function to be accessible from the entry point in
# setup.py
main()
