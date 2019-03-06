from pathlib import Path
import numpy as np
import gauge_length as gl

TEST_DATA_DIR = Path(__file__).resolve().parent / "data"

# This testing requires using the same values for wavelengths and obliquity
# corrections and refractive index formula as used at time of original calculation
# The results for APMP LK1 were calculated using the Matlab software
# in June 2005 using the version in "I:\MSL\Private\LENGTH\Hilger\Matlab\FileArchive\20050127"
# this uses Muijlwijk88 for refractive index of air

RedWavelength  = 632.991417
GreenWavelength  = 546.22705
# ObliquityCorrection  = 1.00000013;


def pytest_generate_tests(metafunc):
    data = np.genfromtxt(TEST_DATA_DIR / "calcs-LK1.csv", delimiter=",", dtype="str")
    metafunc.parametrize("row", list(data))


def test_gaugelength_metric_red_green(row):
    nominalsize_mm = np.float(row[0])
    rtemp_c = np.float(row[15])
    gtemp_c = np.float(row[16])
    pressure_mb = np.float(row[17])
    humidity_rh = np.float(row[19])
    ffred = np.float(row[21])
    ffgreen = np.float(row[22])
    expcoeff = np.float(row[13])

    rd_exp = np.float(row[4])
    gd_exp = np.float(row[5])

    rd_calc, gd_calc, bestindex = gl.calcgaugelength(
        nominalsize_mm,
        rtemp_c,
        gtemp_c,
        pressure_mb,
        humidity_rh,
        ffred,
        ffgreen,
        expcoeff,
        RedWavelength,
        GreenWavelength,
        formula=3,
    )

    np.testing.assert_allclose(rd_calc[5], rd_exp, atol=0.1)
    np.testing.assert_allclose(gd_calc[5], gd_exp, atol=0.1)
