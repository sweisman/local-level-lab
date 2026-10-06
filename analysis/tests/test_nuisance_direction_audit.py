# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent algebraic controls for overlapping nuisance attribution."""
import numpy as np
import pytest

from audit_nuisance_directions import decompose
from audit_model_signal import signal_budget


PAIR = 'sphere_rotating_vs_sphere_still'


def matrix(*nuisance):
    eye = np.eye(6)
    return np.column_stack([eye[:, :3], *nuisance])


def test_orthogonal_nuisance_has_no_information_loss():
    eye = np.eye(6)
    result = decompose(matrix(eye[:, 3], eye[:, 4]), np.ones(6), {'a':[3], 'b':[4]})
    for value in result['attribution'].values():
        assert value['total_squared_retention_lost'] == pytest.approx(0.)
        assert list(value['all_order_attribution'].values()) == pytest.approx([0., 0.])


def test_redundant_exact_alias_shares_loss_without_order_dependence():
    e = np.eye(6)[:, 0]
    result = decompose(matrix(e, e), np.ones(6), {'first':[3], 'second':[4]})
    allocation = result['attribution'][PAIR]
    assert allocation['total_squared_retention_lost'] == pytest.approx(1.)
    assert allocation['all_order_attribution'] == pytest.approx({'first':.5, 'second':.5})


def test_auxiliary_direction_exposes_joint_alias():
    eye = np.eye(6)
    # Wind alone aliases half the first science direction. Adding a nuisance
    # confined to the auxiliary row allows wind to alias the entire direction.
    J = matrix(eye[:, 0] + eye[:, 3], eye[:, 3])
    result = decompose(J, np.ones(6), {'wind':[3], 'auxiliary':[4]})
    assert result['attribution'][PAIR]['all_order_attribution'] == pytest.approx({'wind':.75, 'auxiliary':.25})
    assert result['group_alone']['auxiliary']['model_contrast_information'][PAIR]['pre_cutoff_retained_fraction'] == pytest.approx(1.)


def test_nuisance_units_do_not_change_attribution():
    eye = np.eye(6)
    J = matrix(eye[:, 0] + eye[:, 3], eye[:, 3])
    original = decompose(J, np.ones(6), {'a':[3], 'b':[4]})
    J[:, 3] *= 1e-12
    J[:, 4] *= 1e12
    changed = decompose(J, np.ones(6), {'a':[3], 'b':[4]})
    for pair in original['attribution']:
        assert changed['attribution'][pair]['all_order_attribution'] == pytest.approx(original['attribution'][pair]['all_order_attribution'])


def test_missing_or_duplicate_nuisance_column_is_rejected():
    J = matrix(np.eye(6)[:, 0], np.eye(6)[:, 1])
    for groups in ({'a':[3]}, {'a':[3], 'b':[3, 4]}):
        with pytest.raises(ValueError, match='partition'):
            decompose(J, np.ones(6), groups)


def signal_bins(lat=0., east_speed=0.):
    return dict(dt=np.array([60., 60.]), lat=np.full(2, np.radians(lat)),
                h=np.full(2, 11000.), v_n=np.zeros(2), v_e=np.full(2, east_speed),
                lon_rate=np.zeros(2))


def test_stationary_equator_signal_is_horizontal_sidereal_rate():
    result = signal_budget(signal_bins())
    pair = result['pairs'][PAIR]
    assert pair['horizontal_norm_fraction'] == pytest.approx(1.)
    assert pair['horizontal_rms_dph'] == pytest.approx(15.041, abs=.001)
    assert pair['down_mean_dph'] == pytest.approx(0.)
    assert result['pairs']['sphere_still_vs_flat_still']['horizontal_norm_fraction'] is None


def test_eastward_transport_adds_and_westward_subtracts_north_rate():
    east = signal_budget(signal_bins(45., 200.))
    west = signal_budget(signal_bins(45., -200.))
    assert east['mean_north_globe_transport_dph'] > 0 > west['mean_north_globe_transport_dph']
    assert east['mean_north_sum_dph'] > east['mean_north_earth_rotation_dph'] > west['mean_north_sum_dph']
