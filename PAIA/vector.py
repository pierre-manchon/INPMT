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


def get_distance(shapefile1: AnyStr, shapefile2: AnyStr) -> GeoDataFrame:
    def get_min_distance(point, lines):
        return lines.distance(point).min()
    sf1 = __read_shapefile_as_geodataframe(shapefile1)
    sf2 = __read_shapefile_as_geodataframe(shapefile2)
    sf1.to_crs(epsg=3857, inplace=True)
    sf2.to_crs(epsg=3857, inplace=True)
    sf1['min_dist_to_lines'] = sf1.geometry.apply(get_min_distance, args=(sf2,))
    return sf1


def get_dist(path, path2):
    # https://medium.com/analytics-vidhya/calculating-distances-from-points-to-polygon-borders-in-python-a-paris-example-3b597e1ea291
    # https://gis.stackexchange.com/a/342489
    t = geopandas.read_file(path)
    y = geopandas.read_file(path2)
    for x in t.geometry:
        for c in y.geometry:
            tt = geopandas.GeoSeries(x)
            tt.crs = 3857
            yy = geopandas.GeoSeries(c)
            yy.crs = 3857
            dist = tt.distance(yy)


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
