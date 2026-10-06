# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent checks of attitude attribution and saved cutoff decomposition."""
import copy

import pytest

import audit_processing as audit


def test_frame_reconstruction_matches_independent_rotations():
    assert audit.orientation_fixture()['max_matrix_error'] < 1e-12


def test_aircraft_rotation_is_not_identifiable_as_a_mount_turn_from_gyro_alone():
    still = audit.turn_fixture()
    assert still['mount_rotation_error_deg'] < 1e-8
    for rate in (-3., 3.):
        overlap = audit.turn_fixture(rate)
        assert overlap['mount_rotation_error_deg'] > 10.
        integrated_aircraft = abs(rate)*(overlap['integration']['t1_s']-20.)
        assert overlap['mount_rotation_error_deg'] == pytest.approx(integrated_aircraft, abs=.2)
        assert overlap['flagged_unresolved'] is False


def test_timing_includes_initial_slack_and_accumulated_aircraft_turn_duration():
    sim = dict(legs=[[10., 15.], [190., 15.], [100., 15.]],
               index_turns=[[20., 'z'], [35., 'z']], turn_seconds=4.)
    turns = audit.aircraft_turn_intervals(sim['legs'])
    assert turns[0]['start_s'] == 1200.
    assert turns[1]['start_s'] == 2165.
    assert [r['imu_turn_min'] for r in audit.schedule_overlaps(sim)] == [20.]


def test_cutoff_only_failures_are_separate_from_nuisance_projection_failures():
    design = dict(rank_threshold=.3, anchors={'anchor': {'model_contrast_information': {
        'pair': dict(pre_cutoff_retained_fraction=.4, retained_fraction=.2)}}})
    assert audit.contrast_stages(design)['cutoff_only_failure']
    altered = copy.deepcopy(design)
    altered['anchors']['anchor']['model_contrast_information']['pair']['pre_cutoff_retained_fraction'] = .25
    assert not audit.contrast_stages(altered)['cutoff_only_failure']


@pytest.mark.parametrize('start', [None, 20.])
def test_forward_axis_known_maneuver_without_overlap(start):
    fixture = audit.forward_fixture(start)
    assert fixture['forward_available']
    assert abs(fixture['horizontal_axis_error_deg']) < .2
    if start is not None:
        assert fixture['mount_mapping_error_deg'] < 1e-8


def test_overlapping_roll_contaminates_mount_mapping_in_independent_fixture():
    fixture = audit.forward_fixture(60.)
    assert fixture['mount_mapping_error_deg'] > 5.


def test_timing_only_proposal_avoids_all_known_maneuvers():
    from lll.research_design import validate_turn_schedule
    turns = [5., 25., 40., 55., 70., 80.]
    validate_turn_schedule(turns, 90.)
    sim = dict(legs=[[v, 15.] for v in [10., 190., 100., 280., 10., 190.]],
               index_turns=[[v, 'z'] for v in turns], turn_seconds=4.)
    assert audit.schedule_overlaps(sim) == []
