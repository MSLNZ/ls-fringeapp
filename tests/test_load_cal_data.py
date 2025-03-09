from pathlib import Path
from fringe import load_cal_data

import numpy as np
import pytest

caldata_fn = 'L:/EQUIPREG/XML Files/cal_data.xml'

@pytest.mark.skipif(not Path(caldata_fn).exists(), reason="cal_data.xml not found")
def test_load_cal_data():
    red, green = load_cal_data.read_cal_wavelengths(caldata_fn, red_green=True)
    assert red[0] == 'LENGTH/2018/1111'
    np.testing.assert_allclose(red[1], 632.9913742, 0.0000001, )
    assert green[0] == 'MISEENPRATIQUE'
    np.testing.assert_allclose(green[1], 546.22705, 0.00001, )
