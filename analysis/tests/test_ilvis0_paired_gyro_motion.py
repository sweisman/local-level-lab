import numpy as np
import pytest

from lll.ilvis0_paired_gyro_motion import summaries


def test_one_second_measure_keeps_turns_that_cancel():
    angles = np.zeros((4, 3))
    angles[:, 0] = [.1, -.1, .1, -.1]
    out = summaries([.5, 1., 1.5, 2.], [.5]*4, angles, 2., .01)
    assert out['packets'] == 4 and out['whole_second_windows'] == 2
    assert out['peak_packet_rad_s'] == pytest.approx(.2)
    assert out['peak_one_second_rad_s'] == pytest.approx(.2)
    assert out['packet_peak_with_half_count_rad_s'] > .2


def test_no_nearly_complete_second_is_reported_as_no_summary():
    out = summaries([.3, .7, 1.1], [.4]*3, np.zeros((3, 3)), 1., .01)
    assert out['packets'] == 1 and out['whole_second_windows'] == 0
    assert out['peak_one_second_rad_s'] is None
