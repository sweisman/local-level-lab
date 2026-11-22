# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify matched full error operators and condition the three ESA tangents."""

import argparse
from contextlib import closing
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ID = 'esa-conditioned-tangent-v1-20261118'
ADAPTER = 'analysis/lll/esa_conditioned_tangent.py'
PLAN = 'docs/prediction-observed-development/ESA_CONDITIONED_TANGENT_PLAN.md'
REPORT = 'docs/prediction-observed-development/esa-conditioned-calibration-contrast.json'
SCOPE = 'three fixed receiver-conditioned calibration tangents on sealed ESA 400/120 predictions'
SOURCE = 'data/esa-calibration-contrast-v1-20261118'
SOURCE_SHA = 'b6090b845e20a82e617e05e4f00e97c342729dcecd2150a7ce4bd56e40bbb3ef'
TRAIN, FORECAST, PACKETS = 400, 120, 155868
CALLS = PACKETS+TRAIN+FORECAST
STORAGE = 64*1024**2
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
SHARED = ('interval', 'training', 'forecast_times', 'recipe', 'environment', 'parent', 'frozen_python_native')
FIELDS = ('fit', 'forecast', 'training_observations', 'weights', 'weights-receipt',
          'earlier_operator', 'noise_compilation', 'tangent')
COMPANIONS = tuple('analysis/lll/'+name+'.py' for name in
                   ('esa_original_whitening', 'innovations_snapshot', 'conditioned_calibration'))


def tasks():
    return [dict(identity=model, input_key='interval', native_kind='tangent',
                 payload=dict(model=model),
                 limits=dict(native_calls=CALLS, packet_visits=CALLS, bound_calls=0, bound_steps=0))
            for model in MODELS]


def key(model, field):
    return model+'-'+field


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_original_whitening import ID as WHITENING, QUAL
    from .esa_calibration_contrast import WEIGHTS_SHA
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the already frozen conditioning study')
    checked(root, QUAL+'/request.json', sources=qualification_sources(root),
            environment=runtime_environment(), required_tests=REQUIRED_TESTS,
            minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, SOURCE)) as source, closing(ClosedStudy(
            root, 'data/'+WHITENING, store=source.store)) as weight:
        if (source.completion['manifest_sha256'] != SOURCE_SHA
                or weight.completion['manifest_sha256'] != WEIGHTS_SHA
                or any(not study.rows[m]['passed'] for study in (source, weight) for m in MODELS)
                or source.input('environment') != require_guarded_environment(environment())):
            raise ValueError('exact archived forecast tangents, weights and environment required')
        materials = {field: source.input(field, raw=True) for field in SHARED}
        for model in MODELS:
            for name in FIELDS[:-3]:
                materials[key(model, name)] = source.input(key(model, name), raw=True)
            for name in ('earlier_operator', 'noise_compilation'):
                materials[key(model, name)] = weight.input(key(model, name), raw=True)
            tangent = (source.input('specified-tangent', raw=True) if model == MODELS[0] else
                       source.artifact(model, 'full-tangent.json', raw=True))
            if json.loads(tangent)['source_forecast_sha256'] != digest(materials[key(model, 'forecast')]):
                raise ValueError('tangent and archived predictions differ')
            materials[key(model, 'tangent')] = tangent
    inputs = {}
    for field, payload in materials.items():
        path = base/field
        atomic(path, payload)
        inputs[field] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(), inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN, *COMPANIONS]),
                      workers=3, threads=1, maximum_wall_s=480.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(task, context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import frozen_workspace
    from .innovations_snapshot import restore
    from .studies.artifacts import digest

    model = task['identity']
    body = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or body != next((row for row in tasks() if row['identity'] == model), None)
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('exact frozen forecast conditioning task required')
    files = {name: str(context.input_path(name).resolve()) for name in SHARED}
    files.update({name: str(context.input_path(key(model, name)).resolve()) for name in FIELDS})
    with frozen_workspace(context, COMPANIONS) as work:
        with context.prepay_native(native_calls=CALLS, packet_visits=CALLS):
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '_frozen',
                            model, json.dumps(files), str(work)], cwd=work,
                           env={**os.environ, 'PYTHONPATH': str(work/'analysis')}, check=True)
        report = json.loads((work/'conditioned-tangent.json').read_bytes())
        snapshot = (work/'full-factors.npz').read_bytes()
    if report['model'] != model or digest(snapshot) != report['snapshot_sha256']:
        raise ValueError('sealed conditioned output must match candidate and full factors')
    restore(snapshot, expected_sha256=report['snapshot_sha256'],
            expected_configuration=report['operator_configuration'], maximum_bytes=STORAGE)
    context.save_bytes('full-factors.npz', snapshot)
    context.save('conditioned-tangent.json', report)
    return dict(passed=True, model=model, fit_starts=0,
                later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')


def frozen_replay(model, inputs, work):
    import numpy as np
    from dataclasses import replace
    from lll.airquantumgrav_error_policy import build
    from lll.airquantumgrav_noisy_inputs import error_law
    from lll.conditioned_calibration import conditioned_tangent
    from lll.esa_original_whitening import load_original_noise
    from lll.ilvis0_exploratory import ConditionalBounds
    from lll.ilvis0_native_error_training import build_training_operator
    from lll.ilvis0_precision_value import longitude_residual
    from lll.ilvis0_training_forecast import initialize_training
    from lll.innovations_snapshot import capture, restore
    from lll.studies.artifacts import digest, encoded

    deadline = time.monotonic()+420.

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit, forecast, tangent, recipe, earlier, older, receipt = (read(name) for name in
        ('fit', 'forecast', 'tangent', 'recipe', 'training_observations', 'earlier_operator', 'weights-receipt'))
    rows = json.loads(gzip.decompress(Path(inputs['training']).read_bytes()))
    times = np.asarray(read('forecast_times'))
    coordinates = np.asarray(earlier['coordinates'])
    count = earlier['native_prefix_packets']
    with np.load(inputs['interval'], allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in ('theta', 'dv', 'dt')}
    if (len(rows) != TRAIN or len(times) != TRAIN+FORECAST or len(arrays['dt']) != PACKETS
            or times.tolist() != forecast['times_s'] or times[:TRAIN].tolist() != earlier['times_s']
            or tangent['source_forecast_sha256'] != digest(Path(inputs['forecast']).read_bytes())
            or fit['active_parameters'] != tangent['active_parameters']
            or older['model'] != model or forecast['frozen_error_model'] != model
            or forecast['prediction_receiver_positions_used'] is not False):
        raise ValueError('fixed earlier-only source forecast required')
    prefix = {name: value[:count] for name, value in arrays.items()}
    initial, gravity = initialize_training(times[:TRAIN], coordinates, **prefix, model=model,
        clock=recipe['clock'], maximum_interval_s=recipe['maximum_interval_s'])
    receiver = build(rows, policy_id='reported-short-v1')
    transforms = np.concatenate((receiver.transforms,
                                 np.repeat(receiver.transforms[-1:], FORECAST, axis=0)))
    origin = earlier['time_origin_gps_sow_s']
    if not np.array_equal(receiver.times-origin, times[:TRAIN]):
        raise ValueError('original receiver time origin differs')
    spec = replace(receiver.spec, drift_origin_s=receiver.spec.drift_origin_s-origin)
    pinned = dict(prefix, times=times[:TRAIN], receiver_transforms=transforms[:TRAIN],
        initial_coordinates=[initial[name] for name in ('latitude_rad', 'longitude_rad', 'height_m')],
        initial_velocity=initial['velocity_ned_mps'], initial_rotation=initial['attitude_body_to_ned'])
    if (any(digest(np.asarray(val, dtype='<f8').tobytes()) != older['input_sha256'][name]
            for name, val in pinned.items()) or gravity != older['gravity_mps2']):
        raise ValueError('earlier anchor, receiver transforms or IMU prefix differs')
    noise_kernel, _ = load_original_noise(work, read('noise_compilation'))
    calls = 0

    def reserve(*, native_calls, packet_steps):
        nonlocal calls
        calls += 1
        if native_calls != 1 or packet_steps != 1 or calls > CALLS or time.monotonic() >= deadline:
            raise ValueError('full fixed covariance work allowance exhausted')

    operator, descriptor = build_training_operator(**arrays, times=times, initial=initial,
        bounds=ConditionalBounds(recipe['limits'], fit_earth_removal=True), model=model,
        gravity_mps2=gravity, disc_radius_m=older['disc_radius_m'],
        noise=error_law(recipe['noise_by_law']['increment']), receiver_spec=spec,
        receiver_transforms=transforms, noise_kernel=noise_kernel,
        gravity_anchor_height_m=float(coordinates[0, 2]), maximum_packets=PACKETS,
        maximum_queries=TRAIN+FORECAST, maximum_bytes=STORAGE,
        anchor_policy=recipe['covariance_anchor_policy'], reserve=reserve)
    original = restore(Path(inputs['weights']).read_bytes(), expected_sha256=receipt['snapshot_sha256'],
                       expected_configuration=older['operator_configuration'], maximum_bytes=STORAGE)
    original_prefix = original.prefix(TRAIN).configuration
    if operator.prefix(TRAIN).configuration != original_prefix:
        raise ValueError('full covariance changed its earlier factors')
    residual = np.asarray(forecast['training_coordinate_difference'])
    residual[:, 1] = longitude_residual(residual[:, 1])
    jacobian = np.asarray(tangent['jacobian'])
    if (not np.array_equal(original.whiten(residual.ravel()), fit['local_linearization']['residual'])
            or not np.allclose(original.whiten(jacobian[:3*TRAIN]), fit['local_linearization']['jacobian'],
                               rtol=1e-10, atol=1e-8)):
        raise ValueError('original residual or derivatives do not match sealed training quantities')
    full = conditioned_tangent(operator, np.asarray(forecast['coordinates']).ravel(),
                               jacobian, residual.ravel(), training_epochs=TRAIN)
    snapshot = capture(operator)
    (work/'full-factors.npz').write_bytes(snapshot)
    (work/'conditioned-tangent.json').write_bytes(encoded(dict(model=model, times_s=times[-FORECAST:].tolist(),
        conditioned_mean=full['mean'].reshape(-1, 3).tolist(), conditioned_jacobian=full['design'].tolist(),
        raw_jacobian_sha256=digest(Path(inputs['tangent']).read_bytes()),
        receiver_adjustment=full['receiver_adjustment'].reshape(-1, 3).tolist(),
        prefix_configuration=original_prefix, operator_configuration=operator.configuration,
        descriptor=descriptor, snapshot_sha256=digest(snapshot), actual_noise_calls=calls,
        fit_starts=0, later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')))


def summarize(root):
    import numpy as np
    from .calibration_loss_support import support
    from .esa_calibration_contrast import BUDGETS, RADIUS
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_precision_value import longitude_residual
    from .ilvis0_solver_position import physical_metric
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (study.completion['state'] != 'complete' or set(study.tasks) != set(MODELS)
                or not all(study.rows[model]['passed'] for model in MODELS)
                or study.manifest['sources'][ADAPTER] != digest((root/ADAPTER).read_bytes())):
            raise ValueError('complete frozen earlier-only three-model result required')
        paths = {model: study.artifact(model, 'conditioned-tangent.json') for model in MODELS}
        fits = {model: study.input(key(model, 'fit')) for model in MODELS}
        if any(p['later_receiver_positions_read'] != 0 or p['protected_reads'] != 0
               or p['times_s'] != paths[MODELS[0]]['times_s'] for p in paths.values()):
            raise ValueError('common sealed later queries and earlier-only predictions required')
        nominal = {model: np.asarray(p['conditioned_mean']) for model,p in paths.items()}
        metric = physical_metric(nominal[MODELS[0]]).ravel()
        details = []
        for first, second in ((MODELS[0], MODELS[1]), (MODELS[0], MODELS[2]), (MODELS[1], MODELS[2])):
            path_delta = nominal[second]-nominal[first]
            path_delta[:, 1] = longitude_residual(path_delta[:, 1])
            direction = path_delta.ravel()*metric
            distance = float(np.linalg.norm(direction))
            vector = direction/(distance*np.sqrt(FORECAST))
            for limit in BUDGETS:
                bounds = {}
                for model, sign in ((first, 1), (second, -1)):
                    fit = fits[model]
                    location = np.asarray(fit['normalized_parameters'])
                    local = fit['local_linearization']
                    loading = (sign*vector*metric) @ np.asarray(paths[model]['conditioned_jacobian'])
                    bounds[model] = support(local['jacobian'], local['residual'], loading,
                        np.maximum(-RADIUS, -1-location), np.minimum(RADIUS, 1-location), budget=limit)
                closure = sum(arm['upper_bound'] for arm in bounds.values())
                nominal_rms = distance/np.sqrt(FORECAST)
                details.append(dict(pair=[first,second], allowance=limit, separation_rms_m=nominal_rms,
                    closure_upper_m=closure, separation_along_nominal_axis_lower_m=max(0.,nominal_rms-closure),
                    per_candidate=bounds))
        result = dict(study='data/'+ID, manifest_sha256=study.completion['manifest_sha256'],
            cases=details, native_calls=0, fit_starts=0, later_receiver_positions_read=0,
            protected_reads=0, linearized=True, scientific_decision='abstain')
    _write_equal(root/REPORT, encoded(result))
    return dict(report=REPORT, comparisons=len(details), sha256=digest(encoded(result)))


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '_frozen':
        frozen_replay(sys.argv[2], json.loads(sys.argv[3]), Path(sys.argv[4]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare', 'summarize'))
        operation = prepare if parser.parse_args().action == 'prepare' else summarize
        print(json.dumps(operation(Path.cwd()), sort_keys=True))
