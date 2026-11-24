# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path

import pytest

from lll.esa_ground_reference_evidence import (ADDITIONAL, BASE, COMBINED, QAQ_INTAKE, verify,
                                                verify_carrier_reports, verify_qaq_reports)


ROOT = Path(__file__).resolve().parents[2]


def test_current_nuuk_evidence_reproduces_without_runtime_data():
    index, checks = verify(ROOT, version=2)
    assert index['development_flight_groups'] == 1
    assert index['reserved_groups_opened'] == 0
    assert not index['aircraft_error_coverage_qualified']
    assert checks['public_reports'] == 12
    assert checks['verified_carrier_reports'] == 4


def test_combined_reference_evidence_keeps_both_stations_on_one_development_flight():
    index, checks = verify(ROOT, version=3)
    assert index['development_flight_groups'] == 1 and index['reserved_groups_opened'] == 0
    assert index['distant_high_rate_ground_coverage_verified'] is True
    assert index['high_rate_ground_coverage_verified'] is False
    assert index['joint_error_budget']['decision'] == 'abstain'
    assert len(index['studies']) == 14 and checks['public_reports'] == 17


def test_nuuk_museum_release_keeps_coverage_separate_from_aircraft_accuracy():
    index, checks = verify(ROOT, version=4)
    assert index['development_flight_groups'] == 1
    assert index['reserved_groups_opened'] == 0
    assert index['nuuk_museum_high_rate_ground_coverage_verified'] is True
    assert index['aircraft_error_coverage_qualified'] is False
    assert len(index['studies']) == 18 and checks['public_reports'] == 23
    assert index['nuuk_museum_error_budget']['decision'] == 'abstain'


def test_public_phase_replay_rejects_changed_signed_aircraft_correction():
    from lll.esa_ground_reference_evidence import verify_windup

    def read(name):
        return json.loads((ROOT/BASE/name).read_bytes())

    score = read('esa-carrier-score-bound-result.json')
    ground = read('esa-nkar-ground-score-result.json')
    phase = read('esa-nkar-phase-windup-result.json')
    verify_windup(score, ground, phase)
    phase['matched'][0]['air'][0] += .001
    with pytest.raises(ValueError, match='wind-up'):
        verify_windup(score, ground, phase)


def test_apron_release_checks_both_intervals_without_claiming_airborne_accuracy():
    index, checks = verify(ROOT, version=5)
    assert index['development_flight_groups'] == 1
    assert index['reserved_groups_opened'] == 0
    assert index['aircraft_error_coverage_qualified'] is False
    assert checks['verified_apron_range_steps'] == 138
    assert checks['verified_apron_motion_samples'] == 36_000
    assert len(index['apron']['studies']) == 3


def test_airborne_carrier_release_verifies_derived_evidence_and_preserves_abstention():
    index, checks = verify(ROOT, version=6)
    assert index['reserved_groups_opened'] == 0
    assert index['aircraft_error_coverage_qualified'] is False
    assert checks['public_reports'] == 33
    assert checks['verified_galileo_joint_bounds'] == 4
    assert checks['verified_two_station_witnesses'] == 3
    assert checks['verified_galileo_receiver_ranges'] == 2134


def test_nuuk_release_checks_original_and_extended_support():
    index, checks = verify(ROOT, version=7)
    assert index['reserved_groups_opened'] == 0
    assert index['aircraft_error_coverage_qualified'] is False
    assert checks['verified_nuuk_shared_ranges'] == 994
    assert checks['verified_nuuk_extended_ranges'] == 1236
    assert checks['verified_nuuk_recovered_seconds'] == 20
    assert checks['verified_nuuk_station_witnesses'] == 6


def test_nuuk_replay_rejects_change_to_shared_carrier_ranges():
    from lll.esa_nuuk_evidence import verify_comparisons

    original, diagnostic, extended = [json.loads((ROOT/BASE/name).read_bytes()) for name in (
        'esa-nuuk-near-stations-result.json', 'esa-nuuk-carrier-screen-result.json',
        'esa-nuuk-clock-aware-result.json')]
    verify_comparisons(original, diagnostic, extended)
    for row in extended['evidence']['near']:
        if row['start_gps_s'] == original['evidence']['near'][0]['start_gps_s']:
            row['permanent_m'][0] += .001
            row['permanent_m'][1] -= .001
            break
    with pytest.raises(ValueError, match='shared ranges'):
        verify_comparisons(original, diagnostic, extended)


@pytest.mark.parametrize('kind', ['north', 'joint', 'stations'])
def test_airborne_carrier_replay_rejects_changed_values(kind):
    from lll.esa_airborne_carrier_evidence import verify_joint, verify_north, verify_stations

    def load(name):
        return json.loads((ROOT/BASE/(name+'.json')).read_bytes())

    if kind == 'north':
        result = load('esa-galileo-north-witness-result')
        verify_north(result)
        result['residuals']['mosaic03'][0]['predicted_shift_m'][0] += .001
        with pytest.raises(ValueError, match='airborne carrier'):
            verify_north(result)
    elif kind == 'joint':
        parent = load('esa-carrier-continuous-bound-result')
        result = load('esa-galileo-joint-bound-result')
        verify_joint(parent, result)
        result['cases'][0]['joint_upper'] -= .001
        with pytest.raises(ValueError, match='airborne carrier'):
            verify_joint(parent, result)
    else:
        parent = load('esa-nkar-phase-transfer-result')
        result = load('esa-two-station-score-result')
        verify_stations(parent, result)
        result['witnesses']['positive_gap']['common'][0] += .001
        with pytest.raises(ValueError, match='airborne carrier'):
            verify_stations(parent, result)


@pytest.mark.parametrize('change', ['range', 'time', 'gyro', 'acquisition'])
def test_apron_replay_rejects_changed_saved_values(change):
    from lll.esa_apron_evidence import verify_overlap

    def read(name):
        return json.loads((ROOT/BASE/name).read_bytes())

    acquisition = read('esa-apron-imu-overlap-acquisition.json')
    result = read('esa-apron-imu-ranges-result.json')
    verify_overlap(acquisition, result)
    if change == 'range':
        result['ranges'][0]['aircraft_m'][1] += .001
    elif change == 'time':
        result['ranges'][1]['gps_s'] = result['ranges'][0]['gps_s']
    elif change == 'gyro':
        result['motion']['complete_bin_means'][0]['mean_xyz_deg_per_hour'][0] += 1
    else:
        acquisition['following_marker_gps_s'] += .5
    with pytest.raises(ValueError, match='apron'):
        verify_overlap(acquisition, result)


def test_combined_reference_refuses_changed_distant_transfer_even_without_digest_check():
    def load(name):
        return json.loads((ROOT/BASE/name).read_bytes())

    intake = load(QAQ_INTAKE)
    products, score = [load(row[0]) for row in ADDITIONAL[:2]]
    ground, transfer = [load(row[0]) for row in COMBINED[:2]]
    transfer['withheld']['earlier_gain_rms_m'] += .001
    with pytest.raises(ValueError, match='chronological range transfer'):
        verify_qaq_reports(intake, products, score, ground, transfer)


@pytest.mark.parametrize('report,path', [
    (0, ('product_summary', 'final_fixed_rms_m')),
    (1, ('minimum_range_rms_m',)),
    (2, ('tolerances', 2, 'maximum_anchor_axis_error_m')),
    (3, ('cadences', 'ideal_1s', 'observable_norm_fraction')),
])
def test_nuuk_arithmetic_rejects_changed_summary_even_without_digest_check(report, path):
    rows = [json.loads((ROOT/BASE/name).read_bytes()) for name, *_ in ADDITIONAL]
    altered = rows[report]
    for part in path[:-1]:
        altered = altered[part]
    altered[path[-1]] += .01
    verify_carrier_reports(*[json.loads((ROOT/BASE/name).read_bytes()) for name, *_ in ADDITIONAL])
    with pytest.raises(ValueError, match='carrier evidence'):
        verify_carrier_reports(*rows)
