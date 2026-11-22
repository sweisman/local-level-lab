# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

import pytest

from lll.esa_reference_error_budget import evidence, evaluate_budget


ROOT = Path(__file__).resolve().parents[2]


def test_budget_requires_every_independent_error_cap():
    coefficients = dict(visible_range_rms_m=2., invisible_range_rms_m=1., anchor_axis_m=4.,
                        acceleration_rms_mps2=.5, linearization_score=1.)
    caps = dict(visible_range_rms_m=.1, invisible_range_rms_m=.1, anchor_axis_m=.1,
                acceleration_rms_mps2=.2, linearization_score=0.)
    incomplete = evaluate_budget(1., -.1, coefficients, caps | {'linearization_score': None})
    assert incomplete['status'] == 'abstain'
    assert incomplete['missing'] == ['linearization_score']
    assert evaluate_budget(1., -.1, coefficients, caps)['remaining_margin'] == pytest.approx(.1)
    assert evaluate_budget(.9, -.1, coefficients, caps)['status'] == 'abstain'


def test_actual_qaqartoq_budget_keeps_in_sample_cancellation_separate_from_caps():
    result = evidence(ROOT)
    assert result['current']['status'] == 'abstain'
    assert len(result['current']['missing']) == 5
    assert result['observations']['full_aircraft_score_equivalent'] == pytest.approx(.000112304463195299)
    assert result['observations']['invisible_aircraft_score_equivalent'] == pytest.approx(-.0018042937761457854)
    assert result['coefficients']['visible_range_rms_m'] == pytest.approx(22.369354586469317)
    assert result['coefficients']['invisible_range_rms_m'] == pytest.approx(4.520890798920056)
