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
from pathlib import Path
from typing import Any, AnyStr, Counter, Generator, Optional, SupportsInt, Union

import numpy as np
import geopandas as gpd
import rasterio
import rasterio.mask
import matplotlib.pyplot as plt
from geopandas import GeoDataFrame
from rasterio.features import shapes

from .utils import __count_values, __gather, format_dataset_output
from .vector import __read_shapefile, intersect


def read_pixels(dataset: AnyStr, band: np.ndarray) -> Generator:
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
    # TODO CC
    for __row in range(band.shape[0]):
        for __col in range(band.shape[1]):
            if band[__row, __col] != dataset.nodata:
                yield str(band[__row, __col])


def read_pixels_from_array(dataset: np.ndarray) -> Generator:
    """
    :param dataset:
    :type dataset:
    :return:
    :rtype:
    """
    # TODO CC
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

    with rasterio.open(dataset_path) as __dataset:
        __band = __dataset.read()[band]
        __pixel_value = read_pixels(dataset=__dataset, band=__band)
        __pixel_array = __gather(pixel_values=__pixel_value)
        __ctr = __count_values(pixel_array=__pixel_array)
    return __dataset, __ctr


def raster_crop(
    dataset: AnyStr, shapefile: AnyStr, processing: AnyStr, overwrite: bool = False
) -> AnyStr:
    """
    Cut a raster based on the GeoDataFrame boundary and saves it in a new temporary file.

    :param dataset: Path to the dataset file
    :type dataset: AnyStr
    :param shapefile: Path to the shapefile file
    :type shapefile: AnyStr
    :param processing: Path to the temporary directory used to store temporary files (then deleted)
    :type processing: AnyStr
    :param overwrite: Whether I try to overwrite the file or not
    :type overwrite: bool
    :return: Path to the file of the cropped dataset
    :rtype: AnyStr
    """
    __sf = __read_shapefile(shapefile=shapefile)
    try:
        with rasterio.open(dataset) as src:
            cropped_dataset, output_transform = rasterio.mask.mask(src, __sf, crop=True)
            output_meta = src.meta
            output_meta.update(
                {
                    "driver": "GTiff",
                    "height": cropped_dataset.shape[1],
                    "width": cropped_dataset.shape[2],
                    "transform": output_transform,
                }
            )
            r, r_ext, _ = format_dataset_output(dataset=dataset, name="cropped_tmp")
            __output_path = os.path.join(processing, "".join([r, r_ext]))

            if overwrite:
                try:
                    os.remove(__output_path)
                except FileNotFoundError:
                    pass

            with rasterio.open(__output_path, "w", **output_meta) as output_file:
                output_file.write(cropped_dataset)
        return __output_path

    except ValueError:
        print(
            UserWarning(
                "Raster does not overlap with {}.".format(__sf.__hash__)
            )
        )
        pass


def polygonize(dataset: AnyStr, processing: AnyStr) -> AnyStr:
    """
    Read a raster file and transform each pixel in a vector entity

    :param dataset:
    :return:
    """
    mask = None
    with rasterio.Env():
        with rasterio.open(dataset) as src:
            image = src.read(1)
            results = (
                {"properties": {"val": v}, "geometry": s}
                for i, (s, v) in enumerate(
                    shapes(image, mask=mask, transform=src.transform)
                )
            )
    geoms = list(results)
    gpd_polygonized_raster = gpd.GeoDataFrame.from_features(geoms)
    gpd_polygonized_raster.crs = 3857
    p, p_ext, _ = format_dataset_output(dataset=dataset, name='polygonized_tmp', ext='.shp')
    __output_path = os.path.join(processing, "".join([p, p_ext]))
    gpd_polygonized_raster.to_file(__output_path)
    return __output_path


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
        os.path.join(*args, "mask.tif")
    else:
        "mask.tif"
    with rasterio.open("mask.tif", "w") as output_file:
        output_file.write(output_image)


def raster_stats(
    dataset: AnyStr,
) -> Union[tuple[Any, Any, Any], tuple[float, float, float]]:
    """
    Read any raster file then delete the no data values and returns some basic statistics about the said raster (min,
    mean and max)

    :param dataset: Path to the dataset file
    :type: dataset: AnyStr
    :return: Min, Mean, Max values
    :rtype: typle(SupportsInt, SupportsInt, SupportsInt)
    """
    # If TypeError, you couldn't read the file because it had no data.
    # If ValueError, idk
    try:
        with rasterio.open(dataset) as ro:
            x = ro.read()
            x = x[x != ro.nodata]
        # Divide by 10.000 because NDVI is usually between -1 and 1 and these values are between -10000 and 10000
        return (
            round(x.min() / 10000, 3),
            round(x.mean() / 10000, 3),
            round(x.max() / 10000, 3),
        )
    except TypeError:
        return 0, 0, 0
    except ValueError:
        return 0, 0, 0


def density(dataset: AnyStr, area: AnyStr, processing: AnyStr) -> SupportsInt:
    """
    AA
    """
    # TODO Convertir les pixels en vecteur => Diviser la valeur par le pourcentage de l'air du pixel
    #  (1/3 du pixel de 300m) => Utiliser les valeurs restantes pour faire la moyenne dans le buffer
    with rasterio.open(dataset) as src:
        res_x, res_y = src.res
    polygonized = polygonize(dataset, processing=processing)
    polygon = intersect(base=polygonized, overlay=area, crs=3857)
    polygon.insert(0, "valpop", np.nan)
    for i in range(len(polygon)):
        val = None
        percentage = None
        # area_pop*10 because the population values are minified by 10
        # area_surf * 1 000 000 because they were in square meters (3857 cartesian) and population density is usually
        # expressed in sqaure kilometers
        percentage = round(polygon.loc[i, 'geometry'].area/(res_x*res_y), 2)
        val = polygon.loc[i, 'val']*10
        if percentage > 1.0:
            print('AreaPoly:[{}] AreaRaster:[{}] Val:[{}] Perc:[{}] Res:[{}]'.format(
                polygon.loc[i, 'geometry'].area,
                res_x*res_y,
                val,
                percentage,
                val*percentage))
        polygon.loc[i, 'valpop'] = val*percentage
    print('{}, {}, {}'.format(len(polygon), polygon['val'].sum(), polygon['valpop'].sum()))
    return polygon['valpop'].sum()
