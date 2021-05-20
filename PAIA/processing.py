# -*-coding: utf8 -*
import os
import rasterio
import rasterio.mask
from datetime import datetime
from numpy import ndarray
from geopandas import GeoDataFrame
from typing import AnyStr, SupportsInt
from PAIA.decorators import timer
from PAIA.utils import __get_value_count, __gather, format_dataset_output
from PAIA.vector import merge_touching, __read_shapefile_as_geodataframe, fill_holes
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
        shapefile: AnyStr,
        villages_separation: SupportsInt,
        fill_treshold: SupportsInt,
        export: bool = False
) -> GeoDataFrame:
    merging_result = merge_touching(shapefile=shapefile)

    result = []
    for poly in merging_result.geometry:
        if poly.area <= villages_separation:
            result.append("small")
        else:
            result.append("large")

    merging_result["Size"] = result

    if export:
        directory = os.path.dirname(shapefile)
        output_path = os.path.join(directory, 'test_fill.shp')
        merging_result.to_file(output_path)
    else:
        return merging_result
