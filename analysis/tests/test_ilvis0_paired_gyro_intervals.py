import numpy as np
import pytest

from lll.ilvis0_paired_gyro_intervals import travel


def test_travel_counts_touching_packets_without_cancellation():
    angles = np.zeros((5, 3))
    angles[:, 0] = [.01, -.02, .03, -.04, .05]
    ends = np.arange(1, 6)*.5
    values = travel(ends, [.5]*5, angles, [.6, 0.], [1.3, .6], .001)
    assert values[0] == pytest.approx(.06 + 3*np.sqrt(3)*.001/2)
    assert np.isnan(values[1])
