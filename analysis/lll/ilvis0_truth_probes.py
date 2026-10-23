# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite ambiguity probes at the original long study's actual truth."""
from fractions import Fraction as F
import math


def audit_pair(problem,first,second):
    """Audit represented saved outputs; supplied error bounds need qualification.

    No forward calculation or search occurs here. Callers must separately verify
    artifact hashes, native execution and the stated numerical error bound.
    """
    def number(value):
        if isinstance(value,bool) or not isinstance(value,(int,float,F)):
            raise ValueError('finite represented numerical values required')
        try:return F(value)
        except (ValueError,OverflowError) as exc:
            raise ValueError('finite represented numerical values required') from exc
    def vector(value,size):
        if not isinstance(value,(list,tuple)) or len(value)!=size:
            raise ValueError('complete coordinate vector required')
        return list(map(number,value))
    def matrix(value,rows):
        if not isinstance(value,(list,tuple)) or len(value)!=rows:
            raise ValueError('complete epoch matrix required')
        return [vector(row,3) for row in value]
    try:
        binding=problem['binding']
        if (not isinstance(binding,dict) or binding.get('model') not in (0,1,2)
                or type(binding.get('model')) is not int or type(binding.get('profile')) is not bool):
            raise ValueError('explicit candidate and processing binding required')
        for key in ('case_sha256','source_sha256','configuration_sha256'):
            sha=binding[key]
            if not isinstance(sha,str) or len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('complete original source/configuration bindings required')
        times=list(map(number,problem['training_s']));n=len(times)
        future=number(problem['future_s'])
        if (not n or times[0]<0 or any(b<=a for a,b in zip(times,times[1:]))
                or future<=times[-1] or problem['future_observations_used'] is not False):
            raise ValueError('ordered earlier observations and unused future required')
        observed=matrix(problem['observations'],n);allowance=matrix(problem['allowance_m'],n)
        scale=vector(problem['coordinate_scale'],3);error=vector(problem['numerical_error_m'],3)
        targets=vector(problem['targets_m'],3)
        lower=vector(problem['physical_lower'],27);upper=vector(problem['physical_upper'],27)
        if (any(v<=0 for v in scale+targets) or any(v<0 for v in error)
                or any(v<0 for row in allowance for v in row)
                or any(a>b for a,b in zip(lower,upper,strict=True))):
            raise ValueError('valid bounds, scales, targets and nonnegative allowances required')
        values=[];margins=[]
        for record in (first,second):
            if (record['binding']!=binding or type(record['status']) is not int or record['status']!=0
                    or list(map(number,record['times_s']))!=times+[future]):
                raise ValueError('matching successful source, clock, frame and epoch outputs required')
            point=vector(record['point'],27)
            if any(x<a or x>b for x,a,b in zip(point,lower,upper,strict=True)):
                raise ValueError('all physical coordinates must satisfy the original bounds')
            predictions=matrix(record['prediction'],n+1);values.append(predictions)
            margins.append(min(allowance[i][j]-error[j]
                -abs(predictions[i][j]-observed[i][j])*scale[j]
                for i in range(n) for j in range(3)))
    except (KeyError,TypeError) as exc:
        raise ValueError('complete saved witness problem and records required') from exc
    feasible=[m>=0 for m in margins]
    separation=[max(F(0),abs(values[0][-1][j]-values[1][-1][j])*scale[j]-2*error[j])
        for j in range(3)]
    return dict(training_feasible=feasible,training_margin_exact=list(map(str,margins)),
        separation_lower_exact=list(map(str,separation)),
        separation_exceeds_target=[all(feasible) and v>t for v,t in zip(separation,targets,strict=True)],
        physical_parameter_count=27,training_epochs=n,future_observations_used=False,
        supplied_numerical_error_m=list(map(str,error)),
        source_hashes_independently_verified=False,native_execution_independently_verified=False,
        numerical_error_bound_independently_qualified=False,outer_bound_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def search_witness(problem,initial,oracle,*,sign,max_queries,reserve,save):
    """One bounded nonlinear proposal search; never an outer-range proof.

    ``oracle`` supplies native values and all 27 Jacobian columns. ``reserve``
    charges a new batch before execution; ``save`` preserves proposals and raw
    outputs. The caller owns source verification and a separate final replay.
    """
    import numpy as np
    from scipy.optimize import minimize
    if type(sign) is not int or sign not in (-1,1) or type(max_queries) is not int or not 1<=max_queries<=32:
        raise ValueError('one fixed direction and at most 32 search batches required')
    point=np.array(initial,float,copy=True)
    lower=np.asarray(problem['physical_lower'],float);upper=np.asarray(problem['physical_upper'],float)
    if (point.shape!=(27,) or lower.shape!=(27,) or upper.shape!=(27,)
            or not np.all(np.isfinite(point)) or np.any(point<lower) or np.any(point>upper)):
        raise ValueError('complete initial point inside original bounds required')
    times=list(problem['training_s'])+[problem['future_s']];n=len(times)-1
    schema=dict(binding=problem['binding'],times_s=times,point=point.tolist(),status=0,
        prediction=list(problem['observations'])+[[0.,0.,0.]])
    audit_pair(problem,schema,schema)  # Validate the schema, without a forward call.
    units=np.asarray(problem['coordinate_scale'],float)
    observed=np.asarray(problem['observations'],float)
    available=np.asarray(problem['allowance_m'],float)-np.asarray(problem['numerical_error_m'],float)-.01
    if np.any(available<0):raise ValueError('positive search margin inside supplied allowances required')
    cache={};count=0;best=None
    class QueryBudget(Exception):pass
    def query(p):
        nonlocal count,best
        p=np.array(p,float,copy=True)
        if p.shape!=(27,) or not np.all(np.isfinite(p)) or np.any(p<lower) or np.any(p>upper):
            raise ValueError('search proposed an invalid physical point; no clipping permitted')
        key=p.tobytes()
        if key in cache:return cache[key]
        if count>=max_queries:raise QueryBudget()
        reserve();count+=1
        save('proposal',dict(index=count,point=p.tolist(),saved_before_native=True))
        try:raw=oracle(p.copy())
        except Exception as exc:
            save('native-error',dict(index=count,error=type(exc).__name__,message=str(exc)));raise
        save('native',dict(index=count,output=raw))
        try:
            if type(raw['status']) is not int or raw['status']!=0:raise ValueError()
            value=np.array(raw['prediction'],float,copy=True);jac=np.array(raw['jacobian'],float,copy=True)
            if (value.shape!=(n+1,3) or jac.shape!=(n+1,3,27)
                    or not np.all(np.isfinite(value)) or not np.all(np.isfinite(jac))):raise ValueError()
        except (KeyError,TypeError,ValueError) as exc:
            raise ValueError('successful finite native values and all Jacobian columns required') from exc
        record=dict(binding=problem['binding'],times_s=times,point=p.tolist(),
            prediction=value.tolist(),status=0)
        check=audit_pair(problem,record,record)
        save('feasibility',dict(index=count,audit=check))
        if check['training_feasible'][0]:
            score=sign*value[-1,0]*units[0]
            if best is None or score>best['score']:
                best=dict(score=float(score),point=p.tolist(),record=record,
                    training_margin_exact=check['training_margin_exact'][0])
        cache[key]=(value,jac)
        return value,jac
    initial_value,_=query(point)
    if best is None:raise ValueError('the predeclared initial point must fit the actual training observations')
    base=initial_value[-1,0];target=float(problem['targets_m'][0])
    def objective(p):
        value,jac=query(p)
        return -sign*(value[-1,0]-base)*units[0]/target,-sign*jac[-1,0]*units[0]/target
    def constraints(p):
        value,_=query(p);delta=(value[:-1]-observed)*units
        return np.r_[(available-delta).ravel(),(available+delta).ravel()]
    def constraint_jacobian(p):
        _,jac=query(p);a=(jac[:-1]*units[None,:,None]).reshape(-1,27)
        return np.vstack([-a,a])
    try:
        result=minimize(objective,point,jac=True,method='SLSQP',bounds=list(zip(lower,upper,strict=True)),
            constraints=dict(type='ineq',fun=constraints,jac=constraint_jacobian),
            options=dict(ftol=1e-10,maxiter=32))
        stopping=str(result.message);optimizer_success=bool(result.success)
    except QueryBudget:
        stopping='native budget exhausted';optimizer_success=False
    return dict(native_queries=count,stopping_reason=stopping,optimizer_success=optimizer_success,
        best_point=best['point'],best_record=best['record'],best_training_feasible=True,
        best_training_margin_exact=best['training_margin_exact'],parameter_count=27,
        search_margin_m=.01,future_observations_used=False,outer_bound_qualified=False,
        numerical_error_bound_independently_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')


def recipe():
    return dict(packets=96000,training_s=[2.,10.,30.,180.,290.],future_s=438.,
        scales=['1/50','1/20','1/10'],direction_scale='1/2',training_allowance_m=1.,
        targets_m=[20.,20.,50.],lp_allowance_m=1.,physical_columns=27,
        nonlinear_optimizer_starts=0,original_reads=0)


def validate_recipe(value):
    if value!=recipe():raise ValueError('unchanged actual-fixture scope and original targets required')


def make_point(truth,proposal,scale):
    if (len(truth)!=27 or len(proposal)!=27 or scale not in recipe()['scales']
            or any(not math.isfinite(float(v)) for v in truth)):
        raise ValueError('all27 truth/direction coordinates and predeclared scale required')
    t=list(map(lambda v:F(float(v)),truth));z=list(map(F,proposal));alpha=F(scale)
    if any(abs(v)>1 for v in (*t,*z)):raise ValueError('truth and direction must be in their declared boxes')
    point=[float(v+F(1,2)*alpha*d) for v,d in zip(t,z,strict=True)]
    if any(abs(F(v))>1 for v in point):raise ValueError('represented point outside original physical box')
    return dict(point=point,original_truth=truth,scale_exact=scale,direction_scale_exact='1/2',
        physical_columns=27,clipped=False,point_saved_before_native=True)


def compare(actual,observations,truth_future,scale,linear_future):
    from lll.ilvis0_density_native_probes import metrics
    if len(actual)!=len(observations)+1:raise ValueError('training observations followed by one future epoch required')
    return metrics(actual,list(observations)+[truth_future],scale,linear_future)


def evaluate(task,context):
    import importlib.util
    import numpy as np
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_density_native_probes import query
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    maximum=dict(truth_checks=6,lp_proposals=1,exact_primal_checks=1,point_constructions=3,
        physical_point_checks=81,future_column_products=243,queried_epochs=18,nonlinear_position_checks=54)
    events=0
    def persist(record):
        nonlocal events
        runner._check_continue(context.root,context.manifest);events+=1
        context.save(f'reservation-{events:03d}.json',record)
    budget=Allowance(maximum,persist);budget.reserve(dict(truth_checks=6))
    bundle=runner._load(context.input_path(spec['bundle_key']));project=context.root.parents[1]
    def read(reference):
        path=runner.path_within(project,reference['path'])
        if runner._sha(path)!=reference['sha256']:raise ValueError('sealed actual-fixture input changed')
        return runner._load(path)
    case=read(bundle['case']);truth_records=[read(ref) for ref in bundle['truth_records']]
    observations=read(bundle['observations']);config=case['configuration']
    truth=truth_records[0]['point'];times=settings['training_s']+[settings['future_s']]
    if (len(case['dt'])!=96000 or config['model']!=0 or config['profile']!=spec['profile']
            or config['limits'][25]!=1. or len(truth_records)!=6 or max(map(abs,truth))>.5
            or observations['times_s']!=settings['training_s'] or observations['allowance_m']!=1.
            or observations['future_observations_used'] is not False
            or any(r['status']!=0 or r['point']!=truth or r['time_s']!=t for r,t in zip(truth_records,times,strict=True))):
        raise ValueError('original truth, perturbed observations and all six sealed tangents required')
    jac=np.asarray([r['jacobian'] for r in truth_records],float)
    if jac.shape!=(6,3,27):raise ValueError('all physical tangent columns required')
    units=np.asarray(spec['coordinate_scale']);a=(jac[:-1]*units[None,:,None]*.5).reshape(15,27)
    objective=jac[-1,0]*units[0]*.5
    path=context.root/'source-freeze/docs/ilvis0-long-staged-feasibility-v2/audit_linear_leverage.py'
    loader=importlib.util.spec_from_file_location('_truth_affine_proposal',path)
    helper=importlib.util.module_from_spec(loader);loader.loader.exec_module(helper)
    proposal=helper.probe(a,objective,spec['sign'],1.,
        lambda:budget.reserve(dict(lp_proposals=1,exact_primal_checks=1)))
    context.save('affine-proposal.json',proposal)
    budget.reserve(dict(point_constructions=3,physical_point_checks=81,future_column_products=243))
    points=[make_point(truth,proposal['point'],s) for s in settings['scales']]
    for point in points:
        delta=[F(v)-F(t) for v,t in zip(point['point'],truth,strict=True)]
        point['linear_future_change_m']=[str(sum((F(float(c))*p for c,p in zip(row,delta,strict=True)),F(0))*F(float(unit)))
            for row,unit in zip(jac[-1],units,strict=True)]
    context.save('all-points-before-native.json',dict(points=points,all_saved_before_outcomes=True))
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if (metadata['compiler']!=spec['compiler'] or
            metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('frozen native compiler/source changed')
    context.save('kernel.json',metadata)
    config={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'));candidates=[]
    def reserve(count,visits):
        budget.reserve(dict(queried_epochs=count));context.charge(native_calls=1,packet_visits=visits)
    for ordinal,point in enumerate(points):
        native=query(kernel,config,theta,dv,dt,times,point['point'],reserve,
            lambda raw:context.save(f'native-{ordinal:02d}.json',plain(raw)))
        context.save(f'boundary-{ordinal:02d}.json',native['classification'])
        budget.reserve(dict(nonlinear_position_checks=18))
        result=compare(native['prediction'],observations['observations'],truth_records[-1]['prediction'],
            units,point['linear_future_change_m'])
        candidate=dict(passed=True,scale_exact=point['scale_exact'],**result);candidates.append(candidate)
        context.save(f'comparison-{ordinal:02d}.json',candidate)
    if budget.counts!=maximum:raise ValueError('all fixed points, calls and auxiliary work required')
    context.save('accounting.json',budget.counts)
    return dict(identity=task['identity'],passed=True,profile=spec['profile'],sign=spec['sign'],model=0,
        candidates=candidates,physical_parameter_count=27,training_epochs=5,native_evaluations=3,queried_epochs=18,
        all_points_saved_before_outcomes=True,work=budget.counts,original_reads=0,optimizer_starts=0,
        original_observations_used=True,nonlinear_coverage_qualified=False,observational_coverage_qualified=False,
        scientific_decision='abstain')
