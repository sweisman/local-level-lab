# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check fixed affine calibration proposals in the nonlinear generated model."""
from fractions import Fraction as F


def contracted_point(proposal,training,future):
    import numpy as np
    a=np.asarray(training,float);c=np.asarray(future,float)
    point=np.array([float(F(v)) for v in proposal])*0.99
    if (point.shape!=(27,) or a.ndim!=2 or a.shape[1]!=27 or not len(a) or c.shape!=(3,27)
            or any(not np.all(np.isfinite(v)) for v in (point,a,c)) or np.any(abs(point)>1.)):
        raise ValueError('complete finite 27-direction proposal and training/future rows required')
    exact=list(map(F,map(float,point)))
    change=[sum((F(float(v))*x for v,x in zip(row,exact,strict=True)),F(0)) for row in a]
    if max(map(abs,change))>1:raise ValueError('fixed represented contraction is not affine feasible')
    prediction=[sum((F(float(v))*x for v,x in zip(row,exact,strict=True)),F(0)) for row in c]
    return dict(point=point.tolist(),contraction=.99,affine_feasible=True,
        maximum_affine_training_change_m=str(max(map(abs,change))),
        linear_future_change_m=list(map(str,prediction)),adjusted_after_native_outcome=False)


def metrics(actual,baseline,scale,linear_future):
    import numpy as np
    values=np.asarray(actual,float);center=np.asarray(baseline,float);units=np.asarray(scale,float)
    if (values.ndim!=2 or values.shape!=center.shape or values.shape[1]!=3 or len(values)<2
            or units.shape!=(3,) or np.any(units<=0.) or len(linear_future)!=3
            or any(not np.all(np.isfinite(v)) for v in (values,center,units))):
        raise ValueError('complete finite earlier and future positions in a fixed frame required')
    change=[[(F(float(v))-F(float(b)))*F(float(s)) for v,b,s in zip(row,base,units,strict=True)]
        for row,base in zip(values,center,strict=True)]
    maxima=[max(abs(row[i]) for row in change[:-1]) for i in range(3)]
    return dict(nonlinear_training_feasible=all(v<=1 for v in maxima),
        training_max_axis_m=list(map(float,maxima)),training_max_axis_exact=list(map(str,maxima)),
        training_rms_axis_m=np.sqrt(np.mean(np.array(change[:-1],float)**2,axis=0)).tolist(),
        future_change_m=list(map(float,change[-1])),future_change_exact=list(map(str,change[-1])),
        future_linear_error_m=[float(v-F(p)) for v,p in zip(change[-1],linear_future,strict=True)],
        future_used_for_training_gate=False,training_allowance_m=1.)


def query(kernel,config,theta,dv,dt,times,point,reserve,save=lambda record:None):
    import ctypes
    import numpy as np
    from lll.ilvis0_training_density import boundary_count
    p=np.ascontiguousarray(point,float);t=np.ascontiguousarray(times,float)
    if p.shape!=(27,) or not np.all(np.isfinite(p)) or np.any(abs(p)>1.):
        raise ValueError('complete in-box physical calibration required')
    n=len(dt);m=len(t);reserve(m,n*m)
    out=np.empty((m,3));jac=np.empty((m,3,27));flag=ctypes.c_int()
    code=kernel(n,theta,dv,dt,m,t,config['initial_c'],config['initial_v'],config['initial_r'],
        config['limits'],p,config['model'],int(config['profile']),config['gravity'],config['radius'],
        out,jac,ctypes.byref(flag))
    raw=dict(status=int(code),counter=flag.value,point=p)
    if not code:raw.update(prediction=out,jacobian=jac)
    save(raw)  # Preserve unsuccessful native status before classifying it.
    classified=boundary_count(status=int(code),counter=flag.value,dt=dt,times=t+config['limits'][25]*p[25])
    if not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):raise ValueError('finite native output required')
    return dict(raw,classification=classified)


def evaluate(task,context):
    import importlib.util
    from pathlib import Path
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    from lll.ilvis0_training_density import recipe,validate_recipe
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    pointer=runner._load(context.input_path(spec['case_key']));name=pointer['filename']
    if name!=Path(name).name:raise ValueError('qualified input filename required')
    path=context.root.parents[1]/'docs/ilvis0-recording-duration-controls/inputs'/name
    if runner._sha(path)!=pointer['sha256']:raise ValueError('frozen generated input changed')
    case=runner._load(path);config=case['configuration'];baseline=runner._load(context.input_path(spec['baseline_key']))
    if (config['model']!=0 or config['profile']!=spec['profile'] or len(case['dt'])!=96000
            or config['limits'][25]!=1. or baseline['status']!=0 or not baseline['classification']['counter_verified']):
        raise ValueError('fixed full-history specified-field case and qualified baseline required')
    jac=np.asarray(baseline['jacobian'],float);nominal=np.asarray(baseline['prediction'],float)
    if jac.shape!=(293,3,27) or nominal.shape!=(293,3):raise ValueError('complete saved density baseline required')
    scale=np.array(spec['coordinate_scale']);a=(jac[:-1]*scale[None,:,None]).reshape(-1,27);c=jac[-1]*scale[:,None]
    events=0;maximum=dict(lp_proposals=1,exact_primal_checks=2,queried_epochs=293)
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:03d}.json',record)
    budget=Allowance(maximum,persist)
    helper=context.root/'source-freeze/docs/ilvis0-long-staged-feasibility-v2/audit_linear_leverage.py'
    loader=importlib.util.spec_from_file_location('_frozen_affine_probe',helper)
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    proposal=module.probe(a,c[spec['axis']],spec['sign'],1.,
        lambda:budget.reserve(dict(lp_proposals=1,exact_primal_checks=1)))
    context.save('affine-proposal.json',proposal)
    budget.reserve(dict(exact_primal_checks=1));point=contracted_point(proposal['point'],a,c)
    context.save('fixed-point-before-native.json',point)
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if metadata['compiler']!=spec['compiler'] or metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('frozen compiler/native source changed')
    context.save('kernel.json',metadata)
    def reserve(count,visits):
        budget.reserve(dict(queried_epochs=count));context.charge(native_calls=1,packet_visits=visits)
    native=query(kernel,config,theta,dv,dt,settings['dense_s']+[438.],point['point'],reserve,
        lambda raw:context.save('native-raw.json',plain(raw)))
    context.save('native-boundary.json',native['classification'])
    outcome=metrics(native['prediction'],nominal,scale,point['linear_future_change_m'])
    context.save('nonlinear-comparison.json',outcome)
    if budget.counts!=maximum:raise ValueError('complete fixed proposal/native accounting required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,model=0,profile=spec['profile'],axis=spec['axis'],sign=spec['sign'],
        affine_feasible=True,physical_parameter_count=27,training_epochs=292,queried_epochs=293,
        point_saved_before_native=True,native_evaluations=1,work=budget.counts,
        linear_future_change_m=list(map(lambda v:float(F(v)),point['linear_future_change_m'])),**outcome,
        original_reads=0,optimizer_starts=0,nonlinear_coverage_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
