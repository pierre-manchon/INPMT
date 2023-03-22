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
import os
import warnings
from tempfile import TemporaryDirectory
from typing import AnyStr

import numpy as np
import rioxarray as rxr
import xarray as xr

try:
    from __processing import get_countries_profile, get_urban_profile
    from utils.utils import (
        format_dataset_output,
        get_cfg_val,
        set_cfg_val,
    )
except ImportError:
    from INPMT.__processing import get_countries_profile, get_urban_profile
    from INPMT.utils.utils import (
        format_dataset_output,
        get_cfg_val,
        set_cfg_val,
    )

warnings.filterwarnings("ignore")


def run(
    method: AnyStr = ("villages", "countries"),
    export_dir: AnyStr = "results",
    loc: bool = True,
) -> None:
    """
    Retrieves the datasets path and executes the functions.
    For the countries, i only execute it like that.
    For the villages, i execute first after setting the buffer parameter to
        500, then i execute it after setting the
    parameter to 2000. Then i merge the two results.

    :param loc:
    :param method: Execute whether by villages or countries
    :type method: AnyStr
    :param export_dir:
    :type export_dir: AnyStr
    :return: Nothing
    :rtype: None
    """
    valid_method = ["countries", "villages"]
    if method not in valid_method:
        raise ValueError(
            f"Invalid method parameter. Expected one of {valid_method}"
        )
    datasets = get_cfg_val("datasets_storage_path")
    export = os.path.join(datasets, export_dir)

    # Convert all raster data as an xarray Dataset
    population = rxr.open_rasterio(os.path.join(datasets, "POPULATION_AFRICA_100m_reprj3857.tif"))
    landuse = rxr.open_rasterio(os.path.join(datasets, "LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif"))
    ndvi = rxr.open_rasterio(os.path.join(datasets, "NDVI_MOD13A1.006__500m_16_days_NDVI_doy2016_aid0001.tif"))
    swi = rxr.open_rasterio(os.path.join(datasets, "SWI_c_gls_SWI10_QL_2016_AFRICA_ASCAT_V3.1.1_reprj3857.tif"))
    gws = rxr.open_rasterio(os.path.join(datasets, "GWS_seasonality_AFRICA_reprj3857.tif"))
    prevalence = rxr.open_rasterio(os.path.join(datasets, "PREVALENCE_2019_Global_PfPR_2016_reprj3857.tif"))

    population = population.rename({"band": 'population'}).chunk()
    landuse = landuse.rename({"band": 'landuse'}).chunk()
    ndvi = ndvi.rename({"band": 'ndvi'}).chunk()
    swi = swi.rename({"band": 'swi'}).chunk()
    gws = gws.rename({"band": 'gws'}).chunk()
    prevalence = prevalence.rename({"band": 'prevalence'}).chunk()

    population.name = 'population'
    landuse.name = 'landuse'
    ndvi.name = 'ndvi'
    swi.name = 'swi'
    gws.name = 'gws'
    prevalence.name = 'prevalence'

    # Convert all vector data as a WKT geometry
    irish = os.path.join(datasets, "IRISH_countries.shp")
    landuse_polygonized = os.path.join(datasets, "LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.shp")
    anopheles_kyalo = os.path.join(datasets, "KYALO_VectorDB_1898-2016.shp")
    os.path.join(datasets, "KYALO_anopheles_in_PAs_buffers.shp")  # noqa F841
    os.path.join(datasets, "KYALO_anopheles_out_PAs_buffers.shp")
    national_parks_with_anopheles_kyalo = os.path.join(datasets, "NATIONAL_PARKS_WDPA_Africa_anopheles.shp")
    anopheles_kyalo_all_buffered = os.path.join(datasets, "KYALO_anopheles_all_PAs_buffers.shp")

    with TemporaryDirectory(prefix="INPMT_") as tmp_directory:
        # Read file as a geodataframe
        if method == "countries":
            gdf_profiles_aoi, path_profiles_aoi = get_countries_profile(
                aoi=irish,
                landuse=landuse,
                landuse_polygonized=landuse_polygonized,
                anopheles=anopheles_kyalo,
                processing_directory=tmp_directory,
            )
            # Retrieves the directory the dataset is in and joins it the output
            # filename
            _, _, output_profiles = format_dataset_output(
                dataset=export_dir, name="countries_profiles"
            )
            gdf_profiles_aoi.to_file(output_profiles)
        if method == "villages":
            set_cfg_val("buffer_villages", "500")
            profile_villages_500 = get_urban_profile(
                villages=anopheles_kyalo_all_buffered,
                parks=national_parks_with_anopheles_kyalo,
                population=population,
                landuse=landuse,
                ndvi=ndvi,
                swi=swi,
                gws=gws,
                prevalence=prevalence,
                loc=loc)
            set_cfg_val("buffer_villages", "2000")
            profile_villages_2000 = get_urban_profile(
                villages=anopheles_kyalo_all_buffered,
                parks=national_parks_with_anopheles_kyalo,
                population=population,
                landuse=landuse,
                ndvi=ndvi,
                swi=swi,
                gws=gws,
                prevalence=prevalence,
                loc=loc)

            # https://stackoverflow.com/a/50865526
            # Merge the two dataframes in one (side by side) with the column
            # suffix
            profile_villages = profile_villages_500.reset_index(drop=True
                                                                ).merge(
                profile_villages_2000.reset_index(drop=True),
                left_index=True,
                right_index=True,
                suffixes=("_500", "_2000"),
            )
            # Rename and delete the duplicated columns
            profile_villages.rename(
                columns={
                    "ID_500": "ID",
                    "x_500": "x",
                    "y_500": "y",
                    "NP_500": "NP",
                    "loc_NP_500": "loc_NP",
                    "dist_NP_500": "dist_NP",
                },
                inplace=True,
            )
            profile_villages = profile_villages.drop(
                [
                    "ID_2000",
                    "x_2000",
                    "y_2000",
                    "NP_2000",
                    "loc_NP_2000",
                    "dist_NP_2000",
                ],
                axis=1,
            )
            # Change nan values to NULL string
            # https://stackoverflow.com/a/26838140/12258568
            profile_villages = profile_villages.replace(np.nan,
                                                        "NULL",
                                                        regex=True)
            # Retrieves the directory the dataset is in and joins it the output
            # filename
            _, _, output_urban_profiles = format_dataset_output(
                dataset=export, name="urban_profiles", ext=".xlsx"
            )
            profile_villages.to_excel(output_urban_profiles)
            print("Jesus was black.")
