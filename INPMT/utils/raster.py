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

import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


def get_pixel_count(dataset):
    values, count = np.unique(dataset.values, return_counts=True)
    res = dataset.x.values[1] - dataset.x.values[0]
    pxl_area = res * res
    area = count * pxl_area
    area_total = area.sum()
    percentage = area * 100 / area_total
    return pd.DataFrame(data={"cat": values, "Proportion (%)": percentage})
