# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rebuild and preserve the original ESA training weights for exact ray scoring."""

import argparse
from contextlib import closing
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ID = 'esa-original-whitening-v1-20261118'
ADAPTER = 'analysis/lll/esa_original_whitening.py'
PLAN = 'docs/prediction-observed-development/ESA_ORIGINAL_WHITENING_PLAN.md'
SCOPE = 'three original earlier whitening operators and exact scores for six earlier-cost steps'
PARENT = 'data/esa-earlier-fit-cost-v1-20261118'
PARENT_SHA = '3d76596ba7b4aee7389f613182b5556a4bd0abc600b9c79b8b644fe0b57112ea'
PREFIX_PACKETS = 119868
TRAIN, FORECAST, PACKETS = 400, 120, 155868
NOISE_CALLS = PREFIX_PACKETS+TRAIN
SCALAR_CALLS = 3
CALLS = NOISE_CALLS+SCALAR_CALLS
VISITS = NOISE_CALLS+SCALAR_CALLS*PACKETS*(TRAIN+FORECAST)
MAX_STORAGE = 64*1024**2
COMPANIONS = ('analysis/lll/esa_tangent_remainder.py', 'analysis/lll/innovations_snapshot.py')
RECOVERY = 'data/'+ID+'-recovery'
QUAL = 'data/'+ID+'-qualification'


def recovery_request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request
    from .studies.task_resume import qualification_sources

    return request(root, sources=qualification_sources(root), environment=runtime_environment(),
                   output=QUAL+'/request.json', report=QUAL+'/tests.xml')


def score_change(residual, change):
    """Evaluate the squared-loss difference without subtracting two large costs."""
    import numpy as np
    residual, change = np.asarray(residual, float), np.asarray(change, float)
    if (residual.ndim != 1 or residual.shape != change.shape
            or not np.all(np.isfinite(residual)) or not np.all(np.isfinite(change))):
        raise ValueError('finite aligned whitened residual and change required')
    return float((2*residual+change)@change)


def tasks():
    from .esa_earlier_fit_cost import MODELS
    return [dict(identity=model, input_key='interval', native_kind='mixed',
                 payload=dict(model=model),
                 limits=dict(native_calls=CALLS, packet_visits=VISITS, bound_calls=0, bound_steps=0))
            for model in MODELS]


def stage_points(parent, model):
    import numpy as np
    from .esa_earlier_fit_cost import BUDGETS, key, loss_limited_step

    fit = parent.input(key(model, 'fit'))
    ray = np.asarray(parent.input(key(model, 'ray')))
    fit_point = np.asarray(fit['normalized_parameters'])
    local = fit['local_linearization']
    previous = parent.artifact(model, 'earlier-cost.json')['comparisons']
    result = []
    for cap, archived in zip(BUDGETS, previous, strict=True):
        scale, affine, capped = loss_limited_step(local['residual'], local['jacobian'], ray, limit=cap)
        delta = scale*ray
        point = fit_point+delta
        if (archived['budget'] != cap or archived['cap_limited'] is not capped
                or not np.isclose(affine, archived['affine_loss_increase'], rtol=1e-10, atol=1e-14)
                or not np.isclose(np.linalg.norm(delta), archived['parameter_norm'], rtol=1e-10)
                or np.any(np.abs(point)>1)):
            raise ValueError('exact two declared prior comparison points required')
        result.append(dict(point=point.tolist(), affine_increase=affine, budget=cap,
                           cap_limited=capped, white_bracket=archived['scalar_loss_increase_bracket']))
    return result


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .esa_earlier_fit_cost import CANDIDATE, MODELS, SHARED, key
    from .esa_native_tangent_replay import AUTHORITATIVE, PARENT_SHA as MATRIX_SHA
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources
    from .ilvis0_control_shards import runtime_environment

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing study and its saved continuation')
    checked(root, QUAL+'/request.json', sources=qualification_sources(root),
            environment=runtime_environment(), required_tests=REQUIRED_TESTS,
            minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, PARENT)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_SHA
                or parent.completion['state'] != 'complete'
                or not all(parent.rows[model]['passed'] for model in MODELS)
                or parent.input('environment') != require_guarded_environment(environment())):
            raise ValueError('the sealed earlier-cost study and pinned environment are required')
        materials = {name: parent.input(name, raw=True) for name in SHARED}
        with closing(ClosedStudy(root, AUTHORITATIVE, store=parent.store)) as source:
            if source.completion['manifest_sha256'] != MATRIX_SHA:
                raise ValueError('original calibration matrix differs')
            for model in MODELS:
                names = [key(model, name) for name in CANDIDATE]
                materials.update({name: parent.input(name, raw=True) for name in names})
                original_id = model+'-1-increment-0'
                compile_receipt = source.artifact(original_id, 'compilation.json')['noise_bridge']
                materials[key(model, 'noise_compilation')] = encoded(compile_receipt)
                materials[key(model, 'points')] = encoded(stage_points(parent, model))
    inputs = {}
    for name, raw in materials.items():
        path = base/name
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=tasks(), inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN, *COMPANIONS]),
                      workers=3, threads=1, maximum_wall_s=420.)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment
    from .esa_earlier_fit_cost import CANDIDATE, SHARED, key
    from .esa_tangent_remainder import frozen_workspace
    from .innovations_snapshot import restore
    from .studies.artifacts import digest

    model = declared['identity']
    task = {name: value for name, value in declared.items() if name not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE
            or task != next((row for row in tasks() if row['identity'] == model), None)
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('exact task and training covariance environment required')
    candidate = (*CANDIDATE, 'noise_compilation', 'points')
    names = (*SHARED, *(key(model, name) for name in candidate))
    with frozen_workspace(context, COMPANIONS) as work:
        inputs = {name: str(context.input_path(name).resolve()) for name in names}
        paths = json.dumps({name: inputs[key(model, name)] for name in candidate} |
                           {name: inputs[name] for name in SHARED})
        # Charge the full noise pass and three scalar evaluations before the
        # isolated process starts. It enforces its own exact counter per packet.
        with context.prepay_native(native_calls=NOISE_CALLS, packet_visits=NOISE_CALLS,
                                   native_kind='tangent'):
            pass
        with context.prepay_native(native_calls=SCALAR_CALLS,
                                   packet_visits=SCALAR_CALLS*PACKETS*(TRAIN+FORECAST),
                                   native_kind='value'):
            subprocess.run([sys.executable, str(Path(__file__).resolve()), '_frozen',
                            model, paths, str(work)],
                           cwd=work, env={**os.environ, 'PYTHONPATH': str(work/'analysis')},
                           check=True)
        result = json.loads((work/'exact-earlier-cost.json').read_bytes())
        snapshot = (work/'training-factors.npz').read_bytes()
    if (result['model'] != model or len(result['comparisons']) != 2
            or result['snapshot_sha256'] != digest(snapshot)):
        raise ValueError('complete exact score and factor capture required')
    restore(snapshot, expected_sha256=result['snapshot_sha256'],
            expected_configuration=result['configuration'], maximum_bytes=MAX_STORAGE)
    context.save_bytes('training-factors.npz', snapshot)
    context.save('exact-earlier-cost.json', result)
    return dict(passed=True, snapshot_sha256=result['snapshot_sha256'],
                steps_inside=sum(step['inside'] for step in result['comparisons']),
                new_fits=0, later_receiver_positions_read=0, protected_reads=0,
                scientific_decision='abstain')


def load_original_noise(work, expected_build):
    from lll.ilvis0_noise_step import load

    builds = []

    def reserve_build():
        if builds:
            raise ValueError('only one native noise build is allowed')
        builds.append(True)

    kernel, receipt = load(work/'noise-build', reserve_build=reserve_build,
        expected_source_sha256=expected_build['original_source_sha256'],
        expected_bridge_sha256=expected_build['bridge_source_sha256'],
        expected_wide_loader_sha256=expected_build['wide_loader_source_sha256'])
    matched = ('binary_sha256', 'source_sha256', 'compiler', 'flags', 'internal_mantissa_bits')
    if any(receipt[key] != expected_build[key] for key in matched):
        raise ValueError('original noise bridge compilation differs')
    return kernel, receipt


def frozen_replay(model, inputs, work):
    import numpy as np
    from lll.airquantumgrav_error_policy import build
    from lll.airquantumgrav_noisy_inputs import error_law
    from lll.esa_tangent_remainder import scalar_replay
    from lll.ilvis0_native_error_training import ErrorTrainingFactory
    from lll.ilvis0_precision_value import longitude_residual
    from lll.innovations_snapshot import capture, restore
    from lll.studies.artifacts import digest, encoded

    deadline = time.monotonic()+360.

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    older, recipe, saved, earlier = (read(name) for name in
                   ('earlier_operator', 'recipe', 'forecast', 'training_observations'))
    rows = json.loads(gzip.decompress(Path(inputs['training']).read_bytes()))
    count = earlier['native_prefix_packets']
    if count != PREFIX_PACKETS or len(rows) != TRAIN:
        raise ValueError('exact original earlier covariance support required')
    with np.load(inputs['interval'], allow_pickle=False) as archive:
        arrays = {key: archive[key][:count] for key in ('theta','dv','dt')}
    noise_kernel, _ = load_original_noise(work, read('noise_compilation'))

    calls = 0

    def reserve(*, native_calls, packet_visits):
        nonlocal calls
        calls += 1
        if native_calls != 1 or packet_visits != 1 or calls > NOISE_CALLS or time.monotonic() >= deadline:
            raise ValueError('earlier covariance work allowance exhausted')

    def forbidden_kernel(*args, **kwargs):
        raise ValueError('training optimizer or tangent use is outside the fixed replay')

    coordinates = np.asarray(earlier['coordinates'])
    factory = ErrorTrainingFactory(noise=error_law(recipe['noise_by_law']['increment']),
        noise_kernel=noise_kernel, gravity_anchor_height_m=coordinates[0, 2],
        maximum_packets=PACKETS, maximum_queries=TRAIN+FORECAST, maximum_bytes=MAX_STORAGE,
        anchor_policy=recipe['covariance_anchor_policy'])
    problem = factory(earlier['times_s'], coordinates, **arrays, model=model,
        limits=recipe['limits'], profile=True, clock=recipe['clock'],
        maximum_interval_s=recipe['maximum_interval_s'], kernel=forbidden_kernel,
        tangent_kernel=forbidden_kernel, training_weight=build(rows, policy_id='reported-short-v1'),
        time_origin_s=earlier['time_origin_gps_sow_s'], reserve=reserve)
    operator = problem.observation_error
    if problem.error_descriptor != older or operator.configuration != saved['error_training_configuration']:
        raise ValueError('the exact archived earlier covariance was not reproduced')
    residual = np.asarray(read('fit')['local_linearization']['residual'])
    original_cost = float(residual@residual)
    nominal = np.asarray(saved['training_coordinate_difference'])
    nominal[:, 1] = longitude_residual(nominal[:, 1])
    rewhitened = operator.whiten(nominal.ravel())
    if not np.array_equal(residual, rewhitened):
        raise ValueError('reproduced nominal training residual vector differs')
    snapshot = capture(operator)
    sha = digest(snapshot)
    cached = restore(snapshot, expected_sha256=sha, expected_configuration=operator.configuration,
                     maximum_bytes=MAX_STORAGE)
    if not np.array_equal(cached.whiten(nominal.ravel()), rewhitened):
        raise ValueError('restored whitening changed the archived nominal residual')
    _, _, _, _, _, _, displacement = scalar_replay(inputs, work/'exact-earlier-cost.json',
                                                   expected_model=model)
    rounded = np.asarray(saved['coordinates'])[:TRAIN]-coordinates
    rounded[:, 1] = longitude_residual(rounded[:, 1])
    nominal_offset = nominal-rounded
    comparisons = []
    for step in read('points'):
        whitened_change = cached.whiten((displacement(step['point'])[:TRAIN]-nominal_offset).ravel())
        increase = score_change(residual, whitened_change)
        low, high = step['white_bracket']
        if not low-1e-8 <= increase <= high+1e-8:
            raise ValueError('exact score falls outside prior white-floor bound')
        comparisons.append(dict(budget=step['budget'], affine_increase=step['affine_increase'],
             exact_increase=increase, inside=increase<=step['budget'],
             cap_limited=step['cap_limited'], difference=increase-step['affine_increase']))
    (work/'training-factors.npz').write_bytes(snapshot)
    (work/'exact-earlier-cost.json').write_bytes(encoded(dict(model=model,
        snapshot_sha256=sha, configuration=operator.configuration, original_earlier_loss=original_cost,
        comparisons=comparisons, actual_noise_calls=calls, fit_starts=0,
        later_receiver_positions_read=0, protected_reads=0, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 5 and sys.argv[1] == '_frozen':
        frozen_replay(sys.argv[2], json.loads(sys.argv[3]), Path(sys.argv[4]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('qualify-request', 'prepare'))
        action = parser.parse_args().action
        operation = recovery_request if action == 'qualify-request' else prepare
        print(json.dumps(operation(Path.cwd()), sort_keys=True))
