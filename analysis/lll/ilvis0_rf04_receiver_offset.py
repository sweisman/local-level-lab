# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate fixed spatial offsets from delay-like offsets on the saved RF04 track."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import ilvis0_rf04_motion_match as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-receiver-offset-v1'
SCOPE = 'Earlier-only diagnosis of the relative RF04 receiver offset on the same UTC series'
PLAN = parent.FOLDER + 'RF04_RECEIVER_OFFSET_PLAN.md'
RESULT = parent.FOLDER + 'rf04-receiver-offset-result.json'
PARENT_SHA = '64213fd0ad7f06673683245c0f0df4a3768fc6f4ceda48a879ff302742a6f38b'
TEST = 'analysis/tests/test_ilvis0_rf04_receiver_offset.py'
TESTS = ('test_rf04_offset_recovers_delay_and_bias_while_testing_later_values',
         'test_rf04_offset_separates_halves_and_abstains_for_constant_velocity')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
TASK = dict(identity='rf04-receiver-offset', input_key='layout', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=5, bound_steps=5*parent.EPOCHS))


def split_indices(count):
    import numpy as np

    midpoint = count//2
    return np.arange(1, midpoint-1), np.arange(midpoint+1, count-1)


def compare_models(velocity, delta, early, later, *, reserve=lambda: None):
    import numpy as np

    if len(early) < 2 or len(later) < 2 or early[-1] >= later[0]:
        raise ValueError('disjoint earlier and later support is required')
    v, y = velocity[early], delta[early]

    def score(offset, delay):
        left = y - offset - delay*v
        right = delta[later] - offset - delay*velocity[later]
        return dict(offset_ne_m=offset.tolist(), delay_s=float(delay),
                    earlier_rms_m=float(np.sqrt(np.mean(np.sum(left**2, axis=1)))),
                    later_rms_m=float(np.sqrt(np.mean(np.sum(right**2, axis=1)))))

    reserve()
    baseline = score(np.zeros(2), 0.)
    reserve()
    offset = score(y.mean(axis=0), 0.)
    reserve()
    energy = np.sum(v*v)
    if not energy > 0.:
        raise ValueError('positive earlier receiver speed is required')
    delay = score(np.zeros(2), np.sum(y*v)/energy)
    reserve()
    vc = v-v.mean(axis=0)
    varied = np.sum(vc*vc)
    ratio = float(np.sqrt(varied/energy))
    combined = None
    if ratio > np.finfo(float).eps:
        tau = np.sum(vc*(y-y.mean(axis=0)))/varied
        combined = score((y-tau*v).mean(axis=0), tau)
    return dict(unadjusted=baseline, fixed_offset=offset, delay_only=delay, constant_and_delay=combined,
                centered_velocity_fraction=ratio)


def qualification(root, *, check=False):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the fixed receiver offset comparison')
    sources = qualification(root, check=True)
    raw = (root/parent.RESULT).read_bytes()
    if digest(raw) != PARENT_SHA:
        raise ValueError('the sealed RF04 motion summary is required')
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as study:
        if (study.completion != json.loads(raw)['completion'] or not study.summary['passed']
                or study.envelope(parent.TASK['identity'])['charged'] != parent.TASK['limits']):
            raise ValueError('the completed finite RF04 motion comparison is required')
        material = {key: study.input(key, raw=True) for key in ('layout', 'rf04', 'recovery_policy')}
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(plan=PLAN, parent=parent.RESULT, qualification=REQUEST, tests=XML)
    for name, value in dict(material, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        files[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=files,
                      sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {key: val for key, val in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed RF04 receiver offset comparison is required')

    def reserve():
        context.charge(bound_calls=1, bound_steps=parent.EPOCHS)

    reserve()
    segment = json.loads(context.input_path('layout').read_bytes())['segment']
    nc = json.loads(context.input_path('rf04').read_bytes())['rows']
    ap = segment['receiver_fixes']
    times = np.array([row['time_s'] for row in ap])-segment['start_s']
    if not np.array_equal(times, np.arange(parent.EPOCHS)) or len(nc) != parent.EPOCHS:
        raise ValueError('both original UTC series must cover all common seconds')
    ncar = np.deg2rad([[row['GGLAT'], row['GGLON']] for row in nc])
    applanix = np.array([[row['latitude_rad'], row['longitude_rad']] for row in ap])
    metric = 6_371_000*np.array([1., np.cos(ncar[0, 0])])
    track = (ncar-ncar[0])*metric
    delta = (applanix-ncar)*metric
    velocity = np.zeros_like(track)
    velocity[1:-1] = (track[2:]-track[:-2])/2.
    earlier, later = split_indices(len(track))
    used = np.r_[earlier, later]
    v = velocity[used]
    speed = np.linalg.norm(v, axis=1)
    direction = v/speed[:, None]
    along = np.sum(delta[used]*direction, axis=1)
    right = np.sum(delta[used]*np.column_stack((-direction[:, 1], direction[:, 0])), axis=1)
    course = np.rad2deg(np.arctan2(v[:, 1], v[:, 0])) % 360
    models = compare_models(velocity, delta, earlier, later, reserve=reserve)
    context.save('signed-receiver-offsets.json', [dict(second=int(i), along_m=float(a), right_m=float(b))
                                                 for i, a, b in zip(used, along, right, strict=True)])

    def signed_summary(values):
        return dict(parent._stats(np.abs(values)), signed_median=float(np.median(values)))

    return dict(passed=True, scientific_decision='abstain', earlier_seconds=len(earlier), later_seconds=len(later),
                along_track_m=signed_summary(along), right_track_m=signed_summary(right), models=models,
                speed_mps=[float(speed.min()), float(speed.max())], course_deg=[float(course.min()), float(course.max())],
                asserted_clock_offset=False, new_fits=0, original_imu_reads=0, reserved_reads=0)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete finite receiver comparison required')
        value = dict(env['result'], completion=study.completion, charged=env['charged'])
    _write_equal(root/RESULT, encoded(value))
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
