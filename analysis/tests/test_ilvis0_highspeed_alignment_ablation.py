# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

from lll import ilvis0_highspeed_alignment_ablation as ablation, ilvis0_segments as segments

ROOT = Path(__file__).resolve().parents[2]


def test_policy_changes_only_the_alignment_requirement():
    published = dict(segments.POLICY)
    changed = dict(ablation.POLICY)
    assert changed.pop('require_alignment_status') is False
    assert 'require_alignment_status' not in published
    assert changed.pop('version') == ablation.ID and published.pop('version') == segments.VERSION
    assert changed == published


def test_an_unaligned_sample_no_longer_splits_a_level_interval():
    nav = [dict(utc_week_s=float(t), velocity_north_mps=230., velocity_east_mps=0., velocity_down_mps=0.,
                roll_deg=0., alignment_status=1 if t == 200 else 0) for t in range(400)]
    receiver = [dict(utc_week_s=float(t), speed_mps=230.) for t in range(400)]
    runs = [dict(start_s=0., end_s=399., signature='s', imu_type=21, time_types=33)]
    assert segments.select_segments(nav, receiver, runs) == []
    recovered = segments.select_segments(nav, receiver, runs, policy=ablation.POLICY)
    assert len(recovered) == 1
    assert recovered[0]['start_s'] == 11. and recovered[0]['end_s'] == 388.
    slow = [dict(row, speed_mps=150.) if row['utc_week_s'] == 200 else row for row in receiver]
    assert segments.select_segments(nav, slow, runs, policy=ablation.POLICY) == []


def test_tasks_are_the_232_sealed_sources_with_no_model_allowance():
    rows = ablation.tasks(ROOT)
    assert len(rows) == 232 and rows == sorted(rows, key=lambda row: row['identity'])
    assert all(row['limits'] == dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)
               and len(row['source_sha256']) == 64 for row in rows)
