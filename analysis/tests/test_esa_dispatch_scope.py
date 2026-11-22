# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

import pytest

from lll.esa_dispatch_scope import audit, check_horizon


ROOT = Path(__file__).resolve().parents[2]


def test_completed_scope_audit_keeps_numerical_equivalence_separate_from_accuracy():
    result = audit(ROOT)
    assert result['settings'] == 8 and result['paths'] == 32
    assert result['criteria_checked'] == 384
    assert result['settings_passing'] == {'120': 4, '240': 4, '400': 2}
    assert result['minimum_limit_margin_m'] == pytest.approx(1.9041289852182572)
    assert result['validation_recordings'] == 0
    assert result['observed_method_for_untested_inputs'] == 'wide'


def test_horizon_fails_closed_on_a_near_boundary_or_inconsistent_flag():
    limits = {'horizontal_rms_m': 10.}
    outcome = {'limits': {'limits': limits, 'checks': {'horizontal_rms_m': True}, 'passed': True,
                          'calibrated_goodness_of_fit': False, 'scientific_decision': 'abstain'},
               'score': {'horizontal_rms_m': 9.995}}
    with pytest.raises(ValueError, match='within'):
        check_horizon(outcome, limits, .01)
    outcome['score']['horizontal_rms_m'] = 11.
    with pytest.raises(ValueError, match='flag'):
        check_horizon(outcome, limits, .01)
