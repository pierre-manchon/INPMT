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
# Function for basic processing and miscellanious cases
import os
import unicodedata
import xml.dom.minidom
from collections import Counter
from configparser import ConfigParser
from datetime import datetime
from pathlib import Path
from typing import AnyStr, Generator, List, Union
from warnings import warn

cfgparser = ConfigParser()
cfgparser.read("setup.cfg")
config_file_path = "".join([cfgparser.get("setup", "name"), "/config.cfg"])


def var_dump(var, prefix=""):
    """
    You know you're a php developer when the first thing you ask for
    when learning a new language is 'Where's var_dump?????'
    https://stackoverflow.com/a/21791626
    """
    my_type = "[" + var.__class__.__name__ + "(" + str(len(var)) + ")]:"
    print(prefix, my_type, sep="")
    prefix += "    "
    for i in var:
        if type(i) in (list, tuple, dict, set):
            var_dump(i, prefix)
        else:
            if isinstance(var, dict):
                print(prefix, i, ": (", var[i].__class__.__name__, ") ", var[i], sep="")
            else:
                print(prefix, "(", i.__class__.__name__, ") ", i, sep="")


def format_dataset_output(
    dataset: AnyStr = "", name: AnyStr = "", ext: AnyStr = "", prevent_duplicate=True
) -> tuple[str, Union[AnyStr, str], str]:
    """
    :param dataset: Path to a file
    :type dataset: AnyStr
    :param name: Name of the output file
    :type name: AnyStr
    :param prevent_duplicate:
    :type prevent_duplicate:
    :param ext: Extension of the output file. If blank, then the input file's etension will be used.
    :type ext: AnyStr
    :return: Dataset name, dataset extension, output path formatted
    :rtype: tuple[str, Union[AnyStr, str], str]
    """
    __ext = Path(dataset).suffix
    __dataset_name = Path(dataset).name.replace(__ext, "")

    if not Path(dataset).is_dir():
        __dataset_name = dataset
    else:
        __dataset_name = os.path.join(
            dataset, "".join(["output_", datetime.now().strftime("%Y%m%d%H%M%S")])
        )
        if ext == "":
            raise UserWarning("Custom dataset path must have attribute 'ext' set")
        pass

    if prevent_duplicate:
        if name != "" and name not in Path(dataset).name:
            __dataset_name = "".join([__dataset_name, "_", name])
    else:
        __dataset_name = "".join([__dataset_name, "_", name])

    if ext != "":
        __ext = ext
    else:
        pass

    __output_path = os.path.join(Path(dataset).parent, "".join([__dataset_name, __ext]))
    return __dataset_name, __ext, __output_path


def __strip(text: AnyStr) -> tuple[str, str]:
    """
    https://stackoverflow.com/a/44433664/12258568

    :param text: String to strip
    :type: text: AnyStr
    :return: Stripped string
    :rtype: AnyStr
    """
    text = unicodedata.normalize("NFD", text).encode("ascii", "ignore").decode("utf-8")
    return str(text), str(text).replace(" ", "")


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


def __get_cfg_val(value):
    getcfgparser = ConfigParser()
    getcfgparser.read(config_file_path, encoding="utf-8")
    return getcfgparser.get("config", value)


def __set_cfg_val(var, value):
    setcfgparser = ConfigParser(comment_prefixes="///", allow_no_value=True)
    setcfgparser.read_file(open(config_file_path))
    try:
        _ = setcfgparser["config"][var]
        setcfgparser["config"][var] = value
        with open(config_file_path, "w") as configfile:
            setcfgparser.write(configfile)
    except KeyError:
        warn("Can't modify non present value", category=SyntaxWarning)
        print("\n")


def __read_qml(path_qml: AnyStr) -> List:
    xml_data = xml.dom.minidom.parse(path_qml)
    legend = []
    for item in xml_data.getElementsByTagName("item"):
        legend.append([item.getAttribute("value"), item.getAttribute("label")])
    return legend
