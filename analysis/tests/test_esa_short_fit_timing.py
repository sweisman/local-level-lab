import numpy as np
import pytest

from lll.esa_short_fit_timing import prefix_counts, speed_gate


def test_short_prefix_retains_whole_latency_support_without_extra_packets():
    dt = np.full(200, .01)
    assert prefix_counts(dt, [0.2, 0.5, 0.7], training=2, offset=.025) == (53, 73)
    with pytest.raises(ValueError, match='support'):
        prefix_counts(dt[:71], [0.2, 0.5, 0.7], training=2, offset=.025)


def test_fit_speed_gate_requires_same_numerical_result_in_both_cases():
    assert speed_gate([dict(equivalent=True, fit_cpu_ratio=1.9), dict(equivalent=True, fit_cpu_ratio=1.2)])
    assert not speed_gate([dict(equivalent=False, fit_cpu_ratio=2.0), dict(equivalent=True, fit_cpu_ratio=1.8)])
    assert not speed_gate([dict(equivalent=True, fit_cpu_ratio=1.9), dict(equivalent=True, fit_cpu_ratio=.99)])
