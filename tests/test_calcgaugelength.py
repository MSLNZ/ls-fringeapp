from pathlib import Path
import numpy as np
import gauge_length as gl

TEST_DATA_DIR = Path(__file__).resolve().parent / "data"

# This testing requires using the same values for wavelengths and obliquity
# corrections and refractive index formula as used at time of original calculation
# The results for APMP LK1 were calculated using the Matlab software
# in June 2005 using the version in "I:\MSL\Private\LENGTH\Hilger\Matlab\FileArchive\20050127"
# this uses Muijlwijk88 for refractive index of air

RedWavelength = 632.991417
GreenWavelength = 546.22705


def pytest_generate_tests(metafunc):
    data = np.genfromtxt(TEST_DATA_DIR / "calcs-LK1.csv", delimiter=",", dtype="str")
    metafunc.parametrize("row", list(data))


def test_gaugelength_metric_red_green(row):
    nominalsize_mm = float(row[0])
    rtemp_c = float(row[15])
    gtemp_c = float(row[16])
    pressure_mb = float(row[17])
    humidity_rh = float(row[19])
    ffred = float(row[21])
    ffgreen = float(row[22])
    expcoeff = float(row[13])

    rd_exp = float(row[4])
    gd_exp = float(row[5])

    # use same temperature for air and gauge
    rd_calc, gd_calc, bestindex, redindex, greenindex = gl.calcgaugelength(
        nominalsize_mm,
        rtemp_c,
        gtemp_c,
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


def test_gaugelength_metric_red_only(row):
    nominalsize_mm = float(row[0])
    rtemp_c = float(row[15])
    pressure_mb = float(row[17])
    humidity_rh = float(row[19])
    ffred = float(row[21])
    expcoeff = float(row[13])
    rd_exp = float(row[4])

    # use same temperature for air and gauge
    rd_calc, redindex = gl.calcgaugelength_red_only(
        nominalsize_mm,
        rtemp_c,
        rtemp_c,
        pressure_mb,
        humidity_rh,
        ffred,
        expcoeff,
        RedWavelength,
        formula=3,
    )

    np.testing.assert_allclose(rd_calc, rd_exp, atol=0.1)


def test_different_air_temp_red_only(row):
    # test different temperatures for air and gauge
    offset_temp = 0.1
    nominalsize_mm = float(row[0])
    rtemp_c = float(row[15])
    pressure_mb = float(row[17])
    humidity_rh = float(row[19])
    ffred = float(row[21])
    expcoeff = float(row[13])
    rd_exp = float(row[4])
    rtemp_air_c = rtemp_c + offset_temp
    rd_calc, redindex = gl.calcgaugelength_red_only(
        nominalsize_mm,
        rtemp_air_c,
        rtemp_c,
        pressure_mb,
        humidity_rh,
        ffred,
        expcoeff,
        RedWavelength,
        formula=3,
    )
    # 1 K change in air temperature should result in 1 ppm ~= 1 nm/mm change in length
    rd_exp = rd_exp + nominalsize_mm * offset_temp
    # could amend check to be better than 1 nm but OK for now
    np.testing.assert_allclose(rd_calc, rd_exp, atol=1.0)


def test_different_air_temp(row):
    offset_temp = 0.1
    nominalsize_mm = float(row[0])
    rtemp_c = float(row[15])
    gtemp_c = float(row[16])
    pressure_mb = float(row[17])
    humidity_rh = float(row[19])
    ffred = float(row[21])
    ffgreen = float(row[22])
    expcoeff = float(row[13])

    rd_exp = float(row[4])
    gd_exp = float(row[5])
    rtemp_air_c = rtemp_c + offset_temp

    rd_calc, gd_calc, bestindex, redindex, greenindex = gl.calcgaugelength(
        nominalsize_mm,
        rtemp_air_c,
        rtemp_air_c,
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

    # 1 K change in air temperature should result in 1 ppm ~= 1 nm/mm change in length
    rd_exp = rd_exp + nominalsize_mm * offset_temp
    # could amend check to be better than 1 nm but OK for now
    np.testing.assert_allclose(rd_calc[5], rd_exp, atol=1.0)
