"""
create synthetic images to test array2frac
"""

import random
import numpy as np
import pytest
from ls_fringeapp import synthetic_images as si
from ls_fringeapp import fringeprocess as fp

n_tests = 50
# exclude tests of ffrac close  to 0 and 1 to avoid wrap around problems
margin = 0.01


# this takes 1.7 s for n_tests = 50.
def test_array2frac_random():
    """
    makes n_tests images with random variation of
        - fringe_spacing_px,
        - offset_px,
        - ffrac
        - img size
        - gb size

    calculates ffrac from image
    compares absoulute maximum difference and stdev of difference with expected values
    """
    ffracs2 = []

    for i in range(n_tests):
        ffrac_set = random.uniform(0.0 + margin, 1.0 - margin)
        spacing = random.uniform(80, 120)
        offset = random.uniform(0, spacing)
        img_size = (int(random.uniform(750, 850)), int(random.uniform(350, 450)))
        gb_size = (int(random.uniform(550, 650)), int(random.uniform(150, 250)))

        a1, gb_yx = si.synthetic_image_with_gauge(
            spacing,
            offset,
            ffrac_set,
            img_size,
            gb_size,
        )
        ffrac_calc = fp.array2frac(a1, gb_yx, drawinfo=False)
        ffracs2.append(
            [
                spacing,
                offset,
                img_size[0],
                img_size[1],
                gb_size[0],
                gb_size[1],
                ffrac_set,
                ffrac_calc,
            ],
        )

    ffracs = np.array(ffracs2)
    diff = ffracs[:, -1] - ffracs[:, -2]
    assert diff.mean() == pytest.approx(0.0, abs=1e-3)
    assert diff.std(ddof=1) < 5e-3
    assert diff.max() < 1e-2
    assert abs(diff.min()) < 1e-2


def test_square_synthetic():
    # loop through random trials

    ffracs2 = []

    for i in range(n_tests):
        ffrac_set = random.uniform(0.0 + margin, 1.0 - margin)
        spacing = random.uniform(80, 120)
        offset = random.uniform(0, spacing)
        img_size = (int(random.uniform(750, 850)), int(random.uniform(750, 850)))
        gb_width = int(random.uniform(550, 650))
        gb_size = (gb_width, gb_width)

        a1, gb_yx = si.synthetic_image_with_gauge(
            spacing,
            offset,
            ffrac_set,
            img_size,
            gb_size,
        )
        a2 = si.blur_gauge_hole(a1, gb_yx, circle_radius=0.25)
        ffrac_calc2, drawdata = fp.array2frac(
            a2,
            gb_yx,
            drawinfo=True,
            circle_radius=0.26,
            border=(0.1, 0.1),
        )

        ffracs2.append(
            [
                spacing,
                offset,
                img_size[0],
                img_size[1],
                gb_size[0],
                gb_size[1],
                ffrac_set,
                ffrac_calc2,
            ],
        )

    ffracs = np.array(ffracs2)
    diff = ffracs[:, -1] - ffracs[:, -2]
    assert diff.mean() == pytest.approx(0.0, abs=2e-3)
    assert diff.std(ddof=1) < 5e-3
    assert diff.max() < 1e-2
    assert abs(diff.min()) < 1e-2
