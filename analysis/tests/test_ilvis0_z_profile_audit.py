# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import json
from pathlib import Path

import pytest


def data():
    root = Path(__file__).resolve().parents[2]/'docs/ilvis0-z-profile-20261011'
    return json.loads((root/'summary.json').read_text()), json.loads((root/'manifest.json').read_text())


def compare(summary, manifest):
    from lll import ilvis0_z_profile_audit
    return ilvis0_z_profile_audit.compare(summary, manifest)


def test_completed_grid_preserves_rank_and_separates_fixed_from_free_limits():
    summary, manifest = data()
    out = compare(summary, manifest)
    assert out['converged'] == out['starts'] == 27
    assert out['native_predictions'] == out['optimizer_starts'] == 0
    assert out['shape_preference'] == 'globe'
    assert out['background_field_preference'] == 'specified_field'
    preferred = out['models'][0]
    assert preferred['remaining_boundary_count_min'] == 0
    assert preferred['remaining_boundary_count_max'] == 1
    assert preferred['cost_range_percent'] < 3
    assert out['hardware_calibration_identified'] is False
    assert len(out['weak_directions']) == 27*24*3


@pytest.mark.parametrize('error', ['identity', 'fixed_physical', 'fixed_normalized', 'gradient', 'spectrum'])
def test_corrupt_saved_calibration_diagnostics_rejected(error):
    summary, manifest = data(); f = summary['fits'][0]
    if error == 'identity': f['identity'] = summary['fits'][1]['identity']
    if error == 'fixed_physical': f['parameters']['gyro_gain_z'] = 0
    if error == 'fixed_normalized': f['fixed_normalized_coordinates']['gyro_bias_z'] = 0
    if error == 'gradient': f['projected_gradient'][0] += 1
    if error == 'spectrum': f['right_singular_vectors'][0][0] += 1
    with pytest.raises(ValueError): compare(summary, manifest)


def test_unfinished_fit_withholds_complete_grid_interpretation():
    summary, manifest = data()
    summary['fits'][0]['converged'] = False
    out = compare(summary, manifest)
    assert out['shape_preference'] == 'unresolved'
    assert out['background_field_preference'] is None
    assert out['converged'] == 26
