from ls_fringeapp import load_equipment_data

import numpy as np


def test_load_cal_data():
    wavelengths = load_equipment_data.laser_wavelengths
    print(wavelengths)
    np.testing.assert_allclose(wavelengths["red"], 632.991212579, atol=1e-9)
    np.testing.assert_allclose(wavelengths["green"], 532.245576449053, atol=1e-9)
