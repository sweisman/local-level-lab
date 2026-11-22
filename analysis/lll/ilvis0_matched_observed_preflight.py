# SPDX-License-Identifier: AGPL-3.0-or-later
"""Counted recorded-input check for matched wider-arithmetic forecasts."""

import argparse
from contextlib import closing
import gzip
import io
import json
from pathlib import Path

import numpy as np

from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_generated import RECOVERY, REQUIRED as GENERATED_TESTS
from .ilvis0_matched_observed_inputs import FOLDER, FREEZE, MAX_INTERVAL, RECEIPT, TRACKS
from .ilvis0_matched_training import MATCHED_MODELS
from .ilvis0_matched_wide import ID as WIDE_ID, TESTS as WIDE_TESTS
from .studies.artifacts import atomic, digest, encoded, safe_path


ID = 'ilvis0-matched-observed-preflight-v1-20261118'
ADAPTER = 'analysis/lll/ilvis0_matched_observed_preflight.py'
PLAN = FOLDER+'MATCHED_OBSERVED_NUMERICAL_PLAN.md'
REQUEST = FOLDER+'matched-observed-preflight-qualification-v2.json'
REPORT = FOLDER+'matched-observed-preflight-tests-v2.xml'
GENERATED_GATE = FOLDER+'matched-wide-report.json'
CLOCK = 'nominal_200Hz'
EVALUATIONS = 30
WALL_S = 1800.
SCOPE = 'matched four-model recorded aircraft software preflight; development only'
REQUIRED_TESTS = (*GENERATED_TESTS, *WIDE_TESTS,
                  'test_clock_checks_use_a_distinct_prefix_for_each_period',
                  'test_short_elapsed_clock_or_changed_original_counts_fail_preflight',
                  'test_preflight_assigns_each_model_the_same_recording_allowance')


def recipe():
    return dict(id=ID, clock=CLOCK, gyro_offset_dph=1., profile=False,
                arithmetic='wide', weighting='h1_v3_tau60', independent_neu_m=[.3, .3, .7],
                maximum_evaluations=EVALUATIONS, maximum_interval_s=MAX_INTERVAL,
                maximum_prefix_difference_m=1e-8)


def tasks(cases):
    rows = []
    for case in cases:
        segment = case['segment_id']
        packets = case['clocks'][CLOCK]
        cut, later = case['training_epochs'], case['scoring_epochs']
        for model in MATCHED_MODELS:
            rows.append(dict(identity=segment+'-'+model, input_key=segment+'-packets',
                segment_id=segment, model=model, training_epochs=cut, scoring_epochs=later,
                training_packets=packets['training_packets'], full_packets=packets['forecast_packets'],
                limits=dict(native_calls=EVALUATIONS+1, bound_calls=0, bound_steps=0,
                            packet_visits=EVALUATIONS*packets['training_packets']*cut
                                + packets['forecast_packets']*(cut+later))))
    return rows


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (ADAPTER, PLAN, 'analysis/lll/ilvis0_native.c',
        'analysis/lll/ilvis0_tangent.cpp', 'analysis/tests/test_ilvis0_matched_training.py',
        'analysis/tests/test_ilvis0_matched_generated.py',
        'analysis/tests/test_ilvis0_matched_gyro_free.py',
        'analysis/tests/test_ilvis0_matched_wide.py', 'analysis/tests/test_ilvis0_matched_precision.py',
        'analysis/tests/test_ilvis0_matched_observed_inputs.py',
        'analysis/tests/test_ilvis0_matched_observed_preflight.py'))


def request(root):
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=REPORT)


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS as RECOVERY_TESTS, qualification_sources

    root = Path(root).resolve()
    if (root/'data'/ID).exists():
        raise ValueError('existing case allowances must be retained')
    environment = runtime_environment()
    source_paths = sources(root)
    qualification, tests = checked(root, REQUEST, sources=source_paths,
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=RECOVERY_TESTS, minimum_tests=len(RECOVERY_TESTS))
    wide = json.loads((root/GENERATED_GATE).read_bytes())
    with closing(ClosedStudy(root, 'data/'+WIDE_ID)) as parent:
        completion = parent.completion
        if (wide['qualified'] is not True
                or wide['manifest_sha256'] != completion['manifest_sha256']
                or wide['summary_sha256'] != completion['summary_sha256']):
            raise ValueError('generated wider-arithmetic gate required')
    receipt = json.loads((root/RECEIPT).read_bytes())
    if (receipt['freeze_sha256'] != digest((root/FREEZE).read_bytes())
            or receipt['imu_fit_starts'] != 0 or len(receipt['recordings']) != 2):
        raise ValueError('two prepared recorded inputs required')
    inputs = dict(input_receipt=RECEIPT, input_freeze=FREEZE, generated_gate=GENERATED_GATE)
    aliases = {'packets.npy.gz': 'packets', 'training.json': 'training',
               'scoring.json': 'scoring', 'queries.json': 'queries',
               'packet-provenance.json': 'provenance'}
    for case in receipt['recordings']:
        for name, alias in aliases.items():
            artifact = case['artifacts'][name]
            if digest(safe_path(root, artifact['path']).read_bytes()) != artifact['sha256']:
                raise ValueError('prepared recorded artifact changed: '+name)
            inputs[case['segment_id']+'-'+alias] = artifact['path']
    inputs_dir = root/'data'/(ID+'-inputs')
    inputs_dir.mkdir(parents=True, exist_ok=True)
    materials = dict(recipe=encoded(recipe()), qualification=qualification, qualification_tests=tests,
                     recovery=recovery, recovery_tests=recovery_tests)
    for key, raw in materials.items():
        path = inputs_dir/key
        if path.is_file() and path.read_bytes() != raw:
            raise ValueError('prepared numerical preflight materials changed')
        if not path.is_file():
            atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    data = dict(id=ID, scope=SCOPE, adapter=ADAPTER, sources=source_paths, inputs=inputs,
        tasks=tasks(receipt['recordings']), workers=4, threads=1, maximum_wall_s=WALL_S)
    manifest = Definition.from_dict(data, root).prepare(root)
    return dict(study=ID, limits=manifest['limits'], allocation=manifest['allocation'])


def _json(context, key):
    return json.loads(context.input_path(key).read_bytes())


def load_training(task, context):
    """Rebuild the declared training problem without opening later positions."""
    from .ilvis0_exploratory import load_kernel
    from .ilvis0_gps_sensitivity import assumptions, coordinate_covariance
    from .ilvis0_matched_training import matched_limits, matched_training_problem
    from .ilvis0_shape import load_tangent

    settings = _json(context, 'recipe')
    if settings != recipe():
        raise ValueError('unchanged matched recorded preflight required')
    segment = task['segment_id']
    queries = _json(context, segment+'-queries')
    training = _json(context, segment+'-training')
    values = np.load(io.BytesIO(gzip.decompress(context.input_path().read_bytes())), allow_pickle=False)
    times = np.asarray(queries['query_times_s'], float)
    cut, prefix = task['training_epochs'], task['training_packets']
    gps = np.asarray(training['coordinates']['onboard'], float)
    if (queries['segment_id'] != segment or queries['training_epochs'] != cut
            or queries['clocks'][CLOCK]['training_packets'] != prefix
            or values.shape != (task['full_packets'], 15) or times.shape != (cut+task['scoring_epochs'],)
            or not np.array_equal(times[:cut], training['query_times_s']) or gps.shape != (cut, 3)):
        raise ValueError('changed training shape, timestamps or packet prefix')
    covariance_law = next(item for item in assumptions() if item.name == settings['weighting'])
    blocks = np.tile(np.diag(np.square(settings['independent_neu_m'])), (cut, 1, 1))
    covariance = coordinate_covariance(times[:cut], gps[:, 0], gps[:, 2], blocks, covariance_law)
    theta, dv, dt = values[:, 9:12], values[:, 12:15], np.full(len(values), .005)
    directory = context.root/'shards'/f'{context.shard:03d}'/'matched-observed-kernels'
    kernel, value = load_kernel(directory)
    tangent, ordinary = load_tangent(directory)
    frozen = context.manifest['sources']
    expected_cpp = frozen['analysis/lll/ilvis0_tangent.cpp']
    if (value['source_sha256'] != frozen['analysis/lll/ilvis0_native.c']
            or ordinary['source_sha256'] != expected_cpp):
        raise ValueError('compiled native source differs from freeze')
    problem = matched_training_problem(times[:cut], gps, theta=theta[:prefix], dv=dv[:prefix],
        dt=dt[:prefix], covariance=covariance, model=task['model'],
        limits=matched_limits(settings['gyro_offset_dph']), profile=settings['profile'],
        clock=CLOCK, maximum_interval_s=MAX_INTERVAL, kernel=kernel,
        tangent_kernel=tangent)
    return problem, directory, dict(theta=theta, dv=dv, dt=dt, times=times), dict(value=value, tangent=ordinary)


def evaluate(task, context):
    if context.manifest['scope'] != SCOPE:
        raise ValueError('unchanged matched recorded preflight required')
    return evaluate_recorded(task, context)


def evaluate_recorded(task, context, *, require_converged=False):
    """Run the same split, four-model arithmetic and score for a verified input."""
    from .ilvis0_forecast import native_forecast
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_training_forecast import fit_training
    from .ilvis0_wide_tangent import load as load_wide, problem as wider

    cut, later = task['training_epochs'], task['scoring_epochs']
    expected_work = dict(native_calls=EVALUATIONS+1, bound_calls=0, bound_steps=0,
                         packet_visits=EVALUATIONS*task['training_packets']*cut
                             + task['full_packets']*(cut+later))
    if task['limits'] != expected_work:
        raise ValueError('changed matched evaluation allowance')
    problem, directory, motion, compilation = load_training(task, context)
    precise, wide = load_wide(directory,
        expected_source_sha256=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp'])
    context.save('compilation.json', dict(compilation, wide=wide))
    model, segment = task['model'], task['segment_id']
    times, gps = motion['times'], problem.gps
    problem = wider(problem, kernel=precise)
    fit = fit_training(problem, model, start=np.zeros(len(problem.bounds.active)),
                       maximum_evaluations=EVALUATIONS, reserve=context.charge)
    context.save('fit.json', fit)
    if require_converged and not fit['converged']:
        return dict(passed=False, segment_id=segment, model=model, converged=False,
                    training_evaluations=fit['evaluations'], stopping_probe=fit['stability_probe'],
                    observed_fit_starts=1, confidence_calibrated=False, scientific_decision='abstain')
    forecast = native_forecast(problem, fit['normalized_parameters'], model,
        **motion, maximum_interval_s=MAX_INTERVAL, reserve=context.charge,
        retain_training_difference=True)
    coordinates = forecast['coordinates']
    difference = forecast['training_coordinate_difference']
    context.save('forecast.json', dict(coordinates=coordinates.tolist(), query_times_s=times.tolist(),
        training_epochs=cut, later_positions_used=False,
        training_coordinate_difference=difference.tolist()))
    scoring = _json(context, segment+'-scoring')
    if not np.array_equal(times[cut:], scoring['query_times_s']) or set(scoring['coordinates']) != set(TRACKS):
        raise ValueError('scoring receiver epochs differ from completed forecast')
    rms = {}
    for track in TRACKS:
        later = np.asarray(scoring['coordinates'][track], float)
        if later.shape != coordinates[cut:].shape or not np.isfinite(later).all():
            raise ValueError('scoring track must cover all later epochs')
        error = (coordinates[cut:]-later)*physical_metric(later)
        rms[track] = dict(horizontal_rms_m=float(np.sqrt(np.mean(np.sum(error[:, :2]**2, axis=1)))),
                          height_rms_m=float(np.sqrt(np.mean(error[:, 2]**2))))
    previous = problem.cholesky@np.asarray(fit['local_linearization']['residual'])
    prefix_error = float(np.linalg.norm((difference-previous.reshape((cut, 3)))*physical_metric(gps),
                                        axis=1).max())
    result = dict(passed=prefix_error <= recipe()['maximum_prefix_difference_m'],
        segment_id=segment, model=model, converged=fit['converged'],
        training_evaluations=fit['evaluations'], prefix_difference_m=prefix_error,
        heldout_rms_by_gps_stream=rms, forecast_saved_before_scoring=True,
        observed_fit_starts=1, confidence_calibrated=False, scientific_decision='abstain')
    context.save('scores.json', result)
    return result


if __name__ == '__main__':
    from .ilvis0_control_shards import launch
    from .studies.validation_resume import _other_threads

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'run'))
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'request':
        result = request(root)
    elif args.action == 'prepare':
        result = prepare(root)
    else:
        outcome = launch(root/'data'/ID, reserved_threads=_other_threads(root, 4))
        result = {key: outcome[key] for key in ('state', 'completed', 'total', 'passed', 'charged')}
    print(json.dumps(result, sort_keys=True))
