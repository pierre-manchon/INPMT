# -*-coding: utf8 -*
from INPMT.__utils.utils import __get_cfg_val


def test_calc():
    assert int(__get_cfg_val('buffer_villages')) == 2000
