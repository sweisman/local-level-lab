# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check saved component comparisons without fitting or regeneration."""

import pytest


def _rows():
    from lll.noise_component_decomposition import variants

    values = {'clean': 0., 'full': 4.}
    values.update({name: 1. for name in variants() if name.startswith('only-')})
    values.update({name: 3. for name in variants() if name.startswith('without-')})
    return {name: [[value, 0., 0.]] * 400
            for name, value in values.items()}


def test_saved_component_summary_exposes_nonadditivity_and_leave_out():
    from lll.noise_component_audit import summarize

    report = summarize(_rows())
    assert report['variants'] == 10
    assert report['nonadditive_3d_rms_m'] == 0.
    assert report['rows']['full']['horizontal_rms_m'] == 4.
    assert report['rows']['clean']['horizontal_rms_m'] == 0.
    assert all(value == 1. for value in
               report['leave_out_change_3d_rms_m'].values())
    assert all(value == 1. for value in
               report['only_change_3d_rms_m'].values())
    assert report['scientific_decision'] == 'abstain'


def test_saved_component_summary_requires_complete_finite_matrix():
    from lll.noise_component_audit import summarize

    rows = _rows()
    rows.pop('full')
    with pytest.raises(ValueError):
        summarize(rows)
    rows = _rows()
    rows['full'][0] = [float('nan'), 0., 0.]
    with pytest.raises(ValueError):
        summarize(rows)
