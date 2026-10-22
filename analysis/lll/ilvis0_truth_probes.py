# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite ambiguity probes at the original long study's actual truth."""
from fractions import Fraction as F
import math


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
