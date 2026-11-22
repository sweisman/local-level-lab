# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

from lll.esa_girafe_matched_error_law import fixed_interrogation


def test_condition_requires_positive_observations_and_constant_twenty_milliseconds():
    constant = dict(rows=3990, minimum_half_interrogation_s=.02, maximum_half_interrogation_s=.02)
    assert fixed_interrogation(constant)
    assert not fixed_interrogation(constant | {'minimum_half_interrogation_s': .01})
    assert not fixed_interrogation(constant | {'rows': 0})
