# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite one-packet qualification of all27 path derivative columns."""
from fractions import Fraction as F
import math


def recipe():
    return dict(packets=1,query_fraction=.5,center=[0.]*27,columns=list(range(27)),
        native_calls_per_case=1,interval_steps_per_case=27,maximum_bound_seconds=30.,
        comparison_tolerance_m=1e-6,original_reads=0,optimizer_starts=0)


def validate_recipe(value):
    if value!=recipe():raise ValueError('fixed one-packet all-column software recipe required')


def compare(prediction,jacobian,bounds,scale):
    if (len(prediction)!=3 or len(jacobian)!=3 or any(len(row)!=27 for row in jacobian)
            or len(bounds)!=27 or [row['column'] for row in bounds]!=list(range(27))
            or len(scale)!=3 or any(not math.isfinite(s) or s<=0 for s in scale)
            or any(not math.isfinite(v) for v in (*prediction,*(v for row in jacobian for v in row)))):
        raise ValueError('complete finite native values, all27 ordered columns and positive scales required')
    positions=[];derivatives=[]
    for column,row in enumerate(bounds):
        coords=row['coordinates']
        if len(coords)!=3:raise ValueError('three coordinate derivative bounds required')
        for axis,coordinate in enumerate(coords):
            values=coordinate['exact_derivatives']
            if len(values)!=4:raise ValueError('orders zero through three required')
            for order,value in enumerate(values):
                if len(value)!=2:raise ValueError('complete derivative interval required')
                lo,hi=map(F,value)
                if lo>hi:raise ValueError('ordered derivative interval required')
                if order<2:
                    expected=F(float(prediction[axis] if order==0 else jacobian[axis][column]))
                    gap=max(F(0),lo-expected,expected-hi)*F(float(scale[axis]))
                    (positions if order==0 else derivatives).append(gap)
    p,d=max(positions),max(derivatives);tolerance=F(recipe()['comparison_tolerance_m'])
    return dict(passed=max(p,d)<=tolerance,physical_columns=27,
        maximum_position_gap_m=float(p),maximum_derivative_gap_m=float(d),
        comparison_tolerance_m=float(tolerance),position_checks=len(positions),derivative_checks=len(derivatives),
        native_execution_error_bound=False,whole_history_qualified=False,observational_coverage_qualified=False)


def evaluate(task,context):
    import ctypes
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_training_density import boundary_count
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_path_packets import predict_branch
    from lll.ilvis0_sharded_native import plain
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    case=runner._load(context.input_path(spec['case_key']));config=case['configuration']
    if (len(case['dt'])!=1 or case['center']!=settings['center']
            or config['model']!=spec['model'] or config['profile']!=spec['profile'] or config['limits'][25]!=1.):
        raise ValueError('unchanged qualified prefix and original configuration required')
    arrays={k:np.ascontiguousarray(config[k],float) for k in ('initial_c','initial_v','initial_r','limits')}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    query=float(dt[0])*settings['query_fraction']
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if (metadata['compiler']!=spec['compiler'] or
            metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('frozen native source/compiler changed')
    context.save('kernel.json',metadata);context.charge(native_calls=1,packet_visits=1)
    output=np.full((1,3),np.nan);jac=np.full((3,27),np.nan);flag=ctypes.c_int()
    code=kernel(1,theta,dv,dt,1,np.array([query]),arrays['initial_c'],arrays['initial_v'],arrays['initial_r'],
        arrays['limits'],np.zeros(27),config['model'],int(config['profile']),config['gravity'],config['radius'],
        output,jac,ctypes.byref(flag))
    raw=dict(status=int(code),boundary_counter=flag.value,query_s=query)
    if code==0:raw.update(prediction=output[0],jacobian=jac)
    context.save('native.json',plain(raw))
    context.save('boundary.json',boundary_count(status=int(code),counter=flag.value,dt=dt,times=[query]))
    if not np.all(np.isfinite(output)) or not np.all(np.isfinite(jac)):
        raise ValueError('finite native prediction and all27 derivatives required')
    bounds=[]
    for column in settings['columns']:
        runner._check_continue(context.root,context.manifest)
        context.charge(bound_calls=1,bound_steps=1)
        parameters=[J.constant(0)]*27
        parameters[column]=J(((0,0),(1,1),(0,0),(0,0)))
        answer=predict_branch(config,case['theta'],case['dv'],case['dt'],parameters,
            time=query,packet_index=0,maximum_packets=1,maximum_seconds=settings['maximum_bound_seconds'])
        record=dict(column=column,**answer.report());bounds.append(record)
        context.save(f'direction-{column:02d}.json',record)
    metrics=compare(output[0].tolist(),jac.tolist(),bounds,spec['coordinate_scale'])
    context.save('comparison.json',metrics)
    return dict(identity=task['identity'],model=spec['model'],profile=spec['profile'],**metrics,
        native_evaluations=1,interval_packet_steps=27,original_reads=0,optimizer_starts=0,
        higher_order_native_reference=False,scientific_decision='abstain')
