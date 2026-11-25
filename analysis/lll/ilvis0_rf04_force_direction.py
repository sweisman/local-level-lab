# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check saved force-only trajectories against the separate RF04 attitude record."""

import argparse
from contextlib import closing
from itertools import combinations
import json
from pathlib import Path

from . import ilvis0_recorded_motion_rate as prior
from . import ilvis0_rf04_motion_match as motion
from . import ilvis0_rf04_receiver_offset as offset
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'ilvis0-rf04-force-direction-v1'
SCOPE = 'RF04 attitude-conditioned comparison of saved gyro-free force directions'
PLAN = motion.FOLDER + 'RF04_FORCE_DIRECTION_PLAN.md'
RESULT = motion.FOLDER + 'rf04-force-direction-result.json'
TEST = 'analysis/tests/test_ilvis0_rf04_force_direction.py'
TESTS = ('test_rf04_force_uses_local_to_aircraft_inverse',
         'test_rf04_force_near_seconds_excludes_unmatched_times_without_interpolation')
REQUEST, XML = (f'data/{ID}-inputs/{name}' for name in ('qualification.json', 'tests.xml'))
HASHES = dict(motion=offset.PARENT_SHA,
              freeze='af3bf4864f9ca9f54da89e24a159a316ca48a842371962c21fcdc147b5a2233e',
              recorded='af3eff4157b9c70431c3ac409e93f208999ff96ae0c5fdaf4d0ec948da860072')
START = 302740.
MATCH_S = .005
FORCE_POINTS = 15_856
TASK = dict(identity='rf04-force-direction', input_key='rf04', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=41, bound_steps=FORCE_POINTS+40*motion.EPOCHS))


def body_prediction(attitude, local_force):
    return attitude.inv().apply(local_force)


def near_seconds(utc_week_s):
    import numpy as np

    relative = np.asarray(utc_week_s)-START
    seconds = np.rint(relative).astype(int)
    valid = ((seconds >= 0) & (seconds < motion.EPOCHS) & (abs(relative-seconds) <= MATCH_S+1e-9))
    return seconds, valid


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
        raise ValueError('preserve the fixed RF04 force direction check')
    sources = qualification(root, check=True)
    parents = dict(motion=motion.RESULT, freeze=prior.FREEZE, recorded=prior.RESULT)
    for name, path in parents.items():
        if digest((root/path).read_bytes()) != HASHES[name]:
            raise ValueError(f'original {name} report is required')
    with closing(ClosedStudy(root, 'data/'+motion.ID)) as study:
        receipt = json.loads((root/motion.RESULT).read_bytes())
        if (study.completion != receipt['completion'] or not study.summary['passed']
                or study.envelope(motion.TASK['identity'])['charged'] != motion.TASK['limits']):
            raise ValueError('complete original RF04 comparison required')
        material = {key: study.input(key, raw=True) for key in ('rf04', 'recovery_policy')}
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    files = dict(plan=PLAN, qualification=REQUEST, tests=XML, **parents)
    for name, value in dict(material, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, value)
        files[name] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=files,
                      sources=sources, tasks=[TASK], workers=1, threads=1, maximum_wall_s=90)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from scipy.spatial.transform import Rotation

    from .esa_gyro_force_direction import angles
    from .force_direction_alignment import aligned_direction_scores, unit_vectors
    from .ilvis0_paired_gyro_intervals import force_histories

    declared = {key: val for key, val in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('the fixed RF04 force check is required')

    def reserve():
        context.charge(bound_calls=1, bound_steps=motion.EPOCHS)

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    source = read('rf04')
    if (source['attitude_epochs'] != motion.EPOCHS or len(source['rows']) != motion.EPOCHS
            or source['sha256'] != read('motion')['rf04_sha256']):
        raise ValueError('unchanged RF04 attitude and receiver times required')
    attitude = Rotation.from_euler('ZYX', [[row[key] for key in reversed(motion.ATTITUDE)]
                                           for row in source['rows']], degrees=True)
    context.charge(bound_calls=1, bound_steps=FORCE_POINTS)
    origin, histories = force_histories(context.root.parents[1], read('freeze'), read('recorded'), motion.SEGMENT)
    tracks, clocks = prior.paths.TRACKS, prior.paths.SUPPORT.CLOCKS
    models = prior.paths.average.MATCHED_MODELS
    scores, pairs = [], []
    for track in tracks:
        for clock in clocks:
            predictions = {}
            expected_seconds = None
            for model in models:
                reserve()
                inputs = [histories[motion.SEGMENT, side, track, clock, model] for side in ('training', 'later')]
                seconds_matched, residuals, measured = [], [], []
                for rows in inputs:
                    times, counts, forces, _ = zip(*rows, strict=True)
                    absolute = origin+np.asarray(times)
                    seconds, valid = near_seconds(absolute)
                    ids = seconds[valid]
                    if len(ids) < 2 or np.any(np.diff(ids) <= 0):
                        raise ValueError('ordered near-integer observations are required on both sides of the split')
                    seconds_matched.append(ids.tolist())
                    residuals.append(body_prediction(attitude[ids], np.asarray(forces)[valid]))
                    measured.append(np.asarray(counts)[valid])
                early, later = seconds_matched
                if early[-1] >= later[0] or (expected_seconds is not None and expected_seconds != seconds_matched):
                    raise ValueError('matched disjoint RF04 observations are required across candidates')
                expected_seconds = seconds_matched
                predicted = unit_vectors(np.concatenate(residuals))
                fitted = aligned_direction_scores(predicted, np.concatenate(measured), training=len(early))
                aligned = None
                if fitted['status'] == 'scored':
                    aligned = predicted[len(early):] @ np.array(fitted['rotation_reference_to_measured']).T
                predictions[model] = predicted[len(early):], aligned
                scores.append(dict(track=track, clock=clock, model=model, earlier=len(early), later=len(later),
                                   **{key: value for key, value in fitted.items() if key != 'angular_errors_deg'}))
            for m0, m1 in combinations(models, 2):
                reserve()
                a, aa = predictions[m0]
                b, bb = predictions[m1]
                pairs.append(dict(track=track, clock=clock, models=[m0, m1],
                                  nominal_deg=motion._stats(np.rad2deg(angles(a, b))),
                                  aligned_deg=None if aa is None or bb is None else
                                  motion._stats(np.rad2deg(angles(aa, bb)))))
    return dict(passed=True, scientific_decision='abstain', attitude_source='RF04 fused navigation',
                scores=scores, comparisons=pairs, new_fits=0, original_imu_reads=0, reserved_reads=0,
                absolute_model_error_bound_established=False)


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        env = study.envelope(TASK['identity'])
        if env['charged'] != TASK['limits'] or not env['result']['passed']:
            raise ValueError('complete finite RF04 force check required')
        value = dict(env['result'], completion=study.completion, charged=env['charged'])
    _write_equal(root/RESULT, encoded(value))
    return dict(comparisons=len(value['comparisons']), scores=len(value['scores']), charged=value['charged'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = {'request': qualification, 'prepare': prepare, 'report': report}[parser.parse_args().action]
    print(json.dumps(action(Path.cwd()), sort_keys=True))
