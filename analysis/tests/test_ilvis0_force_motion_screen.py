# SPDX-License-Identifier: AGPL-3.0-or-later
"""A necessary attitude motion bound independent of the omitted gyro data."""

import numpy as np
import pytest


def test_force_direction_pairs_can_rule_out_a_motion_limit_without_gyro():
    from lll.ilvis0_force_motion_screen import screen

    body = [[0., 0., -9.8], [0., 0., -9.9], [0., 0., -9.8]]
    frame = [[0., 0., -9.8], [9.9, 0., 0.], [9.8, 0., 0.]]
    result = screen(body, frame, [0., 1., 2.], maximum_rate_rad_s=.5,
                    body_direction_error_rad=[.02]*3, frame_direction_error_rad=[.03]*3)
    np.testing.assert_allclose(result['necessary_turn_rad'], [np.pi/2-.10, 0.])
    assert result['excluded_pairs'] == [0]
    assert result['attitude_identified'] is False
    assert result['scientific_decision'] == 'abstain'


def test_matching_direction_changes_do_not_certify_a_global_attitude_path():
    from lll.ilvis0_force_motion_screen import screen

    body = [[1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
    # A reflection of three orthogonal directions cannot be one fixed
    # proper rotation, even though every consecutive angle is the same.
    frame = [[0., 1., 0.], [1., 0., 0.], [0., 0., 1.]]
    result = screen(body, frame, [0., 1., 2.], maximum_rate_rad_s=0.,
                    body_direction_error_rad=[0.]*3, frame_direction_error_rad=[0.]*3)
    assert result['excluded_pairs'] == []
    assert result['global_attitude_feasibility_established'] is False


def test_force_direction_screen_requires_known_support_and_error_radii():
    from lll.ilvis0_force_motion_screen import screen

    with pytest.raises(ValueError, match='nonzero'):
        screen([[0., 0., 0.], [1., 0., 0.]], [[1., 0., 0.]]*2, [0., 1.],
               maximum_rate_rad_s=.5, body_direction_error_rad=[0., 0.],
               frame_direction_error_rad=[0., 0.])


def test_motion_witness_constructs_one_bounded_path_for_nominal_directions():
    from lll.ilvis0_force_motion_screen import nominal_witness

    angles = np.array([0., .3, .6])
    body = np.tile([0., 0., -1.], (3, 1))
    frame = np.column_stack((np.sin(angles), np.zeros(3), -np.cos(angles)))
    result = nominal_witness(body, frame, [0., 1., 2.], maximum_rate_rad_s=.31)
    assert result['nominal_witness_within_bound']
    np.testing.assert_allclose(result['turn_rad'], [.3, .3], rtol=0., atol=1e-15)
    np.testing.assert_allclose(np.einsum('nij,nj->ni', result['body_to_common'], body),
                               frame, rtol=0., atol=1e-15)
    assert result['attitude_identified'] is False
    result = nominal_witness(body, frame, [0., 1., 2.], maximum_rate_rad_s=.2)
    assert result['nominal_witness_within_bound'] is False
    assert result['excluded_pairs'] == [0, 1]
