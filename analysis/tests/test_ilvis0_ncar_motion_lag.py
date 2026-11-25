# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import math
from pathlib import Path

import numpy as np
import pytest

from lll import ilvis0_ncar_motion_lag as lag, ilvis0_ncar_motion_match as match, ilvis0_stretch_checks as checks

ROOT = Path(__file__).resolve().parents[2]
RF04 = '2791235ca0b11b1ef4386e21'


def test_a_known_label_delay_is_matched_only_at_its_own_shift():
    first, seconds, delay = 1000, 60, .4

    def roll(t):
        return math.radians(2.)*math.cos(2*math.pi*t/7.)

    ends = first-.2+.005*np.arange(1, int((seconds+1)/.005)+1)
    values = np.zeros((len(ends), 12))
    values[:, 1], values[:, 2] = ends, .005
    values[:, 9] = [roll(t)-roll(t-.005) for t in ends]
    rows = [dict(ROLL=math.degrees(roll(first+second+delay)), PITCH=0., THDG=0.) for second in range(seconds)]
    charged = []
    found = lag.compare(rows, first, values, dict(none=0., gps_lag=delay, one_second_average=lag.AVERAGE_S),
                        reserve=lambda **work: charged.append(work))
    assert len(found) == lag.COMPARISONS and len(charged) == lag.COMPARISONS+1
    assert all(entry['error'] is None and entry['windows'] > 0 for entry in found)
    worst = {name: max(entry['rotation_difference_deg']['maximum'] for entry in found if entry['shift'] == name)
             for name in lag.SHIFTS}
    assert worst['gps_lag'] < 1e-6 and worst['none'] > .1 and worst['one_second_average'] > .01
    with pytest.raises(ValueError):
        lag.shifts(5.)


def test_tasks_carry_the_saved_gps_lag_and_declared_steps():
    rows = lag.tasks(ROOT)
    assert len(rows) == 32 and [row['identity'] for row in rows] == [row['identity'] for row in match.tasks(ROOT)]
    for row in rows:
        seconds = row['seconds']
        assert .39 < row['gps_lag_s'] < .45
        assert row['limits'] == dict(native_calls=0, packet_visits=0, bound_calls=20,
            bound_steps=2*row['native_packets']+6*((seconds-1)+(seconds-1)//5+(seconds-1)//10))


def test_unshifted_windows_reproduce_the_closed_comparison():
    task = next(row for row in lag.tasks(ROOT) if row['identity'] == RF04)
    saved = next(row for row in json.loads((ROOT/lag.PARENT).read_bytes())['rows'] if row['segment_id'] == RF04)

    class Context:
        root = ROOT/'data'/'ncar-motion-lag-test'

        def input_path(self, key=None):
            return ROOT/dict(selection=checks.SELECTION, contexts=checks.CONTEXTS)[key]

    rows = json.loads((ROOT/match.EXTRACTS/(RF04+'.json')).read_bytes())['rows']
    values, _, _, _ = checks.load_stretch(task, Context())
    charged = []
    found = lag.compare(rows, match.week_second(rows[0]['utc']), values, lag.shifts(task['gps_lag_s']),
                        reserve=lambda **work: charged.append(work))
    assert sum(work['bound_calls'] for work in charged)+1 == task['limits']['bound_calls']
    assert sum(work['bound_steps'] for work in charged)+task['native_packets'] == task['limits']['bound_steps']
    for entry in found:
        if entry['clock'] == 'header_elapsed' and entry['shift'] == 'none':
            assert entry['rotation_difference_deg']['rms'] == pytest.approx(
                saved[f"rotation_difference_rms_{entry['window_s']}s_deg"], rel=1e-9)
