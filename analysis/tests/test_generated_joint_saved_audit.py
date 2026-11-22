# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only verification of the completed generated nonlinear work."""

from pathlib import Path

from lll.generated_joint_saved_audit import audit


ROOT = Path(__file__).resolve().parents[2]


def test_terminal_task_contains_three_complete_profiles_and_exact_receipts():
    result = audit(ROOT)
    assert result['no_native_recalculation'] is True
    assert result['source_future_generation_omitted'] == 119
    assert result['actual_construction_charges'] == result['expected_construction_charges']
    assert set(result['profiles']) == {'sphere_rotating', 'sphere_still', 'flat_still'}
    assert all(max(row['native_tangent_rms_m']) > 1 for row in result['profiles'].values())
