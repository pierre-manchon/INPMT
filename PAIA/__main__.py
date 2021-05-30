# -*-coding: utf8 -*
"""
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

cfgparser = ConfigParser()
cfgparser.read('setup.cfg')

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
            raise ArgumentTypeError('[PAIA]: "{}" is not a valid path {}'.format(dirpath, '\n'))

    parser = ArgumentParser(prog='$ python {}'.format(cfgparser.get('setup', 'name')),
                            description='',
                            add_help=False,
                            epilog='\n')

    # Create the arguments
    parser.add_argument("-h", "--help",
                        action="help", default=SUPPRESS,
                        help="'Show this help message and exit.")
    parser.add_argument("-d", "--description",
                        action="store_true", default=SUPPRESS,
                        help="Show the program's description and exit.")
    parser.add_argument("-__ctr", "--license",
                        action="store_true", default=SUPPRESS,
                        help="Show the program's license and exit.")
    parser.add_argument('-c', '--config',
                        nargs='?', type=str,
                        help='Shapefile of the area of interest you want to process')
    parser.add_argument('-i', '--indicator',
                        nargs='?', type=str,
                        help='Shapefile of the area of interest you want to process')
    parser.add_argument('-aoi', '--aoi',
                        nargs='?', type=dir_path,
                        help='Shapefile of the area of interest you want to process')

    # If no arguments are given, print the help
    if len(argv) == 1:
        parser.print_help(stderr)
        exit(1)

    # Parse the arguments
    args = parser.parse_args()

    # Based on the dest vars execute methods with the arguments
    if args.aoi is not None:
        aoi = args.aoi
    else:
        aoi = None
    if args.indicator is not None:
        indicator = args.indicator
    else:
        indicator = 'all'

    print("[PAIA]: Area of interest: {}, Indicator: {}".format(aoi, indicator))
