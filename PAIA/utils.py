# -*-coding: utf8 -*
"""
Only functions
"""
from os.path import join as path_join
from pathlib import Path
from collections import Counter
from typing import AnyStr, List, Generator


def format_dataset_output(dataset: AnyStr, name: AnyStr):
    """
    :param name:
    :type name:
    :param dataset:
    :type dataset:
    :return:
    :rtype:
    """
    __ext = Path(dataset).suffix
    __dataset_name = Path(dataset).name.replace(__ext, '')
    __output_path = path_join(Path(dataset).parent, ''.join([__dataset_name, '_', name, __ext]))
    return __dataset_name, __ext, __output_path


def __gather(pixel_values: Generator) -> List:
    """
    Using a generator as an input, i __gather every value encountered into a list.

    :param pixel_values: Float value of a pixel in a raster band
    :type pixel_values: Generator
    :return: A list of all of the pixels found in a raster band
    :rtype: List
    """
    __cat = []
    for x in pixel_values:
        __cat.append(x)
    return __cat


def __get_value_count(pixel_array: List) -> Counter:
    """
    Using a list as an input, i

    :param pixel_array:  A list of all of the pixels found in a raster band
    :type pixel_array: List
    :return: Countered data
    :rtype: Counter
    """
    __nb = Counter()
    __nb.update(pixel_array)
    return __nb
