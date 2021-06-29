# -*-coding: utf8 -*
"""
INPMT
A tool to process data to learn more about Impact of National Parks on Malaria Transmission

Copyright (C) <2021>  <Manchon Pierre>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import rasterio
import rasterio.mask
from rasterio.features import shapes
import geopandas as gpd
from numpy import ndarray
from pathlib import Path
from geopandas import GeoDataFrame
from typing import Any, AnyStr, Generator, Optional, Counter, SupportsInt
from .utils import format_dataset_output, __gather, __count_values
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
                    yield c


def get_pixel_count(dataset_path: AnyStr, band: SupportsInt) -> tuple[Any, Counter]:
    """
    Takes a dataset path as an input, read every of its pixel then count them based on their values.

    :param dataset_path:
    :param band:
    :return:
    """
    __pixel_value = 0
    __val = None
    __dataset = None
    __output_path = None

    with rasterio.open(dataset_path) as __dataset:
        __band = __dataset.read()[band]
        __pixel_value = read_pixels(dataset=__dataset, band=__band)
        __pixel_array = __gather(pixel_values=__pixel_value)
        __ctr = __count_values(pixel_array=__pixel_array)
    return __dataset, __ctr


def raster_crop(dataset: AnyStr, shapefile: AnyStr, overwrite: bool = False) -> AnyStr:
    """
    Crop raster with geodataframe boundary
    :param overwrite:
    :type overwrite:
    :param dataset:
    :type dataset:
    :param shapefile:
    :type shapefile:
    :return:
    :rtype:
    """
    __sf = __read_shapefile(shapefile=shapefile)

    try:
        with rasterio.open(dataset) as src:
            cropped_dataset, output_transform = rasterio.mask.mask(src, __sf, crop=True)
            output_meta = src.meta
            output_meta.update({"driver": "GTiff",
                                "height": cropped_dataset.shape[1],
                                "width": cropped_dataset.shape[2],
                                "transform": output_transform})
            *_, __output_path = format_dataset_output(dataset=dataset, name='cropped_tmp', prevent_duplicate=False)

            if overwrite:
                try:
                    os.remove(__output_path)
                except FileNotFoundError:
                    pass

            with rasterio.open(__output_path, "w", **output_meta) as output_file:
                output_file.write(cropped_dataset)
        return __output_path

    except ValueError:
        print(UserWarning('Raster {} does not overlap.'.format(dataset)))
        pass


def polygonize(dataset: AnyStr) -> GeoDataFrame:
    mask = None
    with rasterio.Env():
        with rasterio.open(dataset) as src:
            image = src.read(1)
            results = ({'properties': {'val': v}, 'geometry': s}
                       for i, (s, v) in enumerate(shapes(image, mask=mask, transform=src.transform)))
    geoms = list(results)
    gpd_polygonized_raster = gpd.GeoDataFrame.from_features(geoms).dissolve(by='val')
    return gpd_polygonized_raster.loc[1:]


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
