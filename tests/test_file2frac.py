"""
test fringe fraction calculation against results from previous versions of software
put a file fflog.txt with copied lines from calibration fflog.txt in /data
put all corresponding cropped fringe images in /data
"""
from pathlib import Path
import numpy as np
from PIL import Image
import fringeprocess as fp

TEST_DATA_DIR = Path(__file__).resolve().parent / 'data'


def pytest_generate_tests(metafunc):
    data = np.genfromtxt(TEST_DATA_DIR / 'fflog.txt', delimiter='\t', dtype='str')
    metafunc.parametrize("row", list(data))


def test_fringe_calc(row):
    ffrac_exp = np.float(row[0])
    img_filename = TEST_DATA_DIR / row[1]
    img = Image.open(img_filename)
    img.convert('L')
    img_array = np.asarray(img)
    if img_array.ndim > 2:
        img_array = img_array.mean(axis=2)
    xygb = row[2:8].astype(np.float)
    xygb = xygb.reshape((3, 2))
    ffrac_calc = fp.array2frac(img_array, xygb)
    # would have expected we could get 1e-4 here, but not always
    # algorithim must be slightly different
    # uncertainty analysis requires ???
    np.testing.assert_allclose(ffrac_calc, ffrac_exp, 0.5e-3,)
