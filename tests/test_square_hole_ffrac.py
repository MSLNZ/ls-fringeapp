"""
test the new code for masking a central  circular region of a square gauge
by making some mock images from original fringe images of rectangular gauges
"""

from pathlib import Path
import pytest


from PIL import Image
import numpy as np

from ls_fringeapp import fringeprocess as fp
from ls_fringeapp.load_equipment_data import repo_folder
from ls_fringeapp import plot_helpers as ph


TEST_DATA_DIR = Path(__file__).resolve().parent / "data"


def pytest_generate_tests(metafunc):
    data = np.genfromtxt(
        TEST_DATA_DIR / "fflog_to_test_2025-11-11.txt", delimiter="\t", dtype="str"
    )
    metafunc.parametrize("row", list(data))


def test_square_ffrac(row):
    # data from a row in fflog.txt
    ffrac_exp = float(row[0])
    img_filename = TEST_DATA_DIR / row[1]
    xygb = row[2:8].astype(float)
    xygb = xygb.reshape((3, 2))

    img = Image.open(img_filename)
    img = img.convert("L")

    img_sq, xy_sq = ph.make_square_gauge(img, xygb)
    # get ffrac for square image with no hole
    ffrac_sq = fp.array2frac(
        np.asarray(img_sq),
        xy_sq,
        drawinfo=False,
        border=(0.1, 0.1),
    )
    # add blurred hole
    img_hole = ph.blur_gauge_hole(img_sq, xy_sq, circle_radius=0.25)
    ffrac_hole = fp.array2frac(
        np.asarray(img_hole),
        xy_sq,
        drawinfo=False,
        border=(0.1, 0.1),
        circle_radius=0.27,
    )
    # compare the 3 values for fringe fraction
    assert ffrac_sq == pytest.approx(ffrac_exp, abs=1e-3)
    assert ffrac_hole == pytest.approx(ffrac_exp, abs=1e-3)
