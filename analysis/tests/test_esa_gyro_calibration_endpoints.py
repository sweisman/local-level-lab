# SPDX-License-Identifier: AGPL-3.0-or-later
from lll.esa_gyro_calibration_endpoints import direction_reversal


def test_reversal_requires_certified_gap_over_complete_fraction_range():
    assert direction_reversal(.1,.05,.01)
    assert not direction_reversal(.1,.095,.01)
    assert not direction_reversal(.1,.1,.01)
