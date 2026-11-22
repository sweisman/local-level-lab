# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated checks of the height-aware interval remainder."""
import json
from pathlib import Path


ID = 'shape-gravity-history-v4-20261119'
PLAN = 'docs/prediction-observed-development/SHAPE_GRAVITY_HISTORY_V4_PLAN.md'
PACKETS = 160
ANCHOR = 1482.531
STEP_LIMIT = 4 * PACKETS
GRIDS = (.005, .25)
MODELS = ('sphere_still', 'flat_still')
LIMIT = .0403


def tasks():
    return [
        dict(identity=f'{model}-{period:g}', input_key='plan',
             payload=dict(model=model, period=period),
             limits=dict(native_calls=4, packet_visits=4*PACKETS, bound_calls=1,
                         bound_steps=STEP_LIMIT))
        for model in MODELS for period in GRIDS
    ]


def declared_case(task):
    for declared in tasks():
        if all(task.get(key) == value for key, value in declared.items()):
            return declared['payload']
    raise ValueError('fixed generated model, grid and limits required')


def generated(model, period):
    import numpy as np

    dt = np.full(PACKETS, period)
    t = np.arange(PACKETS)*period
    theta = dt[:, None]*np.column_stack(
        (.0002*np.sin(t/8), -.0003*np.cos(t/12), .00015*np.cos(t/9)))
    dv = dt[:, None]*np.column_stack(
        (.002*np.sin(t/7), .002*np.cos(t/9), -9.81+.004*np.sin(t/10)))
    config = dict(initial_c=np.array([.7, 1.2, 3200.]), initial_v=np.array([100., 15., -6.]),
                  initial_r=np.eye(3), model=1+MODELS.index(model), profile=False,
                  gravity=9.81, radius=6371000.,
                  limits=np.r_[[.01]*3, [2.]*3, [10.]*3, [2e-6]*3, [.01]*3,
                               [.001]*6, [2.]*3, .01, 1/1024, 1.])
    times = period*(np.array([20, 40, 80, PACKETS])-.5)
    return config, np.ascontiguousarray(theta), np.ascontiguousarray(dv), dt, times


def generated_reference(config, theta, dv, dt):
    import numpy as np
    from .ilvis0_initial_source_bridge_v2 import certify
    from .ilvis0_transform_native import make_reference

    center = np.zeros(27)
    lower, upper = center-.1, center+.1
    reference = make_reference(config, theta, dv, dt, lower=lower, upper=upper, center=center,
                               outward_initial_force=True)
    certificate = certify(reference, lower, upper)
    if not certificate['nonlinear_cap_sufficient']:
        raise ValueError('generated initial-force cap requires more headroom')
    return reference, certificate


def evaluate(task, context):
    import ctypes
    import numpy as np
    from .ilvis0_batched_transport import configure_backend
    from .ilvis0_control_shards import _check_continue
    from .ilvis0_directional_acceleration import DirectionalAcceleration
    from .ilvis0_native_prefix import enclose_many
    from .ilvis0_source_prefix import load_kernels
    from .ilvis0_wide_tangent import load

    case = declared_case(task)
    model, period = case['model'], case['period']
    source = context.root/'source-freeze/analysis/lll'
    directory = context.root/'shards'/f'{context.shard:03d}'/'kernels'
    backend = configure_backend(directory, source_directory=source)
    kernels, compiled = load_kernels(directory, source_directory=source)
    original_sha = context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']
    tangent, native = load(directory, gravity_anchor_height_m=ANCHOR,
                           expected_source_sha256=original_sha)
    context.save('compiler.json', dict(prefix=compiled, outward=backend, native=native))
    config, theta, dv, dt, times = generated(model, period)
    reference, certificate = generated_reference(config, theta, dv, dt)
    context.save('initial-force.json', certificate)
    center, lower, upper = reference.parent.center, reference.parent.lower, reference.parent.upper
    proof = DirectionalAcceleration(reference, lower, upper)

    def reserve(**resources):
        if 'packet_steps' not in resources:
            _check_continue(context.root, context.manifest)

    context.charge(bound_calls=1, bound_steps=STEP_LIMIT)
    result = enclose_many(config, theta, dv, dt, times=times, lower=lower, upper=upper,
        reference=reference, conditioning=proof, prefix_kernels=kernels, maximum_packet_steps=STEP_LIMIT,
        reserve=reserve, maximum_seconds=25., gravity_anchor_height_m=ANCHOR,
        reuse_force_profiles=True)
    context.save('bounds.json', [bound.report() for bound in result['bounds']])

    def forecast(point):
        out = np.empty((len(times), 3))
        jac = np.empty((3*len(times), 27))
        context.charge(native_calls=1, packet_visits=PACKETS)
        code = tangent(PACKETS, theta, dv, dt, len(times), times, config['initial_c'], config['initial_v'],
            config['initial_r'], config['limits'], point, config['model'], 0, config['gravity'],
            config['radius'], out, jac, ctypes.byref(ctypes.c_int()))
        if code:
            raise ValueError(f'compiled forecast returned {code}')
        return out, jac.reshape(len(times), 3, 27)

    values, native_jac = forecast(center)
    points = (lower, upper, np.linspace(lower[0], upper[0], 27))
    probes = [(forecast(p)[0], np.r_[p-center, reference.normalized_values_at(p)]) for p in points]
    scale = np.array([6371000., 6371000., 1.])
    rows = []
    for index, bound in enumerate(result['bounds']):
        design = bound.design(native_jac[index], reference, gravity_anchor_height_m=ANCHOR)
        if design.shape != (3, 51) or not np.array_equal(design[:, :27], native_jac[index]):
            raise ValueError('expected all physical and shared design columns')
        center_error = np.abs((bound.center-values[index])*scale)
        radius = bound.unshared_remainder*scale
        errors = [np.abs((actual[index]-values[index]-design@delta)*scale)
                  for actual, delta in probes]
        numerical = bool(max(center_error) <= 1e-5 and np.all(np.asarray(errors) <= radius+1e-5))
        rows.append(dict(time_s=float(times[index]), radius_m=radius.tolist(),
            maximum_center_error_m=float(max(center_error)), probes_contained=numerical,
            reaches_target=bool(max(radius) <= LIMIT)))
    return dict(identity=task['identity'], passed=all(r['probes_contained'] for r in rows),
                rows=rows, work=result['work'], original_reads=0, optimizer_starts=0,
                aircraft_remainder_certified=False, scientific_decision='abstain')


def main():
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    root = Path.cwd()
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, 'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_source_prefix_reference.cpp', 'analysis/lll/ilvis0_source_prefix_intervals.cpp'])
    definition = dict(id=ID, adapter=adapter, sources=sources, tasks=tasks(), inputs={'plan': PLAN},
        scope='Generated height-gravity bound growth only', workers=1, threads=1, maximum_wall_s=120.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(json.dumps(dict(study='data/'+ID, allowance=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    main()
