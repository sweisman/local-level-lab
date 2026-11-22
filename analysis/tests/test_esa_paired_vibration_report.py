"""Saved paired generated-control aggregation checks."""

import pytest

from lll.esa_paired_vibration_report import summarize_pairs


def test_summary_counts_paired_changes_without_claiming_coverage():
    rows = [
        dict(seed=1, technical_pass=True, max_z_off=2., max_z_on=4.,
             contained_off=True, contained_on=False),
        dict(seed=2, technical_pass=True, max_z_off=3., max_z_on=2.,
             contained_off=True, contained_on=True),
    ]
    result = summarize_pairs(rows)
    assert result['technical_passes'] == 2
    assert result['failure_counts'] == {'off': 0, 'on': 1}
    assert result['discordant_pairs'] == {'on_only': 1, 'off_only': 0}
    assert result['median_paired_max_z_difference'] == .5
    assert result['maximum_absolute_paired_max_z_difference'] == 2.
    assert result['generated_coverage_qualified'] is False


def test_summary_rejects_duplicate_seed():
    row = dict(seed=1, technical_pass=True, max_z_off=2., max_z_on=2.,
               contained_off=True, contained_on=True)
    with pytest.raises(ValueError, match='unique'):
        summarize_pairs([row, row])
