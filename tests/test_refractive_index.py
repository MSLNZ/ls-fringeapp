import numpy as np
from ls_fringeapp import refractiveindex as ri

# values calculated on NIST website
data = (
    (20, 0, 101.325, 633, 1.000271800, 1.000271799),
    (20, 0, 60, 633, 1.000160924, 1.000160920),
    (20, 0, 120, 633, 1.000321916, 1.000321918),
    (50, 0, 100, 633, 1.000243285, 1.000243270),
    (5, 0, 100, 633, 1.000282756, 1.000282750),
    (-40, 0, 100, 633, 1.000337580, 1.000337471),
    (50, 100, 120, 633, 1.000287924, 1.000287864),
    (40, 75, 120, 633, 1.000299418, 1.000299406),
    (20, 100, 100, 633, 1.000267394, 1.000267394),
    (40, 100, 110, 1700, 1.000270247, 1.000270237),
    (20, 0, 101.325, 1700, 1.000268479, 1.000268483),
    (40, 100, 110, 300, 1.000289000, 1.000288922),
    (20, 0, 101.325, 300, 1.000286581, 1.000286579),
    (-40, 0, 120, 300, 1.000427233, 1.000427072),
)


def pytest_generate_tests(metafunc):
    metafunc.parametrize("row", list(data))


def test_refractive_index(row):
    nindex = [
        ri.RefractiveIndex(row[0], 10 * row[2], row[1], row[3], formula)
        for formula in range(0, 5)
    ]
    np.testing.assert_allclose(nindex[0], row[4], rtol=6e-9)
    np.testing.assert_allclose(nindex[1], row[5], rtol=4e-10)
    # write asserts for other formulas
