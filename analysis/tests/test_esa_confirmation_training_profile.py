# SPDX-License-Identifier: AGPL-3.0-or-later
from math import cos, radians, sin

import pytest

from lll.esa_confirmation_training_profile import profile


def test_receiver_profile_uses_actual_time_and_wraps_course():
    rows = [dict(time_s=t, height_m=30., north_mps=100*cos(radians(heading)),
                 east_mps=100*sin(radians(heading)), up_mps=-2., pdop=1.2,
                 satellites=10, reported_height_sd_m=.05)
            for t, heading in ((0., 359.), (2., 1.), (3., 2.))]
    result = profile(rows)
    assert result['absolute_course_rate_degps']['median'] == pytest.approx(1.)
    assert result['horizontal_speed_mps']['median'] == pytest.approx(100.)
    assert result['absolute_vertical_speed_mps']['median'] == pytest.approx(2.)
    assert result['reported_height_sd_m']['median'] == pytest.approx(.05)
    assert result['rows'] == 3
