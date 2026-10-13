# SPDX-License-Identifier: AGPL-3.0-or-later
import gzip
import hashlib
import json

import numpy as np
import pytest

from lll import ilvis0_rectangular_diagnosis as audit


def payload(point, residual, jacobian):
    return dict(active_parameters=['x', 'y'], normalized_parameters=point,
                residual=residual, jacobian=jacobian,
                convention='whitened residual derivative by normalized parameter')


def test_known_near_bound_stall_and_exact_bound_recovery():
    u = [np.nextafter(1., 0.), 0.]
    row = audit.inspect_linearization(payload(u, [u[0]-2., -.4], [[1., 0.], [0., 2.]]))
    assert row['near_outward_parameters'] == ['x']
    assert row['snap_maximum_change'] == 1.-u[0]
    assert row['original']['cost'] == pytest.approx(1.16, abs=1e-12)
    assert not row['original']['stationarity_passed']
    assert row['snapped']['cost'] == pytest.approx(1., abs=1e-12)
    assert row['snapped']['stationarity_passed']
    assert row['reference']['cost'] == pytest.approx(1., abs=1e-12)
    assert not row['qualifies_archival_fit']


def test_snapping_preserves_box_and_leaves_other_coordinates_unchanged():
    u = np.array([np.nextafter(-1., 0.), .999999])
    snapped = audit.snap_bounds(u)
    assert snapped[0] == -1.
    assert snapped[1] == u[1]
    assert np.all(abs(snapped) <= 1.)
    assert np.all(abs(snapped-u) <= 1e-12)
    assert u[0] != -1.


def test_rank_deficiency_remains_visible():
    row = audit.inspect_linearization(payload([0., 0.], [-1., 1.], [[1., 0.], [1., 0.]]))
    assert row['rank'] == 1
    assert row['condition'] is None
    assert row['weakest_direction'][0]['parameter'] == 'y'
    assert row['column_norms']['y'] == 0.
    json.dumps(row, allow_nan=False)


@pytest.mark.parametrize('change', [
    dict(normalized_parameters=[1.01, 0.]),
    dict(residual=[float('nan'), 0.]),
    dict(jacobian=[[1., 0.]]),
    dict(active_parameters=['x', 'x']),
    dict(convention='unknown'),
])
def test_invalid_saved_arrays_rejected(change):
    value = payload([0., 0.], [-1., 0.], [[1., 0.], [0., 1.]])
    value.update(change)
    with pytest.raises(ValueError):
        audit.inspect_linearization(value)


def test_artifact_hash_checked_before_decoding(tmp_path):
    content = gzip.compress(json.dumps(payload([0., 0.], [-1., 0.], [[1., 0.], [0., 1.]])).encode())
    (tmp_path/'local.json.gz').write_bytes(content)
    fit = dict(linearization_file='local.json.gz', linearization_sha256=hashlib.sha256(content).hexdigest())
    assert audit.load_linearization(tmp_path, fit)['active_parameters'] == ['x', 'y']
    fit['linearization_sha256'] = '0'*64
    with pytest.raises(ValueError, match='hash'):
        audit.load_linearization(tmp_path, fit)
    fit['linearization_file'] = '../local.json.gz'
    with pytest.raises(ValueError, match='filename'):
        audit.load_linearization(tmp_path, fit)


def test_saved_gradient_check_accounts_for_cancelling_dot_products():
    value = payload([0., 0.], [1., -1.], [[1e9, 0.], [1e9, 1.]])
    # Small absolute rounding differences are immaterial at the operand scale.
    audit.check_saved_gradient(value, [1e-6, -1.])
    with pytest.raises(ValueError, match='gradient'):
        audit.check_saved_gradient(value, [1., -1.])
