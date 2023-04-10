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

import rioxarray as rxr
from pandas import DataFrame

try:
    from __processing import get_urban_profile
except ImportError:
    from INPMT.__processing import get_urban_profile

warnings.filterwarnings("ignore")


def run(datasets: str) -> DataFrame:
    """
    Retrieves the datasets path and executes the functions.
    For the countries, i only execute it like that.
    For the villages, i execute first after setting the buffer parameter to
        500, then i execute it after setting the
    parameter to 2000. Then i merge the two results.

    :return: Nothing
    :rtype: None
    """
    # Convert all raster data as xarray DataArrays
    population = rxr.open_rasterio(os.path.join(datasets, "POPULATION_AFRICA_100m_reprj3857.tif"))
    landuse = rxr.open_rasterio(os.path.join(datasets, "LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.tif"))
    ndvi = rxr.open_rasterio(os.path.join(datasets, "NDVI_MOD13A1.006__500m_16_days_NDVI_doy2016_aid0001.tif"))
    swi = rxr.open_rasterio(os.path.join(datasets, "SWI_c_gls_SWI10_QL_2016_AFRICA_ASCAT_V3.1.1_reprj3857.tif"))
    gws = rxr.open_rasterio(os.path.join(datasets, "GWS_seasonality_AFRICA_reprj3857.tif"))
    prevalence = rxr.open_rasterio(os.path.join(datasets, "PREVALENCE_2019_Global_PfPR_2016_reprj3857.tif"))

    # Add name attribute
    population.name = 'population'
    landuse.name = 'landuse'
    ndvi.name = 'ndvi'
    swi.name = 'swi'
    gws.name = 'gws'
    prevalence.name = 'prevalence'

    # Convert all vector data as a WKT geometry
    os.path.join(datasets, "IRISH_countries.shp")
    os.path.join(datasets, "LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0.shp")
    anopheles_kyalo_in_PAs_buffers = os.path.join(datasets, "KYALO_anopheles_in_PAs_buffers.shp")  # noqa F841
    national_parks_with_anopheles_kyalo = os.path.join(datasets, "NATIONAL_PARKS_WDPA_Africa_anopheles.shp")
    anopheles_kyalo = os.path.join(datasets, "KYALO_anopheles.shp")

    profile_villages = get_urban_profile(
        datasets=datasets,
        villages=anopheles_kyalo,
        parks=national_parks_with_anopheles_kyalo,
        population=population,
        landuse=landuse,
        ndvi=ndvi,
        swi=swi,
        gws=gws,
        prevalence=prevalence)
    print("Jesus was black.")
    return profile_villages
