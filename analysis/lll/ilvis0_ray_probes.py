# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-selected ray contractions; not nonlinear uncertainty bounds."""
from fractions import Fraction as F


def recipe():
    return dict(packets=96000,training_epochs=292,query_epochs=293,future_s=438.,
        proposal_target_m=.75,training_allowance_m=1.,width_targets_m=[20.,20.,50.],
        search_steps=48,physical_columns=27,optimizer_starts=0,original_reads=0)


def validate_recipe(value):
    if value!=recipe():raise ValueError('unchanged finite ray recipe and acceptance targets required')


def choose(actual_training,baseline_training,jacobian_training,point,scale):
    """Choose a fixed smaller ray using saved training values only.

The envelope applies to a quadratic proposal heuristic, not the unknown true
nonlinear response. Only a separately charged native call can check feasibility.
"""
    import numpy as np
    a,b,j,p,s=(np.asarray(v,float) for v in (actual_training,baseline_training,jacobian_training,point,scale))
    if (a.ndim!=2 or len(a)<1 or a.shape[1]!=3 or b.shape!=a.shape or j.shape!=(len(a),3,27)
            or p.shape!=(27,) or s.shape!=(3,) or np.any(s<=0) or np.any(abs(p)>1)
            or any(not np.all(np.isfinite(v)) for v in (a,b,j,p,s))):
        raise ValueError('complete finite training values, all27 in-box coordinates and positive scales required')
    exact_point=list(map(lambda v:F(float(v)),p));linear_max=F(0);quadratic_max=F(0)
    for actual,base,jac in zip(a,b,j,strict=True):
        for value,origin,row,unit in zip(actual,base,jac,s,strict=True):
            linear=sum((F(float(c))*v for c,v in zip(row,exact_point,strict=True)),F(0))*F(float(unit))
            delta=(F(float(value))-F(float(origin)))*F(float(unit))
            linear_max=max(linear_max,abs(linear));quadratic_max=max(quadratic_max,abs(delta-linear))
    target=F(3,4);low=F(0);high=F(1)
    def envelope(x):return linear_max*x+quadratic_max*x*x
    if envelope(high)<=target:low=high
    for _ in range(48):
        middle=(low+high)/2
        if envelope(middle)<=target:low=middle
        else:high=middle
    represented=[float(low*v) for v in exact_point]
    if any(abs(v)>1 for v in represented):raise ValueError('represented point left physical box')
    return dict(point=represented,scale_exact=str(low),envelope_exact=str(envelope(low)),
        maximum_linear_training_m=str(linear_max),maximum_quadratic_training_m=str(quadratic_max),
        proposal_model='linear plus endpoint quadratic heuristic',proposal_target_m=.75,
        future_used_for_selection=False,nonlinear_feasibility_established=False,
        native_outcome_used_to_adjust_point=False)


def sampled_span(records):
    values=[[F(0)]*3];count=0
    for row in records:
        if not row.get('passed'):continue
        maxima=list(map(F,row['training_max_axis_exact']))
        future=list(map(F,row['future_change_exact']))
        if (len(maxima)!=3 or len(future)!=3 or min(maxima)<0
                or row.get('future_used_for_training_gate') is not False
                or row['nonlinear_training_feasible']!=all(v<=1 for v in maxima)):
            raise ValueError('actual training feasibility independent of future outcome required')
        if row['nonlinear_training_feasible']:values.append(future);count+=1
    lower=[min(v[i] for v in values) for i in range(3)];upper=[max(v[i] for v in values) for i in range(3)]
    widths=[b-a for a,b in zip(lower,upper)]
    return dict(feasible_points=count,width_m=list(map(float,widths)),width_exact=list(map(str,widths)),
        target_exceeded=[w>t for w,t in zip(widths,(20,20,50))],outer_enclosure=False,
        scope='sampled numerical spread including the zero-reference trajectory')


def evaluate(task,context):
    from pathlib import Path
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_density_native_probes import query,metrics
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    settings=runner._load(context.input_path());validate_recipe(settings);spec=task['payload']
    bundle=runner._load(context.input_path(spec['bundle_key']));project=context.root.parents[1]
    def read(reference):
        path=runner.path_within(project,reference['path'])
        if runner._sha(path)!=reference['sha256']:raise ValueError('sealed prerequisite changed')
        return runner._load(path)
    baseline=read(bundle['baseline']);previous=read(bundle['native']);old_point=read(bundle['point'])
    pointer=read(bundle['case_pointer']);filename=pointer['filename']
    if filename!=Path(filename).name:raise ValueError('qualified generated input filename required')
    path=project/'docs/ilvis0-recording-duration-controls/inputs'/filename
    if runner._sha(path)!=pointer['sha256']:raise ValueError('generated full input changed')
    case=runner._load(path);config=case['configuration']
    if (config['model']!=0 or config['profile']!=spec['profile'] or len(case['dt'])!=96000
            or config['limits'][25]!=1. or baseline['status']!=0 or previous['status']!=0):
        raise ValueError('unchanged generated full-history/reference inputs required')
    nominal=np.asarray(baseline['prediction'],float);jac=np.asarray(baseline['jacobian'],float)
    earlier=np.asarray(previous['prediction'],float)
    if nominal.shape!=(293,3) or earlier.shape!=nominal.shape or jac.shape!=(293,3,27):
        raise ValueError('all saved training and future epochs required')
    maximum=dict(proposals=1,training_column_products=23652,saved_training_checks=876,
        search_steps=48,point_checks=27,future_column_products=81,queried_epochs=293,position_checks=879)
    events=0
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:03d}.json',record)
    budget=Allowance(maximum,persist)
    budget.reserve(dict(proposals=1,training_column_products=23652,saved_training_checks=876,search_steps=48,point_checks=27))
    point=choose(earlier[:-1],nominal[:-1],jac[:-1],old_point['point'],spec['coordinate_scale'])
    context.save('point-before-native.json',point)
    budget.reserve(dict(future_column_products=81))
    represented=list(map(F,point['point']));scale=list(map(F,spec['coordinate_scale']))
    linear_future=[sum((F(float(c))*p for c,p in zip(row,represented,strict=True)),F(0))*unit
        for row,unit in zip(jac[-1],scale,strict=True)]
    context.save('future-linear-diagnostic.json',dict(change_exact=list(map(str,linear_future)),used_for_point_selection=False))
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if (metadata['compiler']!=spec['compiler'] or
            metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('frozen native source/compiler changed')
    context.save('kernel.json',metadata)
    def reserve(count,visits):
        budget.reserve(dict(queried_epochs=count));context.charge(native_calls=1,packet_visits=visits)
    times=list(map(float,range(2,294)))+[438.]
    native=query(kernel,config,theta,dv,dt,times,point['point'],reserve,
        lambda raw:context.save('native-raw.json',plain(raw)))
    context.save('native-boundary.json',native['classification']);budget.reserve(dict(position_checks=879))
    outcome=metrics(native['prediction'],nominal,spec['coordinate_scale'],list(map(str,linear_future)))
    context.save('nonlinear-comparison.json',outcome)
    if budget.counts!=maximum:raise ValueError('complete fixed ray accounting required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,model=0,profile=spec['profile'],axis=spec['axis'],sign=spec['sign'],
        physical_parameter_count=27,scale_exact=point['scale_exact'],**outcome,work=budget.counts,
        native_evaluations=1,training_epochs=292,queried_epochs=293,point_saved_before_native=True,
        original_reads=0,optimizer_starts=0,nonlinear_coverage_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
