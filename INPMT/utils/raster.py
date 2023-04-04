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
import warnings
from typing import AnyStr

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import rasterio.mask
import rasterio.windows
from rasterio.features import shapes

from INPMT.utils.utils import format_dataset_output
from INPMT.utils.vector import __read_shapefile

warnings.filterwarnings("ignore")


def get_pixel_count(dataset):
    values, count = np.unique(dataset.values, return_counts=True)
    res = dataset.x.values[1] - dataset.x.values[0]
    pxl_area = res * res
    area = count * pxl_area
    area_total = area.sum()
    percentage = area * 100 / area_total
    return pd.DataFrame(data={"Category": values,
                              "Nbr of pixels": count,
                              "Surface (m2)": area,
                              "Proportion (%)": percentage})


def raster_crop(
    dataset: AnyStr, shapefile: AnyStr, processing: AnyStr, overwrite: bool = False
) -> str | None:
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
            cropped_dataset, output_transform = rasterio.mask.mask(src, __sf, all_touched=True, crop=True)
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
    except ValueError as e:
        print(UserWarning(f"Raster does not overlap with {__sf}:\n{e}"))
        return None


def polygonize(dataset: AnyStr, processing: AnyStr) -> AnyStr:
    """
    Read a raster file and transform each pixel in a vector entity

    :param processing:
    :type processing:
    :param dataset:
    :return:
    """
    mask = None
    print(dataset, processing)
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
    p, p_ext, _ = format_dataset_output(
        dataset=dataset, name="polygonized_tmp", ext=".shp"
    )
    __output_path = os.path.join(processing, "".join([p, p_ext]))
    gpd_polygonized_raster.to_file(__output_path)
    return __output_path
