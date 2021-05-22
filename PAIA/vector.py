# -*-coding: utf8 -*
import fiona
import libpysal
import geopandas
import pandas as pd
import shapefile as shp
from shapely.geometry import Polygon
from shapefile import Reader
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt


def __read_shapefile(shapefile: AnyStr) -> list:
    with fiona.open(shapefile, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    return shapes


def __read_shapefile_as_dataframe(shapefile: AnyStr) -> [DataFrame, Reader]:
    """
    Read a shapefile into a Pandas dataframe with a 'coords'
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
    gdf = geopandas.read_file(shapefile)
    return gdf


def merge_touching(shapefile: AnyStr) -> GeoDataFrame:
    # https://stackoverflow.com/questions/67280722/how-to-merge-touching-polygons-with-geopandas
    gdf = geopandas.read_file(shapefile)
    W = libpysal.weights.Queen.from_dataframe(gdf)
    components = W.component_labels
    combined_polygons = gdf.dissolve(by=components)
    return combined_polygons


def fill_holes(gdf: GeoDataFrame, area: SupportsInt) -> GeoDataFrame:
    for ring in gdf.interiors:
        pol = Polygon(ring)
        if pol.area < area:
            gdf = gdf.union(pol.buffer(0.3))
    return gdf
