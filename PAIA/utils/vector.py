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
    with fiona.open(shapefile) as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    return shapes


def __read_shapefile_as_dataframe(shapefile: AnyStr) -> [DataFrame, Reader]:
    """
    Read a geodataframe into a Pandas dataframe with a 'coords'
    column holding the geometry information. This uses the pyshp
    package
    """
    sf = shp.Reader(shapefile)
    fields = [x[0] for x in sf.fields][1:]
    records = sf.records()
    shps = [s.points for s in sf.shapes()]
    df = pd.DataFrame(columns=fields, data=records)
    df = df.assign(coords=shps)
    return df, sf


def __read_shapefile_as_geodataframe(shapefile: AnyStr) -> GeoDataFrame:
    gdf = gpd.read_file(shapefile)
    return gdf


def merge_touching(geodataframe: GeoDataFrame) -> GeoDataFrame:
    # https://stackoverflow.com/questions/67280722/how-to-merge-touching-polygons-with-geopandas
    w = libpysal.weights.Queen.from_dataframe(geodataframe)
    components = w.component_labels
    combined_polygons = geodataframe.dissolve(by=components, aggfunc='sum')
    return combined_polygons


def to_wkt(df: DataFrame, column: AnyStr) -> DataFrame:
    df[column] = gpd.GeoSeries.from_wkt(df[column])
    return df


def intersect(base: AnyStr, overlay: AnyStr, crs: int, export: bool = False) -> [GeoDataFrame, AnyStr]:
    gdf_base = gpd.read_file(base)
    gdf_ol = gpd.read_file(overlay)
    gdf_base.crs = crs
    gdf_ol.crs = crs
    inter_df = gpd.overlay(gdf_base, gdf_ol)
    inter_df.crs = crs

    if export:
        _, _, output_path = format_dataset_output(dataset=base, name='intersect')
        inter_df.to_file(output_path, index=False)
        return inter_df, output_path
    else:
        return inter_df


def is_of_interest(base: GeoDataFrame, interest: GeoDataFrame) -> GeoDataFrame:
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
    for i in range(0, len(shapefile)):
        r = gpd.GeoDataFrame(gpd.GeoSeries(shapefile.iloc[i]['geometry']))
        r = r.rename(columns={0: 'geometry'}).set_geometry('geometry')
        r.crs = 3857
        yield i, r
