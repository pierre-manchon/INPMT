# -*-coding: utf8 -*
import os
import rasterio
import rasterio.mask
import pandas as pd
from datetime import datetime
from numpy import ndarray
from pandas import DataFrame
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt
from PAIA.decorators import timer
from PAIA.utils import __get_value_count, __gather, format_dataset_output
from PAIA.vector import merge_touching, to_wkt
from PAIA.raster import read_pixels, read_pixels_from_array


@timer
def get_categories(dataset: AnyStr, shapefile_area: AnyStr, band: SupportsInt) -> None:
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
    __dataset = None
    __dataset_name = None
    __output_path = None

    if type(dataset) is AnyStr:
        __dataset = rasterio.open(dataset)
        __band = __dataset.read()[band]
        __pixel_value = read_pixels(dataset=__dataset, band=__band)
        # Retrieves the directory the dataset is in and joins it the output filename
        __dataset_name, _, __output_path = format_dataset_output(dataset, '_report')
    elif type(dataset) is ndarray:
        __pixel_value = read_pixels_from_array(dataset=dataset)
        __output_path = r'H:\Logiciels\0_Projets\python\PAIA\reports\{}_report.txt'.format(datetime.now().strftime('%Y%m%d-H%M%S%f'))
    else:
        print('None')
        pass

    __pixel_array = __gather(pixel_values=__pixel_value)
    __ctr = __get_value_count(pixel_array=__pixel_array)

    with open(__output_path, "w") as o:
        o.write('{};{};{};{}\n'.format('Category', 'Nbr of pixels', 'Surface (m2)', 'Proportion (%)'))
        for c in __ctr:
            category_area = round(__ctr[c] * (__dataset.res[0] * __dataset.res[1]), 3)
            percentage =((category_area*100) / shapefile_area)
            o.writelines('{};{};{};{}\n'.format(c, __ctr[c], category_area, percentage))

    print('[PAIA]: Report {} generated for layer {}'.format(__output_path, __dataset_name))


@timer
def get_urban_extent(
        urban_areas: GeoDataFrame,
        path_urban_areas: AnyStr,
        villages_separation: SupportsInt,
        export: bool = False
) -> GeoDataFrame:
    merging_result = merge_touching(geodataframe=urban_areas)

    result = []
    for poly in merging_result.geometry:
        if poly.area <= villages_separation:
            result.append("small")
        else:
            result.append("large")
    del poly

    merging_result["Size"] = result
    del result

    if export:
        _, _, output_path = format_dataset_output(path_urban_areas, '_urban_extent')
        merging_result.to_file(output_path)
        return merging_result
    else:
        return merging_result


@timer
def get_distances(pas: GeoDataFrame,
                  urban_areas: GeoDataFrame,
                  path_urban_areas: AnyStr,
                  urban_treshold: SupportsInt,
                  export: bool = False
                  ) -> DataFrame:
    ug = get_urban_extent(urban_areas=urban_areas,
                          path_urban_areas=path_urban_areas,
                          villages_separation=urban_treshold)

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
        min_dist = 100000
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
        _, _, output_path = format_dataset_output(path_urban_areas, 'distances', '.xlsx')
        df.to_excel(output_path, index=False)
        return df
    else:
        return df
