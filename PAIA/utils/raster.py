# -*-coding: utf8 -*
import os
import rasterio
import rasterio.mask
from numpy import ndarray
from pathlib import Path
from typing import AnyStr, Generator, Optional
from PAIA.utils.utils import format_dataset_output
from .vector import __read_shapefile


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


def raster_crop(dataset: AnyStr, shapefile: AnyStr, export: bool = False):
    """
    Crop raster with geodataframe boundary
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
