# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure finite forecast departures from a sealed local ESA tangent."""

import argparse
from contextlib import closing, contextmanager
import gzip
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from zipfile import ZipFile


ID = 'esa-tangent-remainder-v1-20261118'
ADAPTER = 'analysis/lll/esa_tangent_remainder.py'
PLAN = 'docs/prediction-observed-development/ESA_TANGENT_REMAINDER_PLAN.md'
SCOPE = 'six feasible finite changes along weak ESA training directions, without a refit'
REPLAY = 'data/esa-native-tangent-replay-v1-20261118'
REPLAY_SHA = '3a294c22063ed997c22a031f7664b67edeb4aa4652b2af7b0c6e0dcb0303441a'
RADII = (.01, .10)
DIRECTIONS = 3
TRAIN, FORECAST, PACKETS = 400, 120, 155868
SWEEPS = 1 + len(RADII)*DIRECTIONS
WALL_S = 120.
KEYS = ('interval', 'training', 'forecast_times', 'recipe', 'fit', 'forecast',
        'training_observations', 'compiler', 'environment', 'parent', 'frozen_python_native',
        'tangent')


def weak_rays(point, whitened_jacobian):
    """Choose the side with more feasible room on each of the weakest rays."""
    import numpy as np

    point, design = np.asarray(point, float), np.asarray(whitened_jacobian, float)
    if (point.ndim != 1 or len(point) < DIRECTIONS or np.any(np.abs(point) > 1)
            or not np.all(np.isfinite(point)) or design.ndim != 2
            or design.shape[1] != len(point) or design.shape[0] < len(point)
            or not np.all(np.isfinite(design))):
        raise ValueError('finite normalized point and complete aligned training Jacobian required')
    _, _, vectors = np.linalg.svd(design, full_matrices=False)
    rays = []
    for vector in vectors[-1:-1-DIRECTIONS:-1]:
        vector = vector * np.sign(vector[np.argmax(np.abs(vector))])
        active = vector != 0
        candidates = [vector, -vector]

        def clearance(ray):
            return float(np.min((np.sign(ray[active])-point[active]) / ray[active]))

        rays.append(max(candidates, key=clearance))
    return point, np.asarray(rays)


def feasible_moves(point, whitened_jacobian):
    import numpy as np
    point, rays = weak_rays(point, whitened_jacobian)
    moves = []
    for rank, ray in enumerate(rays, start=1):
        for radius in RADII:
            target = point + radius*ray
            if np.any(np.abs(target) > 1):
                raise ValueError('declared singular direction lacks a feasible whole step')
            moves.append(dict(direction=rank, radius=radius, point=target))
    return moves


def summarize(change, affine, metric, *, cut):
    """Report three-axis displacement and the departure from the affine path."""
    import numpy as np

    change, affine, metric = (np.asarray(value, float) for value in (change, affine, metric))
    if (change.ndim != 2 or change.shape[1] != 3 or change.shape != affine.shape
            or change.shape != metric.shape or not 0 < cut < len(change)
            or any(not np.all(np.isfinite(x)) for x in (change, affine, metric))
            or np.any(metric <= 0)):
        raise ValueError('aligned physical metrics for two complete path sections required')
    displacement = np.linalg.norm(change*metric, axis=1)
    remainder = np.linalg.norm((change-affine)*metric, axis=1)
    results = {}
    for section, region in [('training', slice(None, cut)), ('forecast', slice(cut, None))]:
        scale = float(np.sqrt(np.mean(displacement[region]**2)))
        error = float(np.sqrt(np.mean(remainder[region]**2)))
        results[section] = dict(change_rms_m=scale, remainder_rms_m=error,
                                remainder_max_m=float(np.max(remainder[region])),
                                relative_remainder=error/scale if scale > 0 else None)
    return results


def task():
    return dict(identity='finite-calibration-remainders', input_key='interval', native_kind='value',
                payload=dict(directions=DIRECTIONS, radii=list(RADII)),
                limits=dict(native_calls=SWEEPS, packet_visits=SWEEPS*PACKETS*(TRAIN+FORECAST),
                            bound_calls=0, bound_steps=0))


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing frozen study')
    with closing(ClosedStudy(root, REPLAY)) as parent:
        if (parent.completion['manifest_sha256'] != REPLAY_SHA
                or parent.completion['state'] != 'complete'
                or not parent.rows['fixed-forecast-tangent']['passed']
                or parent.input('environment') != require_guarded_environment(environment())):
            raise ValueError('exact completed earlier-only tangent and environment required')
        materials = {key: parent.input(key, raw=True) for key in KEYS if key != 'tangent'}
        materials['tangent'] = parent.artifact('fixed-forecast-tangent', 'full-tangent.json', raw=True)
    inputs = {}
    for name, value in materials.items():
        path = base/name
        atomic(path, value)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=ADAPTER, tasks=[task()], inputs=inputs,
                      sources=source_closure(root, [ADAPTER, PLAN]), workers=1,
                      threads=1, maximum_wall_s=WALL_S)
    atomic(base/'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/'+ID, total=len(manifest['tasks']))


def evaluate(declared, context):
    from .airquantumgrav_inventory import environment

    work_spec = {k: v for k, v in declared.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or set(context.manifest['inputs']) != set(KEYS)
            or work_spec != task()
            or json.loads(context.input_path('environment').read_bytes()) != environment()):
        raise ValueError('unchanged frozen task and environment required')
    raw = invoke_frozen(context, entry=Path(__file__), calls=SWEEPS, inputs=KEYS)
    report = json.loads(raw)
    if len(report['comparisons']) != SWEEPS-1:
        raise ValueError('every declared finite comparison must be present')
    context.save_bytes('finite-changes.json', raw)
    return dict(passed=True, finite_comparisons=SWEEPS-1,
                baseline_scalar_max_m=report['baseline_scalar_max_m'],
                new_fits=0, later_receiver_positions_read=0, protected_reads=0,
                scientific_decision='abstain')


@contextmanager
def frozen_workspace(context, companions=(), *, parent_key='parent',
                     pack_key='frozen_python_native'):
    """Restore verified archived modules into an isolated process workspace."""
    from .studies.artifacts import digest, safe_path

    parent = json.loads(context.input_path(parent_key).read_bytes())
    with TemporaryDirectory(prefix='lll-esa-remainder-') as directory:
        work = Path(directory)
        hashes = parent['source_hashes']
        with ZipFile(context.input_path(pack_key)) as archive:
            if sorted(archive.namelist()) != sorted(hashes):
                raise ValueError('frozen source paths differ')
            for name, sha in hashes.items():
                raw = archive.read(name)
                if digest(raw) != sha:
                    raise ValueError('frozen source differs: '+name)
                target = safe_path(work, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        for name in companions:
            target = safe_path(work, name)
            data = safe_path(context.root/'source-freeze', name).read_bytes()
            if target.exists() or digest(data) != context.manifest['sources'][name]:
                raise ValueError('scalar replay helper conflicts with the archived package')
            target.write_bytes(data)
        yield work


def invoke_frozen(context, *, entry, calls, inputs, companions=()):
    """Run a bounded scalar adapter against the exact archived numerical package."""
    with frozen_workspace(context, companions) as work:
        output = work/'finite-changes.json'
        arguments = json.dumps({key: str(context.input_path(key).resolve()) for key in inputs})
        visits = PACKETS*(TRAIN+FORECAST)
        with context.prepay_native(native_calls=calls, packet_visits=calls*visits) as budget:
            for _ in range(calls):
                budget.reserve(native_calls=1, packet_visits=visits)
            subprocess.run([sys.executable, str(entry.resolve()), '_frozen', arguments,
                            str(output)], cwd=work, check=True,
                           env={**os.environ, 'PYTHONPATH': str(work/'analysis')})
        return output.read_bytes()


def scalar_replay(inputs, output, *, expected_model):
    import numpy as np
    from lll.ilvis0_estimator import Bounds
    from lll.ilvis0_precision_value import calculate, load, longitude_residual
    from lll.ilvis0_shape import TangentProblem
    from lll.ilvis0_solver_position import physical_metric
    from lll.ilvis0_training_forecast import initialize_training
    from lll.studies.artifacts import digest

    deadline = time.monotonic() + 60.

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    with np.load(inputs['interval'], allow_pickle=False) as archive:
        theta, dv, dt = (archive[key] for key in ('theta', 'dv', 'dt'))
    saved, earlier, recipe, fit = (read(name) for name in
                ('forecast', 'training_observations', 'recipe', 'fit'))
    point = np.asarray(fit['normalized_parameters'], float)
    coordinates = np.asarray(saved['coordinates'], float)
    times = np.asarray(read('forecast_times'), float)
    count = earlier['native_prefix_packets']
    rows = json.loads(gzip.decompress(Path(inputs['training']).read_bytes()))
    gps = np.array([[math.radians(row['latitude_deg']), math.radians(row['longitude_deg']),
                     row['height_m']] for row in rows])
    if (gps.shape != (TRAIN, 3) or gps.tolist() != earlier['coordinates']
            or len(dt) != PACKETS or times.shape != (TRAIN+FORECAST,)
            or times.tolist() != saved['times_s'] or coordinates.shape != (len(times), 3)
            or saved['prediction_receiver_positions_used'] is not False
            or not fit['converged']
            or fit['active_parameters'] != saved['active_parameters']
            or fit['active_parameters'] != fit['local_linearization']['active_parameters']
            or len(point) != 27
            or fit['normalized_parameters'] != saved['normalized_parameters']
            or any(digest(data[:count].astype('<f8').tobytes()) != earlier['training_prefix_sha256'][name]
                   for name, data in [('theta', theta), ('dv', dv), ('dt', dt)])):
        raise ValueError('exact saved forecast and original training support required')
    base_model = saved['frozen_error_model']
    if base_model != expected_model:
        raise ValueError('unchanged candidate fit required')
    clock, max_interval = recipe['clock'], recipe['maximum_interval_s']
    initial, gravity = initialize_training(times[:TRAIN], gps, theta=theta[:count],
                dv=dv[:count], dt=dt[:count], model=base_model,
                maximum_interval_s=max_interval, clock=clock)
    expected = read('compiler')
    kernel, compiler = load(output.parent/'kernel', precision='long_double',
                            gravity_anchor_height_m=gps[0, 2],
                            expected_source_sha256=expected['original_source_sha256'])
    if compiler['compiler'] != expected['compiler'] or compiler['mantissa_bits'] != expected['internal_mantissa_bits']:
        raise ValueError('scalar compiler and precision must match the tangent build')
    # The subtraction reference is the original prediction at every epoch.
    # Neither the scalar integrator nor the physical metric sees later receiver observations.
    problem = TangentProblem(theta, dv, dt, times, coordinates, np.eye(coordinates.size),
                initial, Bounds(recipe['limits']), fit_earth_removal=True, tangent_kernel=None,
                clock_hypothesis=clock, processing_hypothesis='unsubtracted_increment_hypothesis',
                maximum_interval_s=max_interval, gravity_mps2=gravity, disc_radius_m=6371000.)
    if list(problem.bounds.active) != fit['active_parameters']:
        raise ValueError('frozen column ordering must match the scalar parameters')
    metric = physical_metric(coordinates)

    def displacement(target):
        if time.monotonic() >= deadline:
            raise ValueError('cooperative scalar replay deadline reached')
        difference = calculate(problem, target, base_model, kernel=kernel,
                               longitude='stable')['coordinate_difference']
        difference[:, 1] = longitude_residual(difference[:, 1])
        return difference

    baseline = displacement(point)
    baseline_max = float(np.max(np.linalg.norm(baseline*metric, axis=1)))
    if baseline_max > 1e-6:
        raise ValueError(f'scalar baseline differs from sealed tangent position by {baseline_max:.9g} m')
    return fit, point, metric, compiler, baseline, baseline_max, displacement


def frozen_replay(inputs, output):
    import numpy as np
    from lll.studies.artifacts import digest, encoded

    tangent = json.loads(Path(inputs['tangent']).read_bytes())
    fit, point, metric, compiler, baseline, baseline_max, displacement = scalar_replay(
        inputs, output, expected_model='sphere_rotating')
    jac = np.asarray(tangent['jacobian'], float)
    if (jac.shape != (baseline.size, len(point))
            or fit['active_parameters'] != tangent['active_parameters']
            or fit['normalized_parameters'] != tangent['normalized_parameters']
            or tangent['source_forecast_sha256'] != digest(Path(inputs['forecast']).read_bytes())):
        raise ValueError('exact saved tangent required')
    comparisons = []
    for move in feasible_moves(point, fit['local_linearization']['jacobian']):
        delta = move['point'] - point
        actual = displacement(move['point']) - baseline
        predicted = (jac @ delta).reshape(baseline.shape)
        comparisons.append(dict(direction=move['direction'], radius=move['radius'],
            normalized_change=delta.tolist(), position_change=actual.tolist(),
            **summarize(actual, predicted, metric, cut=TRAIN)))
    output.write_bytes(encoded(dict(baseline_scalar_max_m=baseline_max, compiler=compiler,
        comparisons=comparisons, fit_starts=0, later_receiver_positions_read=0,
        protected_reads=0, establishes_uniform_bound=False, scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '_frozen':
        frozen_replay(json.loads(sys.argv[2]), Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action', choices=('prepare',))
        parser.parse_args()
        print(json.dumps(prepare(Path.cwd()), sort_keys=True))
