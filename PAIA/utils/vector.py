# -*-coding: utf8 -*
"""
Functions for basic vector processing
"""
import fiona
import libpysal
import pandas as pd
import geopandas as gpd
import shapefile as shp
from shapefile import Reader
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr
from collections import Iterable
from PAIA.utils.utils import format_dataset_output


def __read_shapefile(shapefile: AnyStr) -> list:
    """
    This was made specifically for the raster_crop function because the mask function uses fiona.

    :param shapefile: Vector file path
    :type shapefile: AnyStr
    :return: List of dicts of geometries and their types
    :rtype: list
    """
    with fiona.open(shapefile) as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    return shapes


def __read_shapefile_as_dataframe(shapefile: AnyStr) -> [DataFrame, Reader]:
    """
    Read a geodataframe into a Pandas dataframe with a 'coords' column holding the geometry information.

    :param shapefile: Vector file path
    :type shapefile: AnyStr
    :return: DataFrame with a coords column
    :rtype: [DataFrame, Reader]
    """
    sf = shp.Reader(shapefile)
    fields = [x[0] for x in sf.fields][1:]
    records = sf.records()
    shps = [s.points for s in sf.shapes()]
    df = pd.DataFrame(columns=fields, data=records)
    df = df.assign(coords=shps)
    return df, sf


def __read_shapefile_as_geodataframe(shapefile: AnyStr) -> GeoDataFrame:
    """


    :param shapefile:
    :type shapefile:
    :return:
    :rtype:
    """
    gdf = gpd.read_file(shapefile, encoding='latin1')
    gdf.crs = 3857
    return gdf


def merge_touching(geodataframe: GeoDataFrame) -> GeoDataFrame:
    """
    Takes a GeoDataFrame as input and dissolve every touching polygons by doing the sum of their values.

    Heavily inspired from this stackoverflow post:
    # https://stackoverflow.com/questions/67280722/how-to-merge-touching-polygons-with-geopandas

    :param geodataframe: A generic GeoDataFrame
    :type geodataframe: GeoDataFrame
    :return: A new GeoDataFrame of polygons merged when touching
    :rtype: GeoDataFrame
    """
    w = libpysal.weights.Queen.from_dataframe(geodataframe)
    components = w.component_labels
    combined_polygons = geodataframe.dissolve(by=components, aggfunc='sum')
    return combined_polygons


def to_wkt(df: DataFrame, column: AnyStr) -> DataFrame:
    """
    Transform a column of text geometry into a column of wkt (Well Known Text)

    :param df: Input DataFrame with the faulty geometry column
    :type df: DataFrame
    :param column: Column where the geometry is
    :type column: AnyStr
    :return: New DataFrame
    :rtype: DataFrame
    """
    df[column] = gpd.GeoSeries.from_wkt(df[column])
    return df


def intersect(base: AnyStr, overlay: AnyStr, crs: int, export: bool = False) -> [GeoDataFrame, AnyStr]:
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
    gdf_base = gpd.read_file(base, encoding='latin1')
    gdf_ol = gpd.read_file(overlay, encoding='latin1')
    gdf_base.crs = crs
    gdf_ol.crs = crs
    inter_df = gpd.overlay(gdf_base, gdf_ol)
    inter_df.crs = crs

    if export:
        _, _, output_path = format_dataset_output(dataset=base, name='intersect_tmp')
        try:
            inter_df.to_file(output_path, index=False)
            return inter_df, output_path
        except ValueError:
            print(UserWarning('Empty dataframe from {} was not saved.'.format(base)))
            pass
    else:
        return inter_df


def is_of_interest(base: GeoDataFrame, interest: GeoDataFrame) -> GeoDataFrame:
    """
    Takes two GeoDataFrames as input files and returns the first one minus every polygons that doesn't intersect with
    the polygons of the second GeoDataFrame.
    This function doesn't actually intersect but keep the polygons that does.

    :param base: Geodataframe
    :type base: GeoDataFrame
    :param interest: GeoDataFrame
    :type interest: GeoDataFrame
    :return: GeoDataFrame
    :rtype: GeoDataFrame
    """
    base['intersects'] = False
    for w, x in iter_poly(shapefile=base):
        for y, z in iter_poly(shapefile=interest):
            if x.intersects(z)[0]:
                base.loc[w, 'intersects'] = True
    to_drop = base.loc[base.loc[:, 'intersects'] != True].index
    base.drop(to_drop, inplace=True)
    base.drop(['intersects'], axis=1, inplace=True)
    base = base.reset_index()
    return base


def iter_poly(shapefile: GeoDataFrame) -> Iterable:
    """
    Takes a GeoDataFrame as input file then iterates over it and yields each shape and its index as a GeoDataFrame.

    :param shapefile: Vector file path
    :type shapefile: GeoDataFrame
    :return: Generator yielding the index (i) and a Geodataframe
    :rtype: Iterable
    """
    for i in range(0, len(shapefile)):
        r = gpd.GeoDataFrame(gpd.GeoSeries(shapefile.iloc[i]['geometry']))
        r = r.rename(columns={0: 'geometry'}).set_geometry('geometry')
        r.crs = 3857
        yield i, r
