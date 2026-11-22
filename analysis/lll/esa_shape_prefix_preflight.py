# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the height-aware interval predictor on the start of sealed ESA fits."""
import argparse
from contextlib import closing
import gzip
from io import BytesIO
import json
import math
from pathlib import Path
import time


ID = 'esa-shape-prefix-preflight-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_SHAPE_PREFIX_PREFLIGHT_PLAN.md'
DYADIC_ID = 'esa-shape-prefix-preflight-v2-20261119'
DYADIC_PLAN = 'docs/prediction-observed-development/ESA_SHAPE_PREFIX_PREFLIGHT_V2_PLAN.md'
PREFLIGHT_SHA = '226a225c6a7a83780c025fc3b60ad9fab2e49dcb0b705e708549cea24c941377'
MODELS = ('sphere_still', 'flat_still')
PREFIX_PACKETS = 640
STEP_LIMIT = 2*PREFIX_PACKETS
QUERIES = 2
SIDE = .1
TOLERANCE_M = 1e-6
SCOPE = 'Recorded ESA 187 prefixes and sealed targets only; no fits or later observations'


def tasks():
    return [
        dict(identity=model, input_key=model, payload=dict(model=model),
             limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=STEP_LIMIT))
        for model in MODELS
    ]


def material(study, model):
    import numpy as np
    from .esa_calibration_contrast import TRAIN, FORECAST, PACKETS
    from .ilvis0_exploratory import MODELS as NATIVE_MODELS, ConditionalBounds
    from .ilvis0_shape import PARAMETERS
    from .ilvis0_training_forecast import initialize_training
    from .studies.artifacts import digest

    recipe = study.input('recipe')
    raw = study.input('interval', raw=True)
    with np.load(BytesIO(raw), allow_pickle=False) as archive:
        theta, dv, dt = (archive[key] for key in ('theta', 'dv', 'dt'))
    rows = json.loads(gzip.decompress(study.input('training', raw=True)))
    gps = np.array([[math.radians(v['latitude_deg']), math.radians(v['longitude_deg']),
                     v['height_m']] for v in rows])
    times = np.asarray(study.input('forecast_times'))
    fit = study.input(model+'-fit')
    forecast_raw = study.input(model+'-forecast', raw=True)
    forecast = json.loads(forecast_raw)
    earlier = study.input(model+'-training_observations')
    compiler = study.input(model+'-compiler')
    tangent = study.artifact(model, 'full-tangent.json')
    count = earlier['native_prefix_packets']
    normalized = np.asarray(fit['normalized_parameters'])
    if (len(dt) != PACKETS or times.shape != (TRAIN+FORECAST,) or gps.shape != (TRAIN, 3)
            or times.tolist() != forecast['times_s'] or gps.tolist() != earlier['coordinates']
            or forecast['prediction_receiver_positions_used'] is not False
            or forecast['frozen_error_model'] != model or not fit['converged']
            or compiler['gravity_anchor_height_m'] != gps[0, 2]
            or tuple(fit['active_parameters']) != PARAMETERS
            or fit['normalized_parameters'] != forecast['normalized_parameters']
            or fit['normalized_parameters'] != tangent['normalized_parameters']
            or tangent['source_forecast_sha256'] != digest(forecast_raw)
            or tangent['forecast_queries_s'] != times.tolist()
            or tangent['weighting_applied'] is not False
            or tangent['jacobian_shape'] != [3*len(times), 27]
            or any(digest(data[:count].astype('<f8').tobytes()) != earlier['training_prefix_sha256'][name]
                   for name, data in [('theta', theta), ('dv', dv), ('dt', dt)])):
        raise ValueError('original earlier observations, fit and forecast tangent must agree')
    initial, gravity = initialize_training(
        times[:TRAIN], gps, theta=theta[:count], dv=dv[:count], dt=dt[:count], model=model,
        maximum_interval_s=recipe['maximum_interval_s'], clock=recipe['clock'])
    constraints = ConditionalBounds(recipe['limits'], fit_earth_removal=True)
    limits = np.array([constraints.limits[name] for name in PARAMETERS])
    lower, upper = np.maximum(-1., normalized-SIDE), np.minimum(1., normalized+SIDE)
    edge = times[QUERIES-1]+limits[25]*upper[25]
    # Keep an extra packet beyond the clipped query to cover accumulation rounding.
    packets = int(np.searchsorted(np.cumsum(dt[:PREFIX_PACKETS]), edge, side='right'))+2
    if not 0 < packets <= PREFIX_PACKETS or times[0]+limits[25]*lower[25] < 0:
        raise ValueError('both original queries must have complete bounded packet support')
    config = dict(initial_c=[initial['latitude_rad'], initial['longitude_rad'], initial['height_m']],
                  initial_v=initial['velocity_ned_mps'], initial_r=initial['attitude_body_to_ned'],
                  model=NATIVE_MODELS.index(model), profile=True, gravity=gravity, radius=6371000.,
                  limits=limits)
    metadata = dict(configuration={key: np.asarray(value).tolist() for key, value in config.items()},
        gravity_anchor_height_m=float(gps[0, 2]), parent=study.completion,
        forecast_sha256=digest(forecast_raw), packet_count=packets, cut_upper_s=float(edge),
        parent_interval_sha256=digest(raw), model=model)
    payload = dict(theta=theta[:packets], dv=dv[:packets], dt=dt[:packets], times=times[:QUERIES],
                   center=normalized, lower=lower, upper=upper,
                   positions=np.asarray(forecast['coordinates'])[:QUERIES],
                   jacobian=np.asarray(tangent['jacobian'])[:3*QUERIES])
    return metadata, payload


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact recorded prefix scope required')
    return evaluate_prepared(task, context, packet_limit=PREFIX_PACKETS, step_limit=STEP_LIMIT,
                             seconds=50.)


def evaluate_prepared(task, context, *, packet_limit, step_limit, seconds, save_queries=False, on_position_budget=None):
    import numpy as np
    from .ilvis0_batched_transport import configure_backend
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_directional_acceleration import DirectionalAcceleration
    from .ilvis0_native_prefix import enclose_many
    from .ilvis0_solver_position import physical_metric
    from .ilvis0_source_prefix import load_kernels
    from .ilvis0_transform_native import make_reference

    model = task['identity']
    metadata = json.loads(context.input_path(model+'-metadata').read_bytes())
    with np.load(context.input_path(model), allow_pickle=False) as raw:
        values = {key: raw[key] for key in raw.files}
    theta, dv, dt, times, point, lower, upper = (
        values[key] for key in ('theta', 'dv', 'dt', 'times', 'center', 'lower', 'upper'))
    if metadata['model'] != model or len(dt) != metadata['packet_count'] or len(dt) > packet_limit:
        raise ValueError('exact bounded prefix material required')
    config = metadata['configuration']
    source = context.root/'source-freeze/analysis/lll'
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    outward = configure_backend(directory, source_directory=source)
    kernels, compiled = load_kernels(directory, source_directory=source)
    context.save('compiler.json', dict(outward=outward, prefix=compiled))
    reference = make_reference(config, theta, dv, dt, lower=lower, upper=upper,
                               center=point, outward_initial_force=True)
    conditioning = DirectionalAcceleration(reference, lower, upper)
    context.save('reference.json', reference.report())
    context.charge(bound_calls=1, bound_steps=step_limit)

    def reserve(**counts):
        if 'packet_steps' not in counts:
            _check_continue(context.root, context.manifest)

    anchor = metadata['gravity_anchor_height_m']
    started = time.monotonic()
    forecasts = values['positions']
    metric = physical_metric(forecasts)

    def checkpoint(index, bound):
        error = float(np.linalg.norm((np.asarray(bound['center'])-forecasts[index])*metric[index]))
        context.save(f'query-{index:02d}.json', dict(bound=bound, center_error_m=error,
            predicted_center_matches=error <= TOLERANCE_M,
            remainder_m=(np.asarray(bound['unshared_remainder'])*metric[index]).tolist()))

    result = enclose_many(config, theta, dv, dt, times=times, lower=lower, upper=upper,
        reference=reference, conditioning=conditioning, prefix_kernels=kernels,
        maximum_packet_steps=step_limit, reserve=reserve, maximum_seconds=seconds,
        gravity_anchor_height_m=anchor, reuse_force_profiles=True, on_report=checkpoint if save_queries else None,
        on_position_budget=on_position_budget)
    errors, remainders = [], []
    for j, bound in enumerate(result['bounds']):
        jacobian = values['jacobian'][3*j:3*j+3]
        design = bound.design(jacobian, reference, gravity_anchor_height_m=anchor)
        if design.shape != (3, 51) or not np.array_equal(design[:, :27], jacobian):
            raise ValueError('the archived physical derivative columns must be retained')
        errors.append(float(np.linalg.norm((bound.center-forecasts[j])*metric[j])))
        remainders.append((bound.unshared_remainder*metric[j]).tolist())
    context.save('bounds.json', [bound.report() for bound in result['bounds']])
    return dict(passed=max(errors) <= TOLERANCE_M, model=model, packet_count=len(dt),
                query_times_s=times.tolist(), center_errors_m=errors, remainder_m=remainders,
                elapsed_s=time.monotonic()-started, work=result['work'],
                fit_starts=0, later_receiver_positions_read=0, protected_reads=0,
                aircraft_remainder_certified=False, scientific_decision='abstain')


def main():
    import numpy as np
    from .conditioned_shape_calibration import PARENT_SHA
    from .esa_calibration_contrast import ID as SOURCE
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reuse-prefixes', action='store_true')
    args = parser.parse_args()
    identity, plan = (DYADIC_ID, DYADIC_PLAN) if args.reuse_prefixes else (ID, PLAN)
    root = Path.cwd()
    base = root/'data'/(identity+'-inputs')
    if base.exists() or (root/'data'/identity).exists():
        raise ValueError('use the existing ESA prefix freeze')
    if args.reuse_prefixes:
        with closing(ClosedStudy(root, 'data/'+ID)) as study:
            if (study.completion['manifest_sha256'] != PREFLIGHT_SHA
                    or study.envelope('sphere_still')['result'].get('reason') != 'native batch time allowance exhausted'
                    or not study.envelope('flat_still')['result']['passed']):
                raise ValueError('exact first preflight, including its time-limit outcome, required')
            packets = {model: study.input(model, raw=True) for model in MODELS}
            metadata = {model: study.input(model+'-metadata', raw=True) for model in MODELS}
    else:
        with closing(ClosedStudy(root, 'data/'+SOURCE)) as study:
            if study.completion['manifest_sha256'] != PARENT_SHA or not study.summary['passed']:
                raise ValueError('exact closed ESA calibration study required')
            selected = {model: material(study, model) for model in MODELS}
        packets, metadata = {}, {}
        for model, (record, payload) in selected.items():
            buffer = BytesIO()
            np.savez(buffer, **payload)
            packets[model], metadata[model] = buffer.getvalue(), encoded(record)
    base.mkdir(parents=True)
    inputs = {'plan': plan}
    for model in MODELS:
        for key, suffix, raw in ((model, '.npz', packets[model]),
                                 (model+'-metadata', '.json', metadata[model])):
            path = base/(model+suffix)
            atomic(path, raw)
            inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, plan, 'analysis/lll/ilvis0_source_prefix_reference.cpp',
        'analysis/lll/ilvis0_source_prefix_intervals.cpp'])
    definition = dict(id=identity, adapter=adapter, sources=sources, inputs=inputs, tasks=tasks(),
                      scope=SCOPE, workers=2, threads=1, maximum_wall_s=120.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(json.dumps(dict(study='data/'+identity, allowance=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    main()
