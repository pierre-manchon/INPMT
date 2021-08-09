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
import os
from argparse import ArgumentTypeError
from configparser import ConfigParser
from shlex import quote as shlex_quote
from sys import argv, exit, stderr
from tempfile import TemporaryDirectory
from typing import AnyStr

try:
    from __processing import get_countries_profile, get_urban_profile
    from __utils.utils import __get_cfg_val, __set_cfg_val, format_dataset_output
except ImportError:
    from .__processing import get_countries_profile, get_urban_profile
    from .__utils.utils import __get_cfg_val, __set_cfg_val, format_dataset_output

cfgparser = ConfigParser()
cfgparser.read("setup.cfg")
config_file_path = "".join([cfgparser.get("setup", "name"), "/config.cfg"])


def run(
    aoi: AnyStr,
    countries: bool,
    villages: bool,
    export_dir: AnyStr = "./results/",
    export: bool = False,
):
    """
    population = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/
    UNadj_constrained_merged_degraded.tif'
    landuse = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/
    ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif'
    ndvi = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/test NDVI/1an/
    MOD13A1.006__500m_16_days_NDVI_doy2020145_aid0001.tif'

    countries_irish = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/africa_countries_irish.shp'
    anopheles_kyalo = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/VectorDB_1898-2016.shp'
    national_parks_with_anopheles_kyalo = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/
    WDPA_Africa_anopheles.shp'
    national_parks_with_anopheles_buffered = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/
    WDPA_Africa_anopheles_buffer10km.shp'
    anopheles_kyalo_in_national_parks = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/datasets/
    anopheles_in_PAs.shp'
    anopheles_kyalo_in_national_parks_buffered = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/
    datasets/anopheles_in_PAs_buffers.shp'
    national_parks_buffered_with_anopheles_kyalo = r'H:/Cours/M2/Cours/HGADU03 - Mémoire/Projet Impact PN Anophèles/
    datasets/PAs_buffers_anos.shp'
    """
    datasets = __get_cfg_val("datasets_storage_path")

    # population = os.path.join(datasets, "POPULATION/UNadj_constrained.tif")
    population = os.path.join(datasets, "POPULATION/UNadj_constrained_reprj3857.tif")
    landuse = os.path.join(datasets, "LANDUSE/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif")
    ndvi = os.path.join(datasets, "NDVI/MOD13A1.006__300m_16_days_NDVI_doy2016_aid0001_reprj3857.tif")
    swi = os.path.join(datasets, "SWI/c_gls_SWI10_QL_2016_AFRICA_ASCAT_V3.1.1_reprj3857.tif")
    gws = os.path.join(datasets, "GWS/GWS_yearlyClassification2016_degraded.tif")
    prevalence = os.path.join(datasets, "PREVALENCE/2019_Global_PfPR_2016_reprj3857.tif")

    landuse_polygonized = os.path.join(datasets, "LANDUSE/ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.shp")
    # countries_irish = os.path.join(datasets, 'IRISH/africa_countries_irish_tmp.shp')
    anopheles_kyalo = os.path.join(datasets, "KYALO/VectorDB_1898-2016.shp")
    # anopheles_kyalo_in_national_parks = os.path.join(datasets, 'KYALO/anopheles_in_PAs.shp')
    anopheles_kyalo_in_national_parks_buffered = os.path.join(datasets, "KYALO/anopheles_in_PAs_buffers.shp")
    # national_parks_buffered_with_anopheles_kyalo = os.path.join(datasets, 'NATIONAL PARKS/PAs_buffers_anos.shp')
    national_parks_with_anopheles_kyalo = os.path.join(datasets, "NATIONAL PARKS/WDPA_Africa_anopheles.shp")
    # national_parks_with_anopheles_buffered = os.path.join(datasets, 'NATIONAL PARKS/WDPA_Africa_anopheles_buffer10km.shp')

    with TemporaryDirectory() as tmp_directory:
        # Read file as a geodataframe
        if countries:
            gdf_profiles_aoi, path_profiles_aoi = get_countries_profile(
                aoi=aoi,
                landuse=landuse,
                landuse_polygonized=landuse_polygonized,
                anopheles=anopheles_kyalo,
                processing_directory=tmp_directory,
            )
            if export:
                # Retrieves the directory the dataset is in and joins it the output filename
                _, _, output_profiles = format_dataset_output(dataset=export_dir, name="countries_profiles")
                gdf_profiles_aoi.to_file(output_profiles)
            else:
                return gdf_profiles_aoi
        if villages:
            __set_cfg_val("buffer_villages", "500")
            profile_villages_500 = get_urban_profile(
                villages=anopheles_kyalo_in_national_parks_buffered,
                parks=national_parks_with_anopheles_kyalo,
                landuse=landuse,
                population=population,
                ndvi=ndvi,
                swi=swi,
                gws=gws,
                prevalence=prevalence,
                processing_directory=tmp_directory,
            )
            __set_cfg_val("buffer_villages", "2000")
            profile_villages_2000 = get_urban_profile(
                villages=anopheles_kyalo_in_national_parks_buffered,
                parks=national_parks_with_anopheles_kyalo,
                landuse=landuse,
                population=population,
                ndvi=ndvi,
                swi=swi,
                gws=gws,
                prevalence=prevalence,
                processing_directory=tmp_directory,
            )

            # https://stackoverflow.com/a/50865526
            # Merge the two dataframes in one (side by side) with the column suffix
            profile_vilages = profile_villages_500.reset_index(drop=True).merge(
                profile_villages_2000.reset_index(drop=True),
                left_index=True,
                right_index=True,
                suffixes=("_500", "_2000"),
            )
            if export:
                _, _, output_urban_profiles = format_dataset_output(dataset=export_dir, name="urban_profiles", ext='.xlsx')
                profile_vilages.to_excel(output_urban_profiles)
                return profile_vilages
            else:
                return profile_vilages


def main():
    """
    Function to manage the CLI

    :return: Nothing
    :rtype: None
    """
    # Clean the terminal everytime a command is triggered
    os.system(shlex_quote("cls" if os.name == "nt" else "clear"))

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
            """

            :param message:
            """
            stderr.write("error: %s\n" % message)
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
        normalized_filepath = os.path.normpath(dirpath)
        if os.path.isfile(normalized_filepath):
            return normalized_filepath
        else:
            raise ArgumentTypeError('"{}" is not a valid path {}'.format(dirpath, "\n"))

    parser = ArgumentParser(
        prog="$ python {}".format(cfgparser.get("setup", "name")),
        description="",
        add_help=False,
        epilog="\n",
    )

    # Create the arguments
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit."
    )
    parser.add_argument(
        "-d",
        "--description",
        dest="description",
        action="store_true",
        help="Show the program's description and exit.",
    )
    parser.add_argument(
        "-l",
        "--license",
        dest="license",
        action="store_true",
        help="Show the program's license and exit.",
    )
    parser.add_argument(
        "-c", "--config", nargs="*", help="Read or overwrite local config file."
    )
    parser.add_argument(
        "-aoi",
        "--aoi",
        nargs="?",
        type=file_path,
        help="Shapefile of the area(s) of interest you want to process",
    )

    # If no arguments are given, print the help
    if len(argv) == 1:
        parser.print_help(stderr)
        exit(1)

    # Parse the arguments
    args = parser.parse_args()

    # Based on the dest vars execute methods with the arguments
    try:
        if args.license is True:
            print(cfgparser.get("metadata", "short_license"))
        elif args.description is True:
            print(cfgparser.get("setup", "description"))
        elif args.config is not None:
            if len(args.config) == 2:
                var, value = args.config
                __set_cfg_val(var, value)
                with open(config_file_path, "r") as cfg:
                    print(cfg.read())
            elif len(args.config) == 0:
                with open(config_file_path, "r") as cfg:
                    print(cfg.read())
        elif args.aoi:
            run(aoi=args.aoi, countries=args.countries, villages=args.villages, export=args.export)
    except AttributeError:
        parser.print_help(stderr)
        exit(1)


# Execute outside the if __name__ == '__main__' because I the main function to be accessible from the entry point in
# setup.py
if __name__ == "__main__":
    main()
else:
    pass
