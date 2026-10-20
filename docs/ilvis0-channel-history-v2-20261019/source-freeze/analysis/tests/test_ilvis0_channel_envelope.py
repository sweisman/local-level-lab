# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.ilvis0_channel_envelope import centers, coordinate_error_box, integration_intervals, prepare_jets, assess


def sample():
    edges = np.arange(4001)*.005-10.
    values = np.column_stack((np.arange(4000), edges[1:], np.diff(edges),
        np.zeros(4000), np.zeros(4000), np.full(4000, -4905000)))
    times = np.arange(-20., 21.)
    coordinates = np.tile([.7, .2, 1200.], (len(times), 1))
    return values, times, coordinates


def test_centers_use_saved_geometry_only():
    assert centers(dict(start_s=100., end_s=500.)) == [140., 300., 460.]


@pytest.mark.parametrize('clock', ['nominal', 'header'])
def test_stationary_constructed_history_uses_correct_whole_packet_support(clock):
    values, times, points = sample()
    batch = prepare_jets(values, times, points, 0., clock, 1.)
    assert batch['supported']
    assert 130 <= batch['operators'] <= 150
    for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
        result = assess(values, batch, model=model, velocity_scale=1e-8, calibration='narrow')
        assert result['relation'] == 'overlap'
        assert result['force_boxes'] == batch['operators']
        assert result['scientific_decision'] == 'abstain'


def test_header_and_nominal_time_hypotheses_remain_distinct():
    values, _, _ = sample()
    values[:, 2] *= 1.0001
    with pytest.raises(ValueError):
        prepare_jets(values, np.arange(-20., 21.), np.tile([.7, .2, 1200.], (41, 1)), 0., 'header', 1.)
    assert not np.array_equal(integration_intervals(values, 'nominal'), integration_intervals(values, 'header'))


def test_receiver_gaps_preserved_instead_of_replacing_center():
    values, times, points = sample()
    selected = (times < -2.) | (times > 2.)
    batch = prepare_jets(values, times[selected], points[selected], 0., 'nominal', 1.)
    assert not batch['supported']
    assert batch['reason'] == 'receiver_gap'


def test_longitude_chart_crossing_is_not_silently_unwrapped():
    with pytest.raises(ValueError):
        coordinate_error_box([[.5, 3.14, 1000.], [.5, -3.14, 1000.]], 1.)


def test_polar_coordinate_error_rejected():
    with pytest.raises(ValueError):
        coordinate_error_box([[np.pi/2, 0., 1000.]], 1.)


def test_observable_derivative_conflict_stays_unsupported():
    values, times, points = sample(); points[:, 2] += 100.*times
    batch = prepare_jets(values, times, points, 0., 'nominal', 1.)
    assert not batch['supported']
    assert batch['reason'] == 'observable_derivative_envelope_conflict'
    assert assess(values, batch, model='sphere_still', velocity_scale=1e-8,
        calibration='broad')['force_boxes'] == 0
