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
import warnings
from collections.abc import Iterable
from typing import AnyStr

# Functions for basic vector processing
import fiona
import geopandas as gpd
from geopandas import GeoDataFrame

from INPMT.utils.utils import format_dataset_output

warnings.filterwarnings("ignore")


def __read_shapefile(shapefile: AnyStr) -> list:
    """
    This was made specifically for the raster_crop function because the mask function uses fiona.

    :param shapefile: Vector file path
    :type shapefile: AnyStr
    :return: List of dicts of geometries and their types
    :rtype: list
    """
    with fiona.open(
        shapefile, "r", encoding="utf-8"
    ) as shape:  # , encoding='windows-1252'
        shapes = [feature["geometry"] for feature in shape]
    return shapes


def __read_shp_as_gdf(shapefile: AnyStr) -> GeoDataFrame:
    """


    :param shapefile:
    :type shapefile:
    :return:
    :rtype:
    """
    gdf = gpd.read_file(shapefile, "r", encoding="utf-8")
    gdf.crs = 3857
    return gdf


def intersect(
    base: AnyStr, overlay: AnyStr, crs: int, export: bool = False
) -> [GeoDataFrame, AnyStr]:
    """
    Takes two GeoDataFrames as input files and returns their polygons that intersects as another GeoDataFrame.

    :param base:
    :type base: AnyStr
    :param overlay:
    :type overlay: AnyStr
    :param crs:
    :type crs: int
    :param export:
    :type export: bool
    :return:
    :rtype: [GeoDataFrame, AnyStr]
    """
    gdf_base = gpd.read_file(base, "r", encoding="utf-8")
    gdf_ol = gpd.read_file(overlay, "r", encoding="utf-8")
    gdf_base.crs = crs
    gdf_ol.crs = crs
    inter_df = gpd.overlay(gdf_base, gdf_ol)
    inter_df.crs = crs

    if export:
        _, _, output_path = format_dataset_output(dataset=base, name="intersect_tmp")
        try:
            inter_df.to_file(output_path, index=False)
            return inter_df, output_path
        except ValueError:
            print(UserWarning(f"Empty dataframe from {base} was not saved."))
            pass
    else:
        return inter_df


def iter_geoseries_as_geodataframe(shapefile: GeoDataFrame) -> Iterable:
    """
    Takes a GeoDataFrame as input file then iterates over it and yields each shape and its index as a GeoDataFrame.

    :param shapefile: Vector file path
    :type shapefile: GeoDataFrame
    :return: Generator yielding the index (i) and a Geodataframe
    :rtype: Iterable
    """
    for i in range(0, len(shapefile)):
        r = gpd.GeoDataFrame(gpd.GeoSeries(shapefile.iloc[i]["geometry"]))
        r = r.rename(columns={0: "geometry"}).set_geometry("geometry")
        r.crs = 3857
        yield i, r
