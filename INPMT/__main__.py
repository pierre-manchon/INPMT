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
import argparse
import os
import numpy as np
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
    method: AnyStr = ('villages', 'countries'),
    export_dir: AnyStr = "results",
    loc: bool = True
) -> None:
    """
    Retrieves the datasets path and executes the functions.
    For the countries, i only execute it like that.
    For the villages, i execute first after setting the buffer parameter to 500, then i execute it after setting the
    parameter to 2000. Then i merge the two results.
    
    :param loc:
    :param method: Execute whether by villages or countries
    :type method: AnyStr
    :param export_dir:
    :type export_dir: AnyStr
    :return: Nothing
    :rtype: None
    """
    valid_method = ['countries', 'villages']
    if method not in valid_method:
        raise ValueError("Invalid method parameter. Expected one of {}".format(valid_method))
    datasets = __get_cfg_val("datasets_storage_path")
    export = os.path.join(datasets, export_dir)
    
    # Raster data
    population = os.path.join(datasets, "POPULATION_AFRICA_100m_reprj3857.tif")
    landuse = os.path.join(datasets, "LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif")
    ndvi = os.path.join(datasets, "NDVI_MOD13A1.006__500m_16_days_NDVI_doy2016_aid0001.tif")
    swi = os.path.join(datasets, "SWI_c_gls_SWI10_QL_2016_AFRICA_ASCAT_V3.1.1_reprj3857.tif")
    gws = os.path.join(datasets, "GWS_seasonality_AFRICA_reprj3857.tif")
    prevalence = os.path.join(datasets, "PREVALENCE_2019_Global_PfPR_2016_reprj3857.tif")

    # Vector data
    irish = os.path.join(datasets, "IRISH_countries.shp")
    landuse_polygonized = os.path.join(datasets, "LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.shp")
    anopheles_kyalo = os.path.join(datasets, "KYALO_VectorDB_1898-2016.shp")
    anopheles_kyalo_in_national_parks_buffered = os.path.join(datasets, "KYALO_anopheles_in_PAs_buffers.shp")
    anopheles_kyalo_out_national_parks_buffered = os.path.join(datasets, "KYALO_anopheles_out_PAs_buffers.shp")
    national_parks_with_anopheles_kyalo = os.path.join(datasets, "NATIONAL_PARKS_WDPA_Africa_anopheles.shp")

    with TemporaryDirectory(prefix='INPMT_') as tmp_directory:
        # Read file as a geodataframe
        if method == 'countries':
            gdf_profiles_aoi, path_profiles_aoi = get_countries_profile(
                aoi=irish,
                landuse=landuse,
                landuse_polygonized=landuse_polygonized,
                anopheles=anopheles_kyalo,
                processing_directory=tmp_directory,
            )
            # Retrieves the directory the dataset is in and joins it the output filename
            _, _, output_profiles = format_dataset_output(dataset=export_dir, name="countries_profiles")
            gdf_profiles_aoi.to_file(output_profiles)
        if method == 'villages':
            __set_cfg_val("buffer_villages", "500")
            profile_villages_500 = get_urban_profile(
                villages=anopheles_kyalo_out_national_parks_buffered,
                parks=national_parks_with_anopheles_kyalo,
                landuse=landuse,
                population=population,
                ndvi=ndvi,
                swi=swi,
                gws=gws,
                prevalence=prevalence,
                processing_directory=tmp_directory,
                loc=loc
            )
            __set_cfg_val("buffer_villages", "2000")
            profile_villages_2000 = get_urban_profile(
                villages=anopheles_kyalo_out_national_parks_buffered,
                parks=national_parks_with_anopheles_kyalo,
                landuse=landuse,
                population=population,
                ndvi=ndvi,
                swi=swi,
                gws=gws,
                prevalence=prevalence,
                processing_directory=tmp_directory,
                loc=loc
            )

            # https://stackoverflow.com/a/50865526
            # Merge the two dataframes in one (side by side) with the column suffix
            profile_villages = profile_villages_500.reset_index(drop=True).merge(
                profile_villages_2000.reset_index(drop=True),
                left_index=True,
                right_index=True,
                suffixes=("_500", "_2000"),
            )
            # Rename and delete the duplicated columns
            profile_villages.rename(columns={'ID_500': 'ID',
                                             'x_500': 'x',
                                             'y_500': 'y',
                                             'NP_500': 'NP',
                                             'loc_NP_500': 'loc_NP',
                                             'dist_NP_500': 'dist_NP'}, inplace=True)
            profile_villages = profile_villages.drop(['ID_2000',
                                                      'x_2000',
                                                      'y_2000',
                                                      'NP_2000',
                                                      'loc_NP_2000',
                                                      'dist_NP_2000'], axis=1)
            # Change nan values to NULL string
            # https://stackoverflow.com/a/26838140/12258568
            profile_villages = profile_villages.replace(np.nan, 'NULL', regex=True)
            # Retrieves the directory the dataset is in and joins it the output filename
            _, _, output_urban_profiles = format_dataset_output(dataset=export, name="urban_profiles", ext='.xlsx')
            profile_villages.to_excel(output_urban_profiles)
            print('Jesus was black.')


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
        Overridden to print the help whenever an error occurred (For example, no arguments error)

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
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit.")
    parser.add_argument("-d",
                        "--description",
                        dest="description",
                        action="store_true",
                        help="Show the program's description and exit.")
    parser.add_argument("-l",
                        "--license",
                        dest="license",
                        action="store_true",
                        help="Show the program's license and exit.",)
    parser.add_argument("-c",
                        "--config",
                        nargs="*",
                        help="Read or overwrite local config file.")
    parser.add_argument("-m",
                        "--method",
                        nargs="?",
                        type=file_path,
                        help="How do you want to process the data ['countries', 'villages'].",)
    parser.add_argument("-e",
                        "--export",
                        nargs="?",
                        type=file_path,
                        help="Where do you the result to be saved.",)
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
        elif args.method:
            run(method=args.method, export_dir=args.export)
    except AttributeError:
        parser.print_help(stderr)
        exit(1)


# Execute outside the if __name__ == '__main__' because I the main function to be accessible from the entry point in
# setup.py
if __name__ == "__main__":
    main()
else:
    pass
