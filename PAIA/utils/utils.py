# -*-coding: utf8 -*
"""
PAIA
A tool to process data to learn more about Protected Areas Impact on Malaria Transmission

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
# Function for basic processing and miscellanious cases
from os import path
import xml.dom.minidom
from datetime import datetime
from pathlib import Path
from collections import Counter
from configparser import ConfigParser
from typing import AnyStr, List, Generator, Union


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


def format_dataset_output(dataset: AnyStr = '',
                          name: AnyStr = '',
                          ext: AnyStr = ''
                          ) -> tuple[str, Union[AnyStr, str], str]:
    """
    :param dataset:
    :type dataset: AnyStr
    :param name: Name of the output file
    :type name: AnyStr
    :param ext: Extension of the output file. If blank, then the input file's etension will be used.
    :type ext: AnyStr
    :return: Dataset name, dataset extension, output path formatted
    :rtype: tuple[str, Union[AnyStr, str], str]
    """
    __ext = Path(dataset).suffix
    __dataset_name = Path(dataset).name.replace(__ext, '')

    if not Path(dataset).is_dir():
        __dataset = dataset
    else:
        __dataset_name = path.join(dataset, ''.join(['output_', datetime.now().strftime("%Y%m%d%H%M%S")]))
        if ext == '':
            raise UserWarning("Custom dataset path must have attribute 'ext' set")
        pass

    if name != '' and name not in Path(dataset).name:
        __dataset_name = ''.join([__dataset_name, '_'])
    else:
        pass

    if ext != '':
        __ext = ext
    else:
        pass

    if name in Path(dataset).name:
        __output_path = path.join(Path(dataset).parent, ''.join([__dataset_name, __ext]))
    else:
        __output_path = path.join(Path(dataset).parent, ''.join([__dataset_name, name, __ext]))
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


def __count_values(pixel_array: List) -> Counter:
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


def getConfigValue(value):
    cfgparser = ConfigParser()
    cfgparser.read('./PAIA/config.cfg')
    return cfgparser.get('config', value)


def setConfigValue(var, value):
    config_path = './PAIA/config.cfg'
    config = ConfigParser(comment_prefixes='///', allow_no_value=True)
    config.read_file(open(config_path))
    config['config'][var] = value
    with open(config_path, 'w') as configfile:
        config.write(configfile)


def read_qml(path_qml: AnyStr) -> List:
    xml_data = xml.dom.minidom.parse(path_qml)
    legend = []
    for item in xml_data.getElementsByTagName('item'):
        legend.append([item.getAttribute('value'), item.getAttribute('label')])
    return legend
