"""Saved observed-start audit keeps the original failure immutable."""

from pathlib import Path


def test_saved_esa_start_audit_replays_sealed_pairs():
    from lll.esa_dispatch_start_equivalence_v2 import audit

    root = Path(__file__).resolve().parents[2]
    result = audit(root)
    assert result['verified'] is True
    assert result['frozen_qualified'] is False
    assert result['retrospective_only'] is True
    assert result['new_fits'] == 0
    assert len(result['groups']) == 8
    assert result['retrospective_passing_groups'] == 8
    assert max(group['rule']['reference_within_maximum_m']
               for group in result['groups']) < 0.01
    assert all(group['rule']['absolute_cost_tolerance'] == 0
               for group in result['groups'])
    assert all(group['rule']['relative_cost_tolerance'] == 1e-8
               for group in result['groups'])
    assert all(group['rule']['forecast_epochs'] == 1200
               for group in result['groups'])
