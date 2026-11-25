# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import math
from pathlib import Path

import pytest

from lll import ilvis0_ncar_motion_match as match, ilvis0_stretch_checks as checks

ROOT = Path(__file__).resolve().parents[2]
RF04 = '2791235ca0b11b1ef4386e21'


def test_receiver_offsets_recover_a_known_lag_and_side_offset():
    # Near the equator a straight track keeps one east-west scale, so the generated answer is exact.
    lat0, lon0, course, speed = math.radians(10.), math.radians(-60.), math.radians(60.), 230.

    def place(t, right=0.):
        north = speed*math.cos(course)*t-right*math.sin(course)
        east = speed*math.sin(course)*t+right*math.cos(course)
        return lat0+north/match.RADIUS_M, lon0+east/(match.RADIUS_M*math.cos(lat0))

    rows = []
    for second in range(60):
        lat, lon = place(second)
        rows.append(dict(GGLAT=math.degrees(lat), GGLON=math.degrees(lon), GGALT=10000.))
    start = 302740
    times = [start+second for second in range(60)]+[start+10.5]
    gps = [(*place(second-.4, right=5.), 10020.+.01*second) for second in range(60)]+[(lat0, lon0, 0.)]
    found = match.receiver_offsets(rows, start, times, gps)
    assert [row['index_s'] for row in found] == list(range(60))
    for row in found:
        assert row['along_m'] == pytest.approx(-92., abs=.2) and row['right_m'] == pytest.approx(5., abs=.2)
        assert row['lag_s'] == pytest.approx(.4, abs=2e-3) and row['speed_mps'] == pytest.approx(230., abs=.2)
        assert row['horizontal_m'] == pytest.approx(math.hypot(92., 5.), abs=.2)
        assert row['height_change_difference_m'] == pytest.approx(.01*row['index_s'], abs=1e-9)
    rows[30]['GGLAT'] = None
    assert [row['index_s'] for row in match.receiver_offsets(rows, start, times, gps)] == [
        second for second in range(60) if second not in (29, 30, 31)]
    with pytest.raises(ValueError):
        match.receiver_offsets(rows, start, times[:1], gps[:1])


def test_week_second_follows_the_sunday_start_of_the_recorder_week():
    assert match.week_second('2011-10-12T12:05:40Z') == 302740
    assert match.week_second('2015-10-25T00:00:00Z') == 0
    assert match.week_second('2015-10-24T23:59:59Z') == 7*86400-1


def test_tasks_are_the_stretches_with_complete_aircraft_seconds():
    rows = match.tasks(ROOT)
    assert len(rows) == 32 and RF04 in {row['identity'] for row in rows}
    assert len({row['input_key'] for row in rows}) == 32
    for row in rows:
        seconds = row['seconds']
        assert row['aircraft_file'].split('.')[1] == row['date'].replace('-', '')
        assert row['limits'] == dict(native_calls=0, packet_visits=0, bound_calls=21,
            bound_steps=2*row['native_packets']+seconds+6*((seconds-1)+(seconds-1)//5+(seconds-1)//10))


def test_one_stretch_reproduces_the_published_rf04_comparison():
    task = next(row for row in match.tasks(ROOT) if row['identity'] == RF04)
    published = json.loads((ROOT/'docs/ilvis0-measurement-contribution/rf04-motion-match-result.json').read_bytes())

    class Context:
        root = ROOT/'data'/'ncar-motion-match-test'

        def input_path(self, key=None):
            return ROOT/dict(selection=checks.SELECTION, contexts=checks.CONTEXTS)[key]

    rows = json.loads((ROOT/match.EXTRACTS/(RF04+'.json')).read_bytes())['rows']
    values, times, gps, provenance = checks.load_stretch(task, Context())
    charged = []
    _, summary, comparisons = match.compare(rows, match.week_second(rows[0]['utc']), values,
        times+provenance['first_interval_start_utc_s'], gps, reserve=lambda **work: charged.append(work))
    assert sum(work['bound_calls'] for work in charged)+1 == task['limits']['bound_calls']
    assert sum(work['bound_steps'] for work in charged)+task['native_packets'] == task['limits']['bound_steps']
    assert summary['matched_receiver_seconds'] == published['matched_receiver_seconds'] == 443
    for key in ('horizontal_separation_m', 'relative_height_difference_m'):
        assert summary[key] == pytest.approx(published[key], rel=1e-9)
    assert summary['along_track_median_m'] == pytest.approx(-89.2, abs=.3)
    assert summary['right_of_track_median_m'] == pytest.approx(-.21, abs=.1)
    assert summary['lag_median_s'] == pytest.approx(.393, abs=.01)
    for mine, saved in zip(comparisons, published['comparisons'], strict=True):
        assert mine['error'] is None
        assert [mine[key] for key in ('clock', 'shift_s', 'window_s', 'windows', 'omitted')] == [
            saved[key] for key in ('clock', 'shift_s', 'window_s', 'windows', 'omitted')]
        assert mine['rotation_difference_deg'] == pytest.approx(saved['rotation_difference_deg'], rel=1e-9)
        assert mine['aircraft_rotation_deg'] == pytest.approx(saved['rf04_rotation_deg'], rel=1e-9)
        assert mine['group4_rotation_deg'] == pytest.approx(saved['group4_rotation_deg'], rel=1e-9)
