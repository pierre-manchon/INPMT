# -*-coding: utf8 -*
import os
import fiona
import rasterio
import rasterio.mask
import pandas as pd
import shapefile as shp
from datetime import datetime
from numpy import ndarray
from pathlib import Path
from shapefile import Reader
from pandas import DataFrame
from typing import AnyStr, Generator, SupportsInt, Optional
from PAIA.decorators import timer
from PAIA.utils import __get_value_count, __gather, format_dataset_output


def read_pixels(dataset: AnyStr, band: ndarray) -> Generator:
    """
    Using a dataset filepath and a band numbern i read every pixel values
    one by one for each row then and for each columns.

    :param dataset: Link to a .tif raster file
    :type dataset: AnyStr
    :param band:  Band from a raster to be processed
    :type band: ndarray
    :return: Generator of one pixel at a time
    :rtype: GeneratorType
    """
    for __row in range(band.shape[0]):
        for __col in range(band.shape[1]):
            if band[__row, __col] != dataset.nodata:
                yield str(band[__row, __col])


def read_pixels_from_array(dataset: ndarray) -> Generator:
    """
    :param dataset:
    :type dataset:
    :return:
    :rtype:
    """
    for p in dataset:
        for r in p:
            for c in r:
                if c != 255:
                    print(c)
                    yield c


def var_dump(var, prefix=''):
    """
    You know you're a php developer when the first thing you ask for
    when learning a new language is 'Where's var_dump?????'
    https://stackoverflow.com/a/21791626
    """
    my_type = '[' + var.__class__.__name__ + '(' + str(len(var)) + ')]:'
    print(prefix, my_type, sep='')
    prefix += '    '
    for i in var:
        if type(i) in (list, tuple, dict, set):
            var_dump(i, prefix)
        else:
            if isinstance(var, dict):
                print(prefix, i, ': (', var[i].__class__.__name__, ') ', var[i], sep='')
            else:
                print(prefix, '(', i.__class__.__name__, ') ', i, sep='')


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


def raster_crop(dataset: AnyStr, shapefile: AnyStr, export: bool = False):
    """
    Crop raster with shapefile boundary
    :param export:
    :type export:
    :param dataset:
    :type dataset:
    :param shapefile:
    :type shapefile:
    :return:
    :rtype:
    """
    __sf = __read_shapefile(shapefile=shapefile)

    with rasterio.open(dataset) as src:
        output_image, output_transform = rasterio.mask.mask(src, __sf, crop=True)
        output_meta = src.meta

    output_meta.update({"driver": "GTiff",
                        "height": output_image.shape[1],
                        "width": output_image.shape[2],
                        "transform": output_transform})
    if export:
        *_, __output_path = format_dataset_output(dataset, '_cropped')
        with rasterio.open(__output_path, "w", **output_meta) as output_file:
            output_file.write(output_image)
            print('[PAIA]: Exported cropped file to {}.'.format(Path(__output_path).as_uri()))
    else:
        return output_image


def export_raster(output_image, *args: Optional[Path]) -> None:
    """
    :param output_image:
    :type output_image:
    :param args:
    :type args:
    :return:
    :rtype:
    """
    if args:
        os.path.join(*args, 'mask.tif')
    else:
        'mask.tif'

    with rasterio.open('mask.tif', "w") as output_file:
        output_file.write(output_image)
