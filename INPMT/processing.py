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
from typing import Any, AnyStr

import geopandas as gpd
import pandas as pd
import xarray as xr
from alive_progress import alive_bar
from geopandas import GeoDataFrame
from pandas import DataFrame

try:
    from utils.raster import (
        get_pixel_count,
    )
    from utils.utils import (
        clip,
        read_qml,
        strip,
    )
except ImportError:
    from INPMT.utils.raster import (
        get_pixel_count,
    )
    from INPMT.utils.utils import (
        clip,
        read_qml,
        strip,
    )

warnings.filterwarnings("ignore")


def get_nearest_park(
        parks: GeoDataFrame,
        geom_villages: GeoDataFrame
) -> tuple[Any | None, str | None, str]:
    """
    For each polygon, I check the distance from the point to the boundary of the polygon and compare it to the minimum
    distance found yet (at the start it's 100000 but it is modified in the first occurrence).
    Every time a distance is smaller, the minimum distance it's reset.
    Every time the distance from point to the centroid of the polygon equals 0, it means the polygon of villages is
    inside the polygon of parks. In these cases I set it as a negative value.
    :param geom_villages: A GeoDataFrame of the locations of mosquito counts of Africa
    :type: geom_villages: GeoDataFrame
    :param parks: A GeoDataFrame of the national parks of Africa
    :type: parks: GeoDataFrame
    :return: A DataFrame of the result
    :rtype: DataFrame
    """
    name = None
    loc_np = None
    res_dist = None
    min_dist = 1000000000000000
    for i in range(len(parks)):
        dist = parks.loc[i, "geometry"].boundary.distance(geom_villages.centroid)
        if dist < min_dist:
            min_dist = dist
            name = parks.loc[i, "NAME"]
            if parks.loc[i, "geometry"].contains(geom_villages):
                res_dist = -min_dist
                loc_np = "P"
            else:
                res_dist = min_dist
                loc_np = "B"
    return res_dist, loc_np, name


def get_landuse(
    dataset: xr.Dataset,
    qml: list
) -> tuple[DataFrame, int]:
    """
    Use a shapefile and a raster file to process landuse nature and landuse percentage.
    To do this, I first read the qml (legend file) to get the values and their corresponding labels.
    Then I retrieve a number of pixels by values using the Counter object.
    I process the category area and the landuse percentage using the pixel area and the polygon area

    :param legend_filename:
    :param dataset: Path to the dataset file
    :type dataset: AnyStr
    :param item_type: Type of the item containing labels, values and colors for the legend.
    :type item_type: AnyStr
    :return: A DataFrame updated with the processed values
    :rtype: tuple(DataFrame, SupportsInt)
    """
    df = get_pixel_count(dataset=dataset)
    len_df = len(df)
    for i, r in df.iterrows():
        label = "Unknown"
        for category in qml:
            # https://stackoverflow.com/a/8948303/12258568
            if int(float(r["cat"])) == int(category[0]):
                label = category[1]
                break
        df.loc[i, "Label"] = label
    df = df.pivot_table(columns="Label",
                        values="Proportion (%)",
                        aggfunc="sum")
    return df, len_df


def get_urban_profile(
    datasets: str,
    villages: AnyStr,
    parks: AnyStr,
    population: xr.Dataset,
    landuse: xr.Dataset,
    ndvi: xr.Dataset,
    swi: xr.Dataset,
    gws: xr.Dataset,
    prevalence: xr.Dataset,
) -> DataFrame:
    """
    I use 4 different data, 2 vectors that I read in a GeoDataFrame at the beginning of the script and 2 raster.
    Then, I iterate on the GeoDataFrame of the villages.
    This allows me to make calculations for each entity and not for the whole layer.

    For each iteration:
    - I first calculate which is the nearest park with the ***get_nearest_park*** function. In addition, if the village
        is in the park, I transform the value into a negative value),
    - I count the number of mosquito species in the village,
    - I transform the GeoSeries in GeoDataFrame: The result that we obtain when we iterate on each line of a
        GeoDataFrame, is an object of type GeoSeries. I transform it in GeoDataFrame because these two objects have
        different properties (in particular to calculate a buffer or especially to cut a raster),
    - I calculate a buffer of 500m,
    - I cut my raster of NDVI values with the ***raster_crop*** function. This function has the particularity to produce
        a new raster file that I have to save and then reopen. Indeed, the rasterio package does not allow to overwrite
        files as it can be done with geopandas,
    - I read the raster that I have cut and then calculate statistical values like the minimum, the average and the
        maximum thanks to the ***raster_stats*** function,
    - I cut my raster of NDVI values with the ***raster_crop*** function. This function has the particularity to produce
        a new raster file that I have to save and then reopen. Indeed, the rasterio package does not allow to overwrite
        files as it can be done with geopandas (which I just use above),
    - I read the raster that I cut out then I calculate the percentages of land use and I associate them to the nature
        of these land uses with the ***get_landuse*** function

    :param villages: Path to the shapefile
    :type villages: AnyStr
    :param parks: Path to the shapefile
    :type parks: AnyStr
    :param population: A Dataset with every type of data in it
    :type population: xr.Dataset
    :param population: A Dataset with every type of data in it
    :type population: xr.Dataset
    :param landuse: A Dataset with every type of data in it
    :type landuse: xr.Dataset
    :param ndvi: A Dataset with every type of data in it
    :type ndvi: xr.Dataset
    :param swi: A Dataset with every type of data in it
    :type swi: xr.Dataset
    :param gws: A Dataset with every type of data in it
    :type gws: xr.Dataset
    :param prevalence: A Dataset with every type of data in it
    :type prevalence: xr.Dataset
    :return: A DataFrame of the processed values
    :rtype: DataFrame
    """
    buffer_500 = 500
    buffer_2000 = 2000
    # Read the shapefiles as GeoDataFrames
    gdf_villages = gpd.read_file(villages)
    gdf_parks = gpd.read_file(parks)
    # Set the projection to 3857 to have distance, etc as meters
    # Retrieves buffer size for the villages patches
    # Create a blank DataFrame to receive the result when iterating below
    cols = [
        "ID",
        "x",
        "y",
        "NP",
        "loc_NP",
        "dist_NP",
        "ANO_DIV",
        "POP_500",
        "PREVALENCE_500",
        "SWI_500",
        "NDVI_min_500",
        "NDVI_mean_500",
        "NDVI_max_500",
        "HAB_DIV_500",
        "POP_2000",
        "PREVALENCE_2000",
        "SWI_2000",
        "NDVI_min_2000",
        "NDVI_mean_2000",
        "NDVI_max_2000",
        "HAB_DIV_2000",
    ]
    result = pd.DataFrame(columns=cols)
        # Retrieve the legend file's path
    hd_qml = read_qml(path_qml=os.path.join(datasets, 'LANDUSE_ESACCI-LC-L4-LC10-Map-300m-P1Y-2016-v1.0-2.qml'), item_type='item')
    gws_qml = read_qml(path_qml=os.path.join(datasets, 'GWS_seasonality_AFRICA_reprj3857.qml'), item_type='paletteEntry')
    # Create the progress and the temporary directory used to save some temporary files
    with alive_bar(total=len(gdf_villages)) as pbar:
        for i in range(len(gdf_villages)):
            _, village_id = strip(gdf_villages.loc[i, "Full_Name"])
            result.loc[i, "ID"] = village_id
            if (other_ano := gdf_villages.loc[i, 'Other Anop']) is not None:
                ano_div = int(gdf_villages.iloc[i].str.count("Y").sum()) + len(other_ano.split(','))
            else:
                ano_div = int(gdf_villages.iloc[i].str.count("Y").sum())
            result.loc[i, "ANO_DIV"] = ano_div

            # Geometry
            geom = gdf_villages.loc[i, "geometry"]
            geom_500 = geom.buffer(buffer_500)
            geom_2000 = geom.buffer(buffer_2000)

            # Get the minimum distance from the village the park edge border and return the said distance and the
            # park's name
            res_dist, loc_np, np_name = get_nearest_park(parks=gdf_parks, geom_villages=geom_2000)
            result.loc[i, "NP"] = np_name
            result.loc[i, "loc_NP"] = loc_np
            result.loc[i, "dist_NP"] = round(res_dist, 3)

            # Coordinates
            result.loc[i, "x"] = geom_500.centroid.x
            result.loc[i, "y"] = geom_500.centroid.y

            population_500 = clip(population, geom_500)
            landuse_500 = clip(landuse, geom_500)
            ndvi_500 = clip(ndvi, geom_500)
            swi_500 = clip(swi, geom_500)
            gws_500 = clip(gws, geom_500)
            prevalence_500 = clip(prevalence, geom_500)

            population_2000 = clip(population, geom_2000)
            landuse_2000 = clip(landuse, geom_2000)
            ndvi_2000 = clip(ndvi, geom_2000)
            swi_2000 = clip(swi, geom_2000)
            gws_2000 = clip(gws, geom_2000)
            prevalence_2000 = clip(prevalence, geom_2000)

            # POPULATION
            result.loc[i, "POP_500"] = population_500.sum(skipna=True).values
            result.loc[i, "POP_2000"] = population_2000.sum(skipna=True).values

            # NDVI
            # I divide by 10 000 because Normalized Difference Vegetation
            # Index is usually between -1 and 1.
            # For 500 meters
            result.loc[i, "NDVI_min_500"] = (ndvi_500.min(skipna=True) / 10000).values
            result.loc[i, "NDVI_mean_500"] = (ndvi_500.mean(skipna=True) / 10000).values
            result.loc[i, "NDVI_max_500"] = (ndvi_500.max(skipna=True) / 10000).values
            # For 2000 meters
            result.loc[i, "NDVI_min_2000"] = (ndvi_2000.min(skipna=True) / 10000).values
            result.loc[i, "NDVI_mean_2000"] = (ndvi_2000.mean(skipna=True) / 10000).values
            result.loc[i, "NDVI_max_2000"] = (ndvi_2000.max(skipna=True) / 10000).values

            # SWI
            # https://land.copernicus.eu/global/products/SWI I divide by a 2
            # because SWI data must be between 0 and 100.
            result.loc[i, "SWI_500"] = (swi_500.sum(skipna=True) / 2).values
            result.loc[i, "SWI_2000"] = (swi_2000.sum(skipna=True) / 2).values

            # PREVALENCE
            # https://malariaatlas.org/explorer/#/ I multiply by 100 because PREVALENCE is a percentage between 0
            # and 100.
            result.loc[i, "PREVALENCE_500"] = (prevalence_500.sum(skipna=True) * 100).values
            result.loc[i, "PREVALENCE_2000"] = (prevalence_2000.sum(skipna=True) * 100).values

            # LANDUSE
            df_hd_500, len_ctr_500 = get_landuse(landuse_500, hd_qml)
            result.loc[i, "HAB_DIV_500"] = len_ctr_500
            result.loc[i, df_hd_500.columns] = df_hd_500.values[0]
            df_hd_2000, len_ctr_2000 = get_landuse(landuse_2000, hd_qml)
            result.loc[i, "HAB_DIV_2000"] = len_ctr_2000
            result.loc[i, df_hd_2000.columns] = df_hd_2000.values[0]

            # GWS
            df_gws_500, _ = get_landuse(gws_500, gws_qml)
            result.loc[i, df_gws_500.columns] = df_gws_500.values[0]
            df_gws_2000, _ = get_landuse(gws_2000, gws_qml)
            result.loc[i, df_gws_2000.columns] = df_gws_2000.values[0]
            pbar()
    return result
