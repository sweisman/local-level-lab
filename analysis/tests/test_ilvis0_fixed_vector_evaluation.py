"""A complete joint calibration interpolation stays inside the frozen box."""

import numpy as np
import pytest

from lll.ilvis0_fixed_vector_evaluation import interpolate


def test_joint_vector_interpolation_has_exact_quarter_points():
    first=np.zeros(26)
    second=np.linspace(-.8,.8,26)
    assert np.array_equal(interpolate(first,second,2),second/2)
    assert np.allclose(interpolate(first,second,1),second/4)
    assert np.allclose(interpolate(first,second,3),second*3/4)
    with pytest.raises(ValueError):
        interpolate(first,second,0)
    with pytest.raises(ValueError):
        interpolate(first,second[:25],2)
