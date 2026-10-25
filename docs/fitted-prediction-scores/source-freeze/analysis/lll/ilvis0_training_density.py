# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full-history training-density diagnostics, not nonlinear prediction coverage."""
from fractions import Fraction as F


def recipe():
    return dict(packets=96000,dense_s=list(map(float,range(2,294))),sparse_s=[2.,10.,30.,180.,290.],
        future_s=438.,center=[0.]*27,clock_limit_s=1.,training_allowance_m=1.,targets_m=[20.,20.,50.])


def validate_recipe(value):
    if value!=recipe():raise ValueError('unchanged full-history density recipe required')


def boundary_count(*,status,counter,dt,times):
    import numpy as np
    periods=np.asarray(dt,float);queries=np.asarray(times,float)
    if (status!=0 or type(counter) is not int or periods.ndim!=1 or not len(periods)
            or queries.ndim!=1 or not len(queries) or not np.all(np.isfinite(periods))
            or not np.all(np.isfinite(queries)) or np.any(periods<=0.) or np.any(np.diff(queries)<=0.)
            or queries[0]<0. or not 0<=counter<=len(queries)):
        raise ValueError('successful ordered native batch and complete timestamps required')
    ends=np.cumsum(periods);indices=np.searchsorted(ends,queries,side='left')
    if np.any(indices>=len(ends)):raise ValueError('query outside full input support')
    starts=np.r_[0.,ends[:-1]];fractions=(queries-starts[indices])/periods[indices]
    if np.any(fractions< -1e-10) or np.any(fractions>1.+1e-10):raise ValueError('invalid batch fraction')
    expected=int(np.sum((fractions<1e-8)|(fractions>1.-1e-8)))
    if counter!=expected:raise ValueError('aggregate packet-boundary counter mismatch')
    return dict(counter_verified=True,expected_counter=expected,query_count=len(queries),
        derivative_smoothness_qualified=False)


def native_batch(kernel,config,theta,dv,dt,times,reserve):
    import ctypes
    import numpy as np
    n=len(dt);m=len(times);reserve(m,n*m)
    out=np.empty((m,3));jac=np.empty((m,3,27));flag=ctypes.c_int()
    code=kernel(n,theta,dv,dt,m,np.ascontiguousarray(times,float),config['initial_c'],config['initial_v'],
        config['initial_r'],config['limits'],np.zeros(27),config['model'],int(config['profile']),
        config['gravity'],config['radius'],out,jac,ctypes.byref(flag))
    classification=boundary_count(status=int(code),counter=flag.value,dt=dt,times=times)
    if not np.all(np.isfinite(out)) or not np.all(np.isfinite(jac)):raise ValueError('finite full native batch required')
    return dict(prediction=out,jacobian=jac,status=int(code),counter=flag.value,classification=classification)


def affine_ranges(training,future,allowance,reserve):
    import numpy as np
    from lll.ilvis0_affine_support import propose
    from lll.ilvis0_saved_prediction_audit import support
    a=np.asarray(training,float);f=np.asarray(future,float)
    if a.ndim!=2 or f.shape!=(3,a.shape[1]) or not 1<=a.shape[1]<=27 or not len(a) or allowance<=0:
        raise ValueError('complete training and three future physical rows required')
    n=a.shape[1];design=np.r_[a,-a].tolist();right=[float(allowance)]*len(design)
    lo=[-1.]*n;hi=[1.]*n;axes=[]
    for row in f.tolist():
        saved=[]
        for sign in (1,-1):
            objective=[sign*v for v in row];reserve(1,3)
            certificate=propose(lo,hi,design,right,objective);weights=certificate['multipliers'].tolist()
            exact=support(lo,hi,design,right,objective,weights)
            if exact!=certificate['exact_upper']:raise ValueError('independent exact support disagrees')
            saved.append(dict(exact_upper=str(exact),multipliers=weights,proposal_used=certificate['proposal_used']))
        axes.append(dict(lower_m=str(-F(saved[1]['exact_upper'])),upper_m=saved[0]['exact_upper'],
            width_m=str(F(saved[0]['exact_upper'])+F(saved[1]['exact_upper'])),certificates=saved))
    return dict(axes=axes,physical_parameter_count=n,training_epochs=len(a)//3,
        nonlinear_coverage_qualified=False)


def evaluate(task,context):
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    pointer=runner._load(context.input_path(spec['case_key']));name=pointer['filename']
    if name!=__import__('pathlib').Path(name).name:raise ValueError('one qualified input filename required')
    project=context.root.parents[1]
    path=project/'docs/ilvis0-recording-duration-controls/inputs'/name
    if runner._sha(path)!=pointer['sha256']:raise ValueError('hash-referenced frozen input changed')
    case=runner._load(path);config=case['configuration']
    if (len(case['dt'])!=96000 or config['limits'][25]!=1. or case['center']!=[0.]*27
            or config['model']!=spec['model'] or config['profile']!=spec['profile']):
        raise ValueError('qualified full input and physical settings required')
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    maximum=dict(queried_epochs=294,lp_proposals=12,exact_supports=36);events=0
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:03d}.json',record)
    budget=Allowance(maximum,persist)
    def reserve_native(queries,visits):
        budget.reserve(dict(queried_epochs=queries));context.charge(native_calls=1,packet_visits=visits)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if metadata['compiler']!=spec['compiler'] or metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']:
        raise ValueError('frozen native source/compiler mismatch')
    context.save('kernel.json',metadata)
    times=settings['dense_s']+[settings['future_s']]
    batch=native_batch(kernel,config,theta,dv,dt,times,reserve_native)
    context.save('native-batch.json',plain(batch))
    single=native_batch(kernel,config,theta,dv,dt,[settings['future_s']],reserve_native)
    context.save('native-endpoint.json',plain(single))
    if (not np.array_equal(batch['prediction'][-1],single['prediction'][0])
            or not np.array_equal(batch['jacobian'][-1],single['jacobian'][0])):
        raise ValueError('batch endpoint or physical derivative column changed')
    scale=np.array(spec['coordinate_scale']);jac=batch['jacobian']*scale[None,:,None]
    indices=[settings['dense_s'].index(v) for v in settings['sparse_s']];ranges={}
    for name,selected in (('sparse',indices),('dense',list(range(292)))):
        a=jac[selected].reshape(-1,27);future=jac[-1]
        result=affine_ranges(a,future,settings['training_allowance_m'],
            lambda p,s:budget.reserve(dict(lp_proposals=p,exact_supports=s)))
        ranges[name]=result;context.save(name+'-support.json',result)
    # Intersection retains both sets of verified certificates. The denser
    # constraints contain every sparse row; a poor new dual cannot widen them.
    widths=[]
    for old,new in zip(ranges['sparse']['axes'],ranges['dense']['axes'],strict=True):
        widths.append(min(F(old['upper_m']),F(new['upper_m']))-max(F(old['lower_m']),F(new['lower_m'])))
    if any(v<0 for v in widths) or budget.counts!=maximum:raise ValueError('nested exact ranges/accounting required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],
        physical_parameter_count=27,dense_epochs=292,sparse_epochs=5,batch_endpoint_bitwise=True,
        sparse_width_m=[float(F(a['width_m'])) for a in ranges['sparse']['axes']],
        dense_width_m=list(map(float,widths)),targets_m=settings['targets_m'],
        linear_width_useful=all(v<=F(t) for v,t in zip(widths,settings['targets_m'],strict=True)),
        native_evaluations=2,queried_epochs=294,work=budget.counts,original_reads=0,optimizer_starts=0,
        nonlinear_coverage_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
