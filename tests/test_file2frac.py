"""
test fringe fraction calculation against results from previous versions of software
put a file fflog.txt with copied lines from calibration fflog.txt in /data
put all corresponding cropped fringe images in /data


EFH 2025-11-11
I am updating the values in "fflog_to_test_2025-11-11.txt" to the fringe fraction values produced by the software today.
This software has been validated by key comparison .....
"""

from pathlib import Path
import numpy as np
from PIL import Image
from ls_fringeapp import fringeprocess as fp

TEST_DATA_DIR = Path(__file__).resolve().parent / "data"


def pytest_generate_tests(metafunc):
    data = np.genfromtxt(
        TEST_DATA_DIR / "fflog_to_test_2025-11-11.txt", delimiter="\t", dtype="str"
    )
    metafunc.parametrize("row", list(data))


def test_fringe_calc(row):
    ffrac_exp = float(row[0])
    img_filename = TEST_DATA_DIR / row[1]
    img = Image.open(img_filename)
    img.convert("L")
    img_array = np.asarray(img)
    if img_array.ndim > 2:
        img_array = img_array.mean(axis=2)
    xygb = row[2:8].astype(float)
    xygb = xygb.reshape((3, 2))
    ffrac_calc = fp.array2frac(img_array, xygb)

    # uncertainty analysis requires 0.4e-3 at 1 sigma,
    np.testing.assert_allclose(
        ffrac_calc,
        ffrac_exp,
        atol=0.00001,
    )
