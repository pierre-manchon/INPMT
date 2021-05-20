# -*-coding: utf8 -*
import fiona
import libpysal
import geopandas
import pandas as pd
import shapefile as shp
from shapefile import Reader
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr


def __read_shapefile(shapefile: AnyStr) -> list:
    with fiona.open(shapefile, "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
    return shapes


def read_shapefile_as_dataframe(shapefile: str) -> [DataFrame, Reader]:
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


def merge_touching(shapefile: str) -> GeoDataFrame:
    # https://stackoverflow.com/questions/67280722/how-to-merge-touching-polygons-with-geopandas
    gdf = geopandas.read_file(shapefile)
    W = libpysal.weights.Queen.from_dataframe(gdf)
    components = W.component_labels
    combined_polygons = gdf.dissolve(by=components)
    return combined_polygons
