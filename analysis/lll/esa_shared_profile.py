# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recover the common calibration coefficient history bound to a saved ESA fit."""
from contextlib import closing
from fractions import Fraction
from io import BytesIO
import json
import os
from pathlib import Path
import subprocess
import sys


ID = 'esa-shared-profile-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_SHARED_PROFILE_PLAN.md'
SCOPE = 'Full shared calibration coefficient history on sealed ESA 187 inputs'
MODELS = ('sphere_still', 'flat_still')
PACKETS = 155868
QUERIES = 520
PRECHECK = 'data/esa-shape-prefix-preflight-v2-20261119'
PRECHECK_SHA = 'f38473c8e02a1e7c6827a38e797f612658773f2255a8329628ec76f74cf84b97'
START_FIELDS = ('initial_c', 'initial_v', 'initial_r', 'limits')


def tasks():
    return [dict(identity=model,input_key='interval',native_kind='value',payload=dict(model=model),
                 limits=dict(native_calls=2,packet_visits=2*PACKETS*QUERIES,
                             bound_calls=1,bound_steps=PACKETS)) for model in MODELS]


def nominal_clocks(dt, times, offset):
    """Recover the binary clock position and the selected one-sided slope."""
    import numpy as np

    ends = np.cumsum(dt)
    clock = times + offset
    indices = np.searchsorted(ends, clock, side='left')
    if np.any(clock < 0.) or np.any(indices == len(dt)) or np.any(np.diff(ends) <= 0.):
        raise ValueError('complete positive elapsed packet clock required')
    start = np.r_[0., ends[:-1]][indices]
    duration = dt[indices]
    elapsed = start + np.clip((clock-start)/duration,0.,1.)*duration
    slope = (1./duration)*duration
    return elapsed, slope


def coefficients(config, theta, dv, dt, times, body, *, center, lower, upper):
    import numpy as np
    from .ilvis0_clocked_force_transform import ClockedForceTransform
    from .ilvis0_component_geography import Coordinates, Scalar, coordinate_map, plus
    from .ilvis0_force_integrals import enclose_many
    from .ilvis0_local_step_bounds import Value
    from .ilvis0_transform_native import make_reference

    if config['model'] not in (1,2):
        raise ValueError('saved zero-field candidate required')
    model = MODELS[config['model']-1]
    radius = config['radius']
    reference = make_reference(config,theta,dv,dt,lower=lower,upper=upper,center=center,
                               outward_initial_force=True)
    initial = Coordinates(*(Scalar.fixed(v) for v in config['initial_c']))
    physical = np.asarray(config['limits'])*center
    offsets = coordinate_map(initial,Value(physical[6:9]),model=model,disc_radius_m=radius)
    initial = Coordinates(*(plus(v,d) for v,d in zip(
        (initial.latitude,initial.longitude,initial.height),offsets,strict=True)))

    def metric(position):
        fixed = Coordinates(*(Scalar.fixed(v) for v in position))
        return [v.center for v in coordinate_map(fixed,Value([1.,1.,1.]),
                                                  model=model,disc_radius_m=radius)]

    reference_metric = metric(initial.center)
    elapsed, slopes = nominal_clocks(dt,times,physical[25])
    scale = Fraction(float(config['limits'][25]))
    window = [scale*Fraction(float(v)) for v in (center[25],lower[25],upper[25])]
    queries = (tuple(Fraction(float(t))+v for v in window) for t in times)
    force = dv/dt[:,None]-dv[0]/dt[0]
    integrals = enclose_many(dt,force,queries=queries,maximum_packets=len(dt),maximum_seconds=100.)
    result = []
    for t,body_position,s,q,integral in zip(times,body,elapsed,slopes,integrals,strict=True):
        clock_force = ClockedForceTransform(reference.transform,integral,
                                             nominal_time=t,metric=reference_metric)
        result.append(np.c_[
            reference.parent.coefficients(reference_metric,q,metric(body_position)).matrix,
            reference.acceleration.coefficients(reference_metric,clock_center=s,time_slope=q).matrix,
            clock_force.coefficients.matrix,
        ])
    return np.asarray(result)


def frozen_body(interval, metadata_path, target, compiler_path, output):
    import ctypes
    import numpy as np
    from lll.ilvis0_precision_value import load

    metadata = json.loads(Path(metadata_path).read_bytes())
    compiler = json.loads(Path(compiler_path).read_bytes())
    config = metadata['configuration']
    with np.load(interval,allow_pickle=False) as raw:
        theta,dv,dt = (np.ascontiguousarray(raw[k]) for k in ('theta','dv','dt'))
    with np.load(target,allow_pickle=False) as raw:
        times,point,positions = (np.ascontiguousarray(raw[k]) for k in ('times','center','positions'))
    kernel,actual = load(Path(output).parent/'build',precision='long_double',
        gravity_anchor_height_m=metadata['gravity_anchor_height_m'],
        expected_source_sha256=compiler['original_source_sha256'])
    if (actual['compiler']!=compiler['compiler']
            or actual['mantissa_bits']!=compiler['internal_mantissa_bits']):
        raise ValueError('archived scalar compiler and precision required')
    fields = [np.ascontiguousarray(config[name],dtype=float) for name in START_FIELDS]

    def integrate(parameters):
        values = np.empty_like(positions)
        delta = np.empty_like(positions)
        code = kernel(len(dt),theta,dv,dt,len(times),times,*fields,parameters,
            config['model'],int(config['profile']),config['gravity'],config['radius'],
            values,positions,delta,ctypes.byref(ctypes.c_int()))
        if code or not np.isfinite(values).all():
            raise ValueError('sealed scalar integration did not complete')
        return values

    antenna = integrate(point)
    without_lever = point.copy()
    without_lever[21:24] = 0.
    np.savez(output,antenna=antenna,body=integrate(without_lever))


def evaluate(task, context):
    import numpy as np
    from .esa_tangent_remainder import frozen_workspace
    from .ilvis0_solver_position import physical_metric

    model = task['identity']
    declared = {key:value for key,value in task.items() if key not in ('index','shard')}
    if context.manifest['scope']!=SCOPE or declared not in tasks():
        raise ValueError('exact shared-profile scope required')
    metadata_path = context.input_path(model+'-metadata')
    metadata = json.loads(metadata_path.read_bytes())
    with np.load(context.input_path(model),allow_pickle=False) as archive:
        targets = {name:archive[name] for name in archive.files}
    positions,times = targets['positions'],targets['times']
    interval = context.input_path('interval')
    with np.load(interval,allow_pickle=False) as raw:
        theta,dv,dt = (raw[k] for k in ('theta','dv','dt'))
    if len(dt)!=PACKETS or positions.shape!=(QUERIES,3) or times.shape!=(QUERIES,):
        raise ValueError('exact archived packet and forecast history required')
    with frozen_workspace(context) as work:
        result = work/'body.npz'
        for _ in range(2):
            context.charge(native_calls=1,packet_visits=PACKETS*QUERIES)
        subprocess.run([sys.executable,str(Path(__file__).resolve()),'_body',str(interval),
                        str(metadata_path),str(context.input_path(model)),
                        str(context.input_path(model+'-compiler')),str(result)],
                       cwd=work,check=True,env={**os.environ,'PYTHONPATH':str(work/'analysis')})
        with np.load(result,allow_pickle=False) as saved:
            antenna,body = saved['antenna'],saved['body']
    metres = physical_metric(positions)
    replay = float(np.max(np.linalg.norm((antenna-positions)*metres,axis=1)))
    if replay > 1e-6:
        raise ValueError('full sealed scalar forecast did not replay')
    context.charge(bound_calls=1,bound_steps=PACKETS)
    shared = coefficients(metadata['configuration'],theta,dv,dt,times,body,
        **{k:targets[k] for k in ('center','lower','upper')})
    error = float(np.max(np.abs((shared[:2]-targets['precheck'])*metres[:2,:,None])))
    output = BytesIO()
    np.savez(output,shared=shared,body=body,times=times)
    context.save_bytes('shared-profile.npz',output.getvalue())
    return dict(passed=error<=1e-9,scalar_replay_max_m=replay,precheck_column_max_m=error,
                shared_shape=list(shared.shape),fit_starts=0,protected_reads=0,
                aircraft_remainder_certified=False,scientific_decision='abstain')


def main():
    import numpy as np
    from .conditioned_shape_calibration import PARENT_SHA
    from .esa_calibration_contrast import ID as SOURCE
    from .studies.artifacts import atomic,digest,encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    root = Path.cwd()
    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing shared-profile freeze')
    materials = {}
    with closing(ClosedStudy(root,PRECHECK)) as preflight, closing(
            ClosedStudy(root,'data/'+SOURCE,store=preflight.store)) as source:
        if (preflight.completion['manifest_sha256']!=PRECHECK_SHA or not preflight.summary['passed']
                or source.completion['manifest_sha256']!=PARENT_SHA or not source.summary['passed']):
            raise ValueError('exact complete prefix and forecast histories required')
        for name in ('interval','parent','frozen_python_native'):
            materials[name] = source.input(name,raw=True)
        for model in MODELS:
            raw = preflight.input(model+'-metadata',raw=True)
            metadata = json.loads(raw)
            forecast = source.input(model+'-forecast',raw=True)
            if (metadata['forecast_sha256']!=digest(forecast)
                    or metadata['parent_interval_sha256']!=digest(materials['interval'])):
                raise ValueError('prefix must identify the exact full record')
            materials[model+'-metadata'] = raw
            materials[model+'-compiler'] = source.input(model+'-compiler',raw=True)
            predictions = json.loads(forecast)
            bounds = preflight.artifact(model,'bounds.json')
            precheck = np.asarray([np.c_[row['previous_coefficients'],row['acceleration_coefficients'],
                                        row['transform_coefficients']] for row in bounds])
            with np.load(BytesIO(preflight.input(model,raw=True)),allow_pickle=False) as saved:
                target = dict(center=saved['center'],lower=saved['lower'],upper=saved['upper'],
                              times=predictions['times_s'],positions=predictions['coordinates'],precheck=precheck)
            output = BytesIO()
            np.savez(output,**target)
            materials[model] = output.getvalue()
    base.mkdir(parents=True)
    inputs = {'plan':PLAN}
    for name, raw in materials.items():
        path = base/name
        atomic(path,raw)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID,adapter=adapter,inputs=inputs,tasks=tasks(),scope=SCOPE,
        sources=source_closure(root,[adapter,PLAN]),workers=2,threads=1,maximum_wall_s=180.)
    manifest = Definition.from_dict(definition,root).prepare(root)
    print(json.dumps(dict(study='data/'+ID,allowance=manifest['limits']),sort_keys=True))


if __name__ == '__main__':
    if len(sys.argv)==7 and sys.argv[1]=='_body':
        frozen_body(*sys.argv[2:])
    else:
        main()
