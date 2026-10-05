# SPDX-License-Identifier: AGPL-3.0-or-later
"""Sensor rotations split averaging intervals, not stable aircraft cruise qualification."""
import numpy as np
import pytest

from lll import segments


def fixture(monkeypatch, seconds=1201, events=(), exclude=(), maneuver=None, timestamp_gap=None):
    t = np.arange(seconds, dtype=float)
    if timestamp_gap:
        t[t >= timestamp_gap[0]] += timestamp_gap[1]
    kin = {"t": t, "speed": np.full(seconds, 220.), "vz": np.zeros(seconds),
           "psi_dot": np.zeros(seconds), "h_acc": np.ones(seconds), "bearing_ok": np.ones(seconds, bool),
           "psi": np.zeros(seconds), "lat": np.full(seconds, .6), "lon": np.zeros(seconds),
           "h": np.full(seconds, 10000.), "v_n": np.full(seconds, 220.), "v_e": np.zeros(seconds),
           "lon_rate": np.zeros(seconds)}
    if maneuver:
        kin["psi_dot"][(t >= maneuver[0]) & (t <= maneuver[1])] = .1
    streams = {"gnss": {"t_ns": (t*1e9).astype(np.int64)},
               "accel": {"t_ns": (t*1e9).astype(np.int64), "x": np.zeros(seconds),
                         "y": np.zeros(seconds), "z": np.full(seconds, 9.81)},
               "gyro": {"t_ns": (t*1e9).astype(np.int64), "x": np.zeros(seconds),
                        "y": np.zeros(seconds), "z": np.zeros(seconds)}}
    class Session:
        def slice(self, name, *args): return self.streams[name]
        def gyro_stream(self): return "gyro"
    sess = Session()
    sess.streams = streams
    sess.events = [(int(time*1e9), kind, "") for time, kind in events]
    monkeypatch.setattr(segments, "gnss_kinematics", lambda *args: kin)
    th = segments.Thresholds()
    intervals, kinematics = segments.find_segments(sess, {"start_ns": 0, "end_ns": int(seconds*1e9)}, th, exclude)
    return sess, th, intervals, kinematics


def test_deliberate_turns_keep_qualified_cruise_without_crossing_mount_frames(monkeypatch):
    turns = [300, 600, 900]
    exclusions = [(t-10, t+1) for t in turns]
    sess, th, intervals, kin = fixture(monkeypatch, events=[(t, "index_turn") for t in turns], exclude=exclusions)
    assert len(intervals) == 4
    assert all(b-a < th.min_segment_s for a, b in intervals)
    bins = segments.make_bins(sess, intervals, kin, th)
    assert len(bins["t"]) >= 16
    for center, duration in zip(bins["t"], bins["dt"]):
        assert all(center+duration/2 <= a or center-duration/2 > b for a, b in exclusions)


@pytest.mark.parametrize("kind", ["placement_shift", "imu_disconnect"])
def test_unqualified_fragments_cannot_bridge_hard_breaks(monkeypatch, kind):
    _, _, intervals, _ = fixture(monkeypatch, events=[(t, kind) for t in (300, 600, 900)])
    assert intervals == []


def test_deliberate_turn_does_not_qualify_aircraft_maneuver(monkeypatch):
    _, _, intervals, _ = fixture(monkeypatch, events=[(600, "index_turn")], exclude=[(575, 625)], maneuver=(575, 625))
    assert intervals == []


def test_unknown_exclusion_cannot_bridge_cruise(monkeypatch):
    _, _, intervals, _ = fixture(monkeypatch, exclude=[(t-10, t+1) for t in (300, 600, 900)])
    assert intervals == []


def test_short_uninterrupted_cruise_still_fails_duration_requirement(monkeypatch):
    _, _, intervals, _ = fixture(monkeypatch, seconds=599)
    assert intervals == []


def test_missing_fixes_do_not_bridge_short_cruise_runs(monkeypatch):
    _, _, intervals, _ = fixture(monkeypatch, seconds=1200, timestamp_gap=(600, 30))
    assert intervals == []
