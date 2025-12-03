"""
create synthetic images to test array2frac
"""

import random
import numpy as np
import pytest
from ls_fringeapp import synthetic_images as si
from ls_fringeapp import fringeprocess as fp

n_tests = 10


@pytest.mark.slow
def test_array2frac_random():
    """
    makes n_tests images with random variation of
        - fringe_spacing_px,
        - offset_px,
        - ffrac
    calculates ffrac from image
    compares absoulute maximum difference and stdev of difference with expected values
    """
    img_size = (800, 400)
    gb_size = (600, 200)
    ffracs = []
    skip_margin = (
        1e-3  # skip numbers near zero and 1 to avoid wrap around errors. HACKY
    )
    for i in range(n_tests):
        ffrac_set = random.uniform(0.0 + skip_margin, 1.0 - skip_margin)
        spacing = int(random.uniform(80, 120))
        offset = int(random.uniform(0, spacing))

        a1, gb_yx = si.synthetic_image_with_gauge(
            spacing,
            offset,
            ffrac_set,
            img_size,
            gb_size,
        )
        ffrac_calc = fp.array2frac(a1, gb_yx, drawinfo=False)
        ffracs.append([ffrac_set, ffrac_calc])

    ffracs = np.array(ffracs)
    diff = ffracs[:, 1] - ffracs[:, 0]
    assert diff.mean() == pytest.approx(0.0, abs=1e-5)
    assert diff.std(ddof=1) < 5e-4
    assert diff.max() < 1e3
    assert abs(diff.min()) < 1e-3


@pytest.mark.slow
def test_array2frac_not_random():
    """
    fringe fractions from 0 to 1 in 0.01 steps
    fixed spacing and offset
    """
    spacing = 100
    offset = 0
    ffracs = []
    for ffrac_set in np.arange(0, 1, 0.01):
        a1, gb_yx = si.synthetic_image_with_gauge(
            spacing,
            offset,
            ffrac_set,
            (800, 400),
            (600, 200),
        )
        ffrac_calc = fp.array2frac(a1, gb_yx, drawinfo=False)
        ffracs.append([ffrac_set, ffrac_calc])

    ffracs = np.array(ffracs)
    diff = ffracs[:, 1] - ffracs[:, 0]
    assert diff.mean() == pytest.approx(0.0, abs=1e-5)
    assert diff.std(ddof=1) < 5e-4
    assert diff.max() < 1e3
    assert abs(diff.min()) < 1e-3
