# -*-coding: utf8 -*
import rasterio
import rasterio.mask
import pandas as pd
from numpy import ndarray
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt, Counter, Any, Union
from PAIA.decorators import timer
from PAIA.utils.utils import __get_value_count, __gather, format_dataset_output, get_config_value, read_qml
from PAIA.utils.vector import merge_touching, to_wkt
from PAIA.utils.raster import read_pixels


@timer
def get_categories(dataset_path: AnyStr, band: SupportsInt, export: bool = False) -> DataFrame:
    """
    As an input, i take the dataset path and the band number i want to categorize.
    Then i export the counted values (from the __get_value_count() function).
    To do so, i retrieve the path where the dataset is stored then join it to nameofthedataset_report.txt.
    That way, i can save the report at the same place where the dataset is stored.
    After that, i create the file and populate it with the field names then the values with formatted strings:
        - Number of the category
        - Number of pixels found
        - Surface (based on the pixels surface (h*w) and the number of pixels)

    :param shapefile_area:
    :type shapefile_area:
    :param dataset:
    :type dataset:
    :param band: Specific band from a raster file
    :type band: ndarray
    :return: Export the counter to a text file row by row
    :rtype: None
    """
    __pixel_value = 0
    __val = None
    __dataset = None
    __dataset_name = None
    __output_path = None

    _, _, __qml_path = format_dataset_output(dataset=dataset_path, ext='.qml')
    __style = read_qml(__qml_path)

    __dataset = rasterio.open(dataset_path)
    __band = __dataset.read()[band]
    __pixel_value = read_pixels(dataset=__dataset, band=__band)
    # Retrieves the directory the dataset is in and joins it the output filename
    __dataset_name, _, __output_path = format_dataset_output(dataset=dataset_path, name='report', ext='.xlsx')

    __pixel_array = __gather(pixel_values=__pixel_value)
    __ctr = __get_value_count(pixel_array=__pixel_array)
    data = []
    for c in __ctr:
        category_area = round(__ctr[c] * (__dataset.res[0] * __dataset.res[1]), 3)
        raster_area = sum(__ctr.values())
        percentage = ((__ctr[c] * 100) / raster_area)
        data.append([c, __ctr[c], category_area, percentage])

    df = pd.DataFrame(data, columns=['Category', 'Nbr of pixels', 'Surface (m2)', 'Proportion (%)'])

    for i, row in df.iterrows():
        for j in __style:
            if row['Category'] == j['value']:
                __val = j['label']
        df.at[i, 'Label'] = __val

    if export:
        df.to_excel(__output_path, index=False)
        return df
    else:
        return df


@timer
def get_urban_extent(
        urban_areas: GeoDataFrame,
        path_urban_areas: AnyStr,
        urban_treshold: SupportsInt,
        export: bool = False
) -> GeoDataFrame:
    """
    # TODO
    """
    merging_result = merge_touching(geodataframe=urban_areas)

    result = []
    for poly in merging_result.geometry:
        if poly.area <= urban_treshold:
            result.append("small")
        else:
            result.append("large")
    del poly

    merging_result["Size"] = result
    del result

    if export:
        _, _, output_path = format_dataset_output(dataset=path_urban_areas, name='urban_extent')
        merging_result.to_file(output_path)
        return merging_result
    else:
        return merging_result


@timer
def get_distances(pas: GeoDataFrame,
                  urban_areas: GeoDataFrame,
                  path_urban_areas: AnyStr,
                  export: bool = False
                  ) -> DataFrame:
    """
    # TODO
    """
    urban_treshold = get_config_value('urban_area_treshold')
    ug = get_urban_extent(urban_areas=urban_areas,
                          path_urban_areas=path_urban_areas,
                          urban_treshold=urban_treshold)

    centros = []
    for r in zip(ug.fid, ug.DN, ug.Size, ug.geometry):
        if r[2] == 'small':
            centros.append([r[0], str(r[3].centroid)])
        else:
            centros.append([r[0]])
            pass
    del r
    df = pd.DataFrame(centros, columns=['fid', 'centro'])
    del centros
    df = to_wkt(df=df, column='centro')
    ug = ug.merge(df, on='fid')
    del df

    result = []
    for u in zip(ug.fid, ug.DN, ug.Size, ug.geometry):
        min_dist = get_config_value('min_dist')
        name = None
        for p in zip(pas.WDPA_PID, pas.ORIG_NAME, pas.GIS_AREA, pas.geometry):
            dist = p[3].distance(u[3])
            if dist < min_dist:
                min_dist = dist
                name = p[1]
        result.append([u[0], u[1], u[2], u[3], name, min_dist])
    del dist, min_dist, name, p, u
    df = pd.DataFrame(result, columns=['fid', 'DN', 'Size', 'geometry', 'pa_name', 'distance'])
    del result
    if export:
        _, _, output_path = format_dataset_output(dataset=path_urban_areas, name='distances', ext='.xlsx')
        df.to_excel(output_path, index=False)
        return df
    else:
        return df


@timer
def get_pas_profiles(gdf_pa, gdf_urbain_gabon, path_urbain_gabon, path_ds):
    # Crop the raster and the vector for every polygon of the pas layer
    # Might want use a mask otherwise
    # Then process and associate result to each polygon
    dists = get_distances(pas=gdf_pa,
                          urban_areas=gdf_urbain_gabon,
                          path_urban_areas=path_urbain_gabon,
                          export=True)
    cats = get_categories(dataset_path=path_ds,
                          band=0,
                          export=True)
    pass
