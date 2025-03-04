from fringe import load_cal_data

import numpy as np

caldata_fn = r'I:\MSL\Private\LENGTH\EQUIPREG\cal_data.xml'

def test_load_cal_data():
    red, green = load_cal_data.read_cal_wavelengths(caldata_fn, red_green=True)
    assert red[0] == 'LENGTH/2018/1111'
    np.testing.assert_allclose(red[1], 632.9913742, 0.0000001, )
    assert green[0] == 'MISEENPRATIQUE'
    np.testing.assert_allclose(green[1], 546.22705, 0.00001, )
