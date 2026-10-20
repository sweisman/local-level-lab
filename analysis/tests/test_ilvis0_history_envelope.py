# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_history_envelope import central_average_bounds, inventory, prepare_group, assess_group, shared_zero_check
from test_ilvis0_channel_envelope import sample


def test_central_tent_average_attains_bound():
    result = central_average_bounds([[-.5, 0.], [0., .5]], [9., 9.],
        center_s=0., offset_bounds_s=[0., 0.], maximum_rate_mps3=2.)
    # q=9+2*abs(t), whose exact average is 9.5.
    assert result['averaging_error_mps2'] == .5
    assert result['bounds_mps2'] == [8.5, 9.5]


def test_disjoint_union_excludes_gaps_from_central_average():
    result = central_average_bounds([[0., .2], [.8, 1.]], [9., 10.],
        center_s=.5, offset_bounds_s=[-.1, .2], maximum_rate_mps3=1.)
    assert result['averaging_error_mps2'] == pytest.approx(.4)
    assert result['synchronization_error_mps2'] == .2
    np.testing.assert_allclose(result['bounds_mps2'], [8.4, 10.6])


@pytest.mark.parametrize('offset', [-.15, 0., .15])
def test_linear_true_average_inside_central_envelope(offset):
    intervals = np.array([[-.5, -.1], [.1, .4]])
    result = central_average_bounds(intervals, [10., 10.], center_s=0.,
        offset_bounds_s=[-.15, .15], maximum_rate_mps3=3.)
    duration = np.diff(intervals, axis=1).ravel()
    actual = np.dot(duration, 10.+3.*(intervals.mean(axis=1)+offset))/duration.sum()
    assert result['bounds_mps2'][0] <= actual <= result['bounds_mps2'][1]


@pytest.mark.parametrize('intervals,bounds,offset,rate', [
    ([[0., 0.]], [9., 10.], [0., 0.], 1.),
    ([[0., 1.], [.9, 2.]], [9., 10.], [0., 0.], 1.),
    ([[0., 1.]], [10., 9.], [0., 0.], 1.),
    ([[0., 1.]], [9., 10.], [.1, -.1], 1.),
    ([[0., 1.]], [9., 10.], [0., 0.], -1.),
    ([[0., np.inf]], [9., 10.], [0., 0.], 1.)])
def test_invalid_central_bound_inputs_rejected(intervals, bounds, offset, rate):
    with pytest.raises(ValueError):
        central_average_bounds(intervals, bounds, center_s=0., offset_bounds_s=offset, maximum_rate_mps3=rate)


def test_packet_groups_do_not_change_with_observed_force_or_clock():
    values, times, points = sample()
    segment = dict(start_s=-10., end_s=10.)
    before = inventory(values, times, segment)
    changed = values.copy(); changed[:, 3:6] *= -100.
    assert before == inventory(changed, times, segment)
    assert len(before['groups']) == 20
    indices = [i for g in before['groups'] if g['eligible'] for i in range(g['first_packet'], g['first_packet']+200)]
    assert len(indices) == len(set(indices))


def test_edge_groups_stay_excluded_with_no_replacement():
    values, times, _ = sample()
    result = inventory(values, times, dict(start_s=-10., end_s=10.))
    assert not any(g['eligible'] for g in result['groups'])  # 16-second stencil cannot fit.
    assert all(g['reason'] == 'receiver_support_margin' for g in result['groups'])


def test_full_group_pipeline_and_serialized_batch_match():
    import json
    import ilvis0_channel_envelope_worker as snapshot
    values, times, points = sample()
    # Enlarge declared selection so a central group has complete eligible stencil.
    group = dict(first_packet=2000, packet_count=200, group_index=10, eligible=True)
    result = prepare_group(values, times, points, group, 'nominal', 1.)
    assert result['supported']
    restored = json.loads(json.dumps(snapshot.plain(result)))
    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        before = assess_group(values, result, model=model, velocity_scale=1e-8)
        after = assess_group(values, restored, model=model, velocity_scale=1e-8)
        assert before == after
        assert before['comparisons']['zero']['relation'] == 'overlap'


def test_individual_overlaps_do_not_establish_shared_calibration():
    rows = [dict(supported=True, comparisons={'zero':dict(relation='overlap')}),
            dict(supported=True, comparisons={'zero':dict(relation='disjoint')})]
    result = shared_zero_check(rows)
    assert not result['zero_calibration_not_excluded_everywhere']
    assert not result['joint_receiver_history_feasibility_established']


def test_missing_group_prevents_complete_shared_point_claim():
    result = shared_zero_check([dict(supported=False)])
    assert not result['zero_calibration_not_excluded_everywhere']
    assert result['unsupported_groups'] == 1
