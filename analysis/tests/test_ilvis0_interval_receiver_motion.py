# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path

import pytest

from lll import ilvis0_interval_receiver_motion as motion, ilvis0_review_study as review
from lll import ilvis0_stretch_checks as checks

ROOT = Path(__file__).resolve().parents[2]


def test_range_rule_uses_the_published_extremes():
    published = [dict(p95_abs_climb_mps=1., max_abs_climb_mps=2., p95_abs_course_rate_deg_s=.02,
                      max_abs_course_rate_deg_s=.05, minimum_speed_kmh=710.),
                 dict(p95_abs_climb_mps=.5, max_abs_climb_mps=3., p95_abs_course_rate_deg_s=.04,
                      max_abs_course_rate_deg_s=.03, minimum_speed_kmh=800.)]
    edge = dict(p95_abs_climb_mps=1., max_abs_climb_mps=3., p95_abs_course_rate_deg_s=.04,
                max_abs_course_rate_deg_s=.05, minimum_speed_kmh=710.)
    assert motion.inside_published_range(edge, published)
    for key in motion.RATES:
        assert not motion.inside_published_range(dict(edge, **{key: edge[key]+1e-6}), published)
    assert not motion.inside_published_range(dict(edge, minimum_speed_kmh=709.9), published)


def test_tasks_are_the_published_and_recovered_intervals():
    rows = motion.tasks(ROOT)
    assert [row['kind'] for row in rows] == ['published']*53+['recovered']*16
    assert all(row['limits'] == review.NO_MODEL_WORK and row['end_s']-row['start_s'] >= 240. for row in rows)
    assert {row['filename'].split('_')[3] for row in rows if row['kind'] == 'recovered'} == {'510'}


def test_one_recovered_interval_reproduces_and_profiles():
    task = min((row for row in motion.tasks(ROOT) if row['kind'] == 'recovered'),
               key=lambda row: row['compressed_bytes'])

    class Context:
        root = ROOT/'data'/'interval-receiver-motion-test'
        manifest = dict(scope=motion.SCOPE)

        def input_path(self, key=None):
            return ROOT/checks.CONTEXTS

    result = motion.evaluate(task, Context())
    assert result['passed'] and result['imu_type'] == 6 and not result['gyro_used']
    assert result['profile']['minimum_speed_kmh'] > 600.
    assert result['profile']['duration_s'] == pytest.approx(task['end_s']-task['start_s'], abs=2.)
    with pytest.raises(ValueError):
        motion.evaluate(dict(task, start_s=task['start_s']+1.), Context())
