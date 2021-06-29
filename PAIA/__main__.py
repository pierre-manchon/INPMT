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


Tox: tests CI
Jenkins: Open source automation server
Devpi: PyPI server and packaging/testing/release tool

get_distances(pas=gdf_pa,
              urban_areas=gdf_urbain_gabon,
              path_urban_areas=path_urbain_gabon,
              export=True)
df, sf = read_shapefile_as_dataframe(path_country_boundaries)

In case the following contraption doesn'u work, this allows to get coordinates
for v in sf.__geo_interface__['features']:
    shape = v['geometry']['coordinates']

for x in zip(df.NAME, df.AREA, df.coords):
    if x[0] != '':
        cr = raster_crop(dataset=path_occsol, geodataframe=sf.shp.name)
        get_pixel_diversity(dataset=cr, shapefile_area=x[1], band=0)
        # plot_shape(geodataframe=sf, dataframe=df, name=x)
    else:
        pass

https://automating-gis-processes.github.io/2017/lessons/L3/nearest-neighbour.html

https://stackoverflow.com/questions/39995839/gis-calculate-distance-between-point-and-polygon-border
load every layers
Illustrer difference Gabon/Afrique (proportion occsol/pays = Surface catégories/surface pays)
Stats pour Afrique, Zone présence Anophèles, Pays (polygonize dominant vectors)
Lister lesx variables calculables: proportion par buffer
Lien proximité/pop/parcs/anophèles

QGIS
Convertir les pixels urbains de l'occsol en polygone
CODE
Convertir ces polygones en mono parties.
Associer puis séparer les villages gros des villages petits.

Dans le premier cas, mesurer dans un premier temps la distance entre le bord de l'aire urbaine et le parc.
Dans le second cas, utiliser le centroïde pour ensuite mesurer la distance avec la bordure du parc.
=> Puis, dans un second temps, mesurer au sein de cellules/patchs la fragmentation des tâches urbaines.


path_occsol = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Occupation du sol/Produit OS/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7/' \
              r'ESACCI-LC-L4-LCCS-Map-300m-P1Y-1992_2015-v2.0.7_AFRICA.tif'
path_population = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Population/population_dataset/' \
                  r'gab_ppp_2020_UNadj_constrained.tif'
path_country_boundaries = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/' \
                          r'Limites administratives/african_countries_boundaries.shp'
path_decoupage = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/Administratif/decoupe_3857.shp'


# Intersect and crop every layers with the area of interest
gdf_anos_aoi, path_anos_aoi = intersect(base=path_anopheles,
                                        overlay=aoi,
                                        crs=3857,
                                        export=True)

gdf_urban_aoi, path_urban_aoi = intersect(base=path_urbain,
                                          overlay=aoi,
                                          crs=3857,
                                          export=True)

path_occsol_aoi = raster_crop(dataset=path_occsol_degrade, shapefile=aoi)

# Keep all the PAs where there is population
gdf_pa_aoi_anos_pop = is_of_interest(base=gdf_pa_aoi, interest=gdf_urban_aoi)

# Keep all the buffers of the PAs where there is anopheles and population. I process a buffer of 1m so the
# polygons intersects otherwise they would just be next ot each other.
gdf_pa_aoi_anos_pop_buffer_tmp = gdf_pa_aoi.buffer(1)
gdf_pa_buffered_aoi_anos_pop = is_of_interest(base=gdf_pa_aoi, interest=gdf_pa_aoi_anos_pop_buffer_tmp)
"""
import argparse
from shutil import rmtree
from os import path, system, name
from sys import argv, stderr, exit
from typing import AnyStr
from geopandas import GeoDataFrame
from configparser import ConfigParser
from shlex import quote as shlex_quote
from argparse import ArgumentTypeError

try:
    from __processing import get_profile
    from __utils.utils import __getConfigValue, __setConfigValue, format_dataset_output
    from __utils.vector import __read_shapefile_as_geodataframe
except ImportError:
    from .__processing import get_profile
    from .__utils.utils import __getConfigValue, __setConfigValue, format_dataset_output
    from .__utils.vector import __read_shapefile_as_geodataframe

cfgparser = ConfigParser()
cfgparser.read('setup.cfg')
config_file_path = ''.join([cfgparser.get('setup', 'name'), '/config.cfg'])

# Really not important tho
# Use the qgis project to get the list of files and the list of legend files
# TODO Use a list of files to unpack rather than multiple line vars
# Appears to be impossible due to qgz project file being a binary type file


def run(aoi: AnyStr,
        processing_dir: AnyStr = './.processing/',
        export: bool = False
        ) -> GeoDataFrame:
    """
    path_urbain =  r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/0/pop_polygonized_taille.shp'
    :param aoi:
    :type aoi:
    :param processing_dir:
    :type processing_dir:
    :param export:
    :type export:
    :return:
    :rtype:
    """
    datasets = __getConfigValue('datasets_storage_path')

    # population = path.join(datasets, 'UNadj_constrained_merged_degraded.tif')
    landuse = path.join(datasets, 'ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif')
    anopheles_kyalo = path.join(datasets, 'VectorDB_1898-2016.shp')
    # countries_irish = path.join(datasets, 'africa_countries_irish_tmp.shp')
    # protected_areas = path.join(datasets, 'WDPA_Africa_anopheles.shp')
    # protected_areas_buffered = path.join(datasets, 'WDPA_Africa_anopheles_buffer10km.shp')
    # TODO Polygonize population
    # TODO Polygonize Land Use

    # Read file as a geodataframe
    gdf_aoi = __read_shapefile_as_geodataframe(aoi)
    gdf_profiles_aoi, path_profiles_aoi = get_profile(geodataframe_aoi=gdf_aoi,
                                                      aoi=aoi,
                                                      landuse=landuse,
                                                      anopheles=anopheles_kyalo)
    # Clean the processing directory
    rmtree(processing_dir)
    if export:
        # Retrieves the directory the dataset is in and joins it the output filename
        _, _, output_countries = format_dataset_output(dataset=aoi, name='profiling')
        gdf_profiles_aoi.to_file(output_countries)
        return gdf_profiles_aoi
    else:
        return gdf_profiles_aoi


def main():
    """
    Function to manage the CLI

    :return: Nothing
    :rtype: None
    """
    # Clean the terminal everytime a command is triggered
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
                        nargs='*',
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
                __setConfigValue(var, value)
                with open(config_file_path, 'r') as cfg:
                    print(cfg.read())
            elif len(args.config) == 0:
                with open(config_file_path, 'r') as cfg:
                    print(cfg.read())
        elif args.aoi:
            _ = run(aoi=args.aoi, export=True)
    except AttributeError:
        parser.print_help(stderr)
        exit(1)


# Execute outside the if __name__ == '__main__' because I the main function to be accessible from the entry point in
# setup.py
if __name__ == '__main__':
    main()
else:
    pass
