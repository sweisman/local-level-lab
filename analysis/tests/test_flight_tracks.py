# SPDX-License-Identifier: AGPL-3.0-or-later
import csv
import pytest

from import_flight_tracks import read_track, summary


def export(tmp_path, rows):
    path = tmp_path/'2025-09-01 etihad 10 ord auh.csv'
    with path.open('w', newline='') as output:
        writer = csv.writer(output)
        writer.writerow(['Time', 'Latitude', 'Longitude', 'Course', 'Knots', 'Feet', 'Source'])
        writer.writerows(rows)
    return path


def test_midnight_units_and_missing_values_are_preserved(tmp_path):
    path = export(tmp_path, [('Mon 23:59:30', 35, -30, '→ 91°', '300', '35000', 'ADS-B'),
                             ('Tue 00:00:30', 35, -29, '↘ 100°', '', '', 'ADS-B')])
    track = read_track(path)
    assert track['rows'][1]['t_s'] == 60
    assert track['rows'][0]['ground_speed_mps'] == pytest.approx(154.3333333333)
    assert track['rows'][0]['reported_altitude_m'] == pytest.approx(10668)
    assert track['rows'][1]['ground_speed_mps'] is None
    assert track['rows'][1]['reported_altitude_m'] is None
    assert summary(track)['missing_altitude_points'] == 1


def test_large_gap_never_counts_as_window_coverage(tmp_path):
    track = read_track(export(tmp_path, [('Mon 00:00:00', 35, -30, '359°', '300', '35000', 'ADS-B'),
                                          ('Mon 01:15:00', 35, -29, '1°', '300', '35000', 'ADS-B')]))
    report = summary(track)
    assert report['windows_75min'][0]['observed_coverage_fraction'] == 0
    assert report['windows_75min'][0]['minimum_course_arc_deg'] == 2
    assert report['coverage95_windows'] == 0


def test_out_of_order_clock_is_rejected(tmp_path):
    path = export(tmp_path, [('Mon 10:01:00', 35, -30, '90°', 300, 35000, 'ADS-B'),
                             ('Mon 10:00:00', 35, -29, '90°', 300, 35000, 'ADS-B')])
    with pytest.raises(ValueError, match='out-of-order'):
        read_track(path)


def test_estimated_coordinates_do_not_count_as_observed_coverage(tmp_path):
    rows = [(f'Mon {i//60:02d}:{i%60:02d}:00', 35, -30, '90°', 300, 35000, 'Estimated') for i in range(76)]
    track = read_track(export(tmp_path, rows))
    assert track['rows'][0]['source'] == 'Estimated' and track['rows'][0]['is_provider_estimate']
    report = summary(track)
    assert report['provider_estimated_points'] == 76
    assert report['windows_75min'][0]['table_coverage_fraction'] == 1
    assert report['windows_75min'][0]['observed_coverage_fraction'] == 0
    assert report['reported_latitude_range_deg'] is None
