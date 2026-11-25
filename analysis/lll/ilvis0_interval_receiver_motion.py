# SPDX-License-Identifier: AGPL-3.0-or-later
"""GPS-only motion profile of the published stretches and of the intervals recovered without the alignment flag.

One interval is one task. The profile uses receiver positions alone: no gyro,
no accelerometer and no fused navigation value. No Earth model is evaluated.
"""
import argparse
import csv
import gzip
import json
from pathlib import Path

from . import ilvis0_highspeed_alignment_ablation as ablation, ilvis0_review_study as review
from . import ilvis0_segments as segments, ilvis0_stretch_checks as checks
from .ilvis0_receiver_motion_profile import profile_fixes

ID = 'ilvis0-interval-receiver-motion-v1'
FOLDER = ablation.FOLDER
ADAPTER = 'analysis/lll/ilvis0_interval_receiver_motion.py'
TEST = 'analysis/tests/test_ilvis0_interval_receiver_motion.py'
PLAN = FOLDER+'RECEIVER_MOTION_PLAN.md'
OTHER = FOLDER+'other-intervals.csv'
REQUEST = FOLDER+'receiver-motion-qualification.json'
TEST_REPORT = FOLDER+'receiver-motion-tests.xml'
SCOPE = 'receiver-only motion profile of 53 published and 16 recovered intervals; no Earth-model fits'
RATES = ('p95_abs_climb_mps', 'max_abs_climb_mps', 'p95_abs_course_rate_deg_s', 'max_abs_course_rate_deg_s')
WALL_S = 2*3600
TESTS = ('test_range_rule_uses_the_published_extremes',
         'test_tasks_are_the_published_and_recovered_intervals',
         'test_one_recovered_interval_reproduces_and_profiles')


def inside_published_range(profile, published):
    """No climb or course-change measure above the largest published value, and no lower minimum speed."""
    return (all(profile[key] <= max(row[key] for row in published) for key in RATES)
            and profile['minimum_speed_kmh'] >= min(row['minimum_speed_kmh'] for row in published))


def tasks(root):
    """The 53 published stretches, then the 16 intervals found without the alignment requirement."""
    root = Path(root)
    with gzip.open(root/checks.SELECTION, 'rt') as stream:
        bounds = {row['segment']['segment_id']: row['segment'] for row in json.load(stream)['selected']}
    out = [dict(identity=row['segment_id'], kind='published', source_task=row['source_task'],
                filename=row['filename'], source_path=row['source_path'], source_sha256=row['source_sha256'],
                compressed_bytes=row['compressed_bytes'], start_s=bounds[row['segment_id']]['start_s'],
                end_s=bounds[row['segment_id']]['end_s']) for row in checks.stretches(root)]
    sources = {row['identity']: row for row in ablation.tasks(root)}
    with (root/OTHER).open(newline='') as stream:
        recovered = [row for row in csv.DictReader(stream) if row['relation'] == 'additional']
    for row in recovered:
        source = sources[row['task']]
        out.append(dict(identity=row['task'], kind='recovered', source_task=row['task'],
            filename=source['filename'], source_path=source['source_path'],
            source_sha256=source['source_sha256'], compressed_bytes=source['compressed_bytes'],
            start_s=float(row['start_week_s']), end_s=float(row['end_week_s'])))
    if (sum(row['kind'] == 'published' for row in out) != 53 or len(recovered) != 16
            or len({row['identity'] for row in out}) != len(out)):
        raise ValueError('the 53 published and 16 recovered intervals are required')
    return [dict(row, input_key='contexts', native_kind='value', limits=dict(review.NO_MODEL_WORK)) for row in out]


def code_sources(root):
    return review.code_sources(root, ADAPTER, TEST, 'analysis/tests/test_ilvis0_receiver_motion_profile.py')


def request(root):
    return review.request(root, sources=code_sources(root), output=REQUEST, report=TEST_REPORT)


def prepare(root):
    root = Path(root).resolve()
    inputs = dict(contexts=checks.CONTEXTS, selection=checks.SELECTION, analytics=checks.ANALYTICS,
                  packets=checks.PACKETS, recovered=OTHER, parent=ablation.PARENT)
    return review.prepare(root, identity=ID, scope=SCOPE, adapter=ADAPTER, plan=PLAN, sources=code_sources(root),
        qualification=REQUEST, tests=TESTS, inputs=inputs, tasks=tasks(root), wall_s=WALL_S)


def evaluate(task, context):
    from .studies.artifacts import safe_path

    root = Path(context.root).resolve().parents[1]
    contexts = json.loads(context.input_path('contexts').read_bytes())
    prior = [row for row in contexts['results'] if row['task_id'] == task['source_task']]
    if (context.manifest['scope'] != SCOPE or len(prior) != 1 or task['kind'] not in ('published', 'recovered')
            or prior[0]['inspection']['source_sha256'] != task['source_sha256']):
        raise ValueError('sealed interval and source bindings required')
    source = safe_path(root, task['source_path'])
    if source.stat().st_size != task['compressed_bytes']:
        raise ValueError('original source byte count changed')
    report = segments.scan(source, prior[0], policy=None if task['kind'] == 'published' else ablation.POLICY)
    found = [row for row in report['segments'] if (row['start_s'], row['end_s']) == (task['start_s'], task['end_s'])]
    if (report['source_sha256'] != task['source_sha256'] or len(found) != 1
            or (task['kind'] == 'published' and found[0]['segment_id'] != task['identity'])):
        raise ValueError('saved interval did not reproduce')
    result = dict(identity=task['identity'], kind=task['kind'], filename=task['filename'],
        start_s=task['start_s'], end_s=task['end_s'], imu_type=found[0]['imu_type'], profile=None, reason=None,
        scientific_decision='abstain', earth_model_fits=0, gyro_used=False, group1_motion_used_in_profile=False)
    try:
        result.update(profile=profile_fixes(found[0]['receiver_fixes']), passed=True)
    except ValueError as error:
        result.update(passed=False, reason=str(error))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
