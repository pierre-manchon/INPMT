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
from typing import Any, AnyStr, Optional, SupportsInt, Union

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import rasterio.mask
import rasterio.windows
from rasterio.features import shapes

from geopandas import GeoDataFrame

from .utils import format_dataset_output
from .vector import __read_shapefile, intersect


def get_pixel_count(dataset_path: AnyStr, processing: AnyStr):
    """
    Takes a dataset path as an input, read every of its pixel then count them based on their values.

    :param processing:
    :type processing:
    :param dataset_path:
    :return:
    """
    ds = polygonize(dataset=dataset_path, processing=processing)
    ua = gpd.read_file(ds)
    for i in range(len(ua)):
        ua.loc[i, 'area'] = ua.loc[i, 'geometry'].area
    ua = ua.groupby(by='val').agg(func='sum')
    labels = ua.value_counts('val').keys().values.astype(np.str)
    nbrs = ua.value_counts().values
    area = ua.value_counts('area').keys().values
    category_area = np.multiply(nbrs, area)
    percentage = np.divide(np.multiply(category_area, 100), ua['area'].sum())
    return pd.DataFrame(data={"Category": labels, "Nbr of pixels": nbrs, "Surface (m2)": area, "Proportion (%)": percentage})


def get_value_from_coord(index: int, dataset: AnyStr, shapefile: GeoDataFrame) -> int:
    with rasterio.open(dataset) as src:
        x, y = list(shapefile.loc[index, 'geometry'].coords)[0]
        # get pixel x+y of the coordinate
        py, px = src.index(x, y)
        # create 1x1px window of the pixel
        window = rasterio.windows.Window(px - 1//2, py - 1//2, 1, 1)
        # read rgb values of the window
        value = src.read(window=window)
    return value[0][0][0]


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
                {"driver": "GTiff",
                 "height": cropped_dataset.shape[1],
                 "width": cropped_dataset.shape[2],
                 "transform": output_transform})
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
        print(UserWarning("Raster does not overlap with {}.".format(__sf.__hash__)))
        pass


def polygonize(dataset: AnyStr, processing: AnyStr) -> AnyStr:
    """
    Read a raster file and transform each pixel in a vector entity

    :param processing:
    :type processing:
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
) -> Union[tuple[Any, Any, Any, Any], tuple[int, int, int, int]]:
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
        return (
            round(x.sum(), 3),
            round(x.min(), 3),
            round(x.mean(), 3),
            round(x.max(), 3),
        )
    except TypeError:
        return 0, 0, 0, 0
    except ValueError:
        return 0, 0, 0, 0


def density(dataset: AnyStr, area: AnyStr, processing: AnyStr) -> SupportsInt:
    """
    AA
    """
    # TODO Convert the pixels to vector => Divide the value by the percentage of air in the pixel
    # (1/3 of the pixel of 300m) => Use the remaining values to average in the buffer
    with rasterio.open(dataset) as src:
        res_x, res_y = src.res
    polygonized = polygonize(dataset, processing=processing)
    polygon = intersect(base=polygonized, overlay=area, crs=3857)
    polygon.insert(0, "valpop", np.nan)
    print('on est la')
    zda = gpd.read_file(polygonized, encoding='windows-1252')
    zda.plot()
    polygon.plot()
    i = None
    val = None
    percentage = None
    for i in range(len(polygon)):
        # area_pop*10 because the population values are minified by 10
        # area_surf * 1 000 000 because they were in square meters (3857 cartesian) and population density is usually
        # expressed in square kilometers
        val = polygon.loc[i, 'val']*10
        percentage = round(polygon.loc[i, 'geometry'].area/(res_x*res_y), 2)
        polygon.loc[i, 'valpop'] = val*percentage
    print('{}, {}, {}, {}, {}, {}, {}'.format(len(polygon),
                                              polygon.loc[i, 'geometry'].area,
                                              res_x*res_y,
                                              val,
                                              percentage,
                                              polygon['val'].sum(),
                                              polygon['valpop'].sum()))
    return polygon['valpop'].sum()
