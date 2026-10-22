# SPDX-License-Identifier: AGPL-3.0-or-later
"""One fixed linear repair of generated training ambiguity probes."""
from fractions import Fraction as F
import numpy as np


def recipe():
    return dict(packets=96000,training_s=[2.,10.,30.,180.,290.],future_s=438.,
        seed_scale='1/10',linear_solves_per_case=1,native_calls_per_case=1,
        rank_rcond=1e-12,maximum_correction=.25,linear_tolerance_m=.001,
        training_allowance_m=1.,targets_m=[20.,20.,50.],physical_columns=27,
        future_prediction_constraint_used=True,future_observations_used=False,
        original_reads=0,optimizer_starts=0)


def validate_recipe(value):
    if value!=recipe():raise ValueError('fixed one-repair generated-data recipe required')


def repair(point,prediction,jacobian,training_truth,scale):
    p=np.asarray(point,float);v=np.asarray(prediction,float);j=np.asarray(jacobian,float)
    truth=np.asarray(training_truth,float);units=np.asarray(scale,float)
    if (p.shape!=(27,) or v.shape!=(6,3) or j.shape!=(6,3,27) or truth.shape!=(5,3)
            or units.shape!=(3,) or np.any(units<=0) or np.any(abs(p)>1)
            or any(not np.all(np.isfinite(x)) for x in (p,v,j,truth,units))):
        raise ValueError('all27 finite columns, six predictions, five training targets and positive scales required')
    settings=recipe();matrix=np.vstack(((j[:5]*units[None,:,None]).reshape(15,27),j[5,0]*units[0]))
    target=np.r_[((truth-v[:5])*units).ravel(),0.]
    correction,_,rank,singular=np.linalg.lstsq(matrix,target,rcond=settings['rank_rcond'])
    candidate=p+correction;residual=matrix@correction-target
    maximum=float(np.max(abs(residual)));size=float(np.max(abs(correction)))
    valid=bool(np.all(np.isfinite(candidate)) and np.all(abs(candidate)<=1)
        and size<=settings['maximum_correction'] and maximum<=settings['linear_tolerance_m'])
    return dict(point=candidate.tolist(),correction=correction.tolist(),rank=int(rank),
        singular_values=singular.tolist(),maximum_linear_residual_m=maximum,maximum_correction=size,
        proposal_valid=valid,clipped=False,physical_columns=27,linear_rows=16,linear_solves=1,
        future_prediction_constraint_used=True,future_observations_used=False,
        nonlinear_feasibility_established=False)


def evaluate(task,context):
    from lll import ilvis0_control_shards as runner
    from lll.ilvis0_density_native_probes import query
    from lll.ilvis0_truth_probes import compare
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    spec=task['payload'];settings=runner._load(context.input_path());validate_recipe(settings)
    pointer=runner._load(context.input_path(spec['bundle_key']));project=context.root.parents[1]
    def read(ref):
        path=runner.path_within(project,ref['path'])
        if runner._sha(path)!=ref['sha256']:raise ValueError('sealed generated reference changed')
        return runner._load(path)
    bundle=read(pointer['original_bundle']);case=read(bundle['case']);seed=read(pointer['seed'])
    truth=[read(ref) for ref in bundle['truth_records']];observations=read(bundle['observations'])
    config=case['configuration'];times=settings['training_s']+[settings['future_s']]
    if (len(case['dt'])!=96000 or config['model']!=0 or config['profile']!=spec['profile']
            or seed['status']!=0 or len(truth)!=6 or any(r['status']!=0 or r['time_s']!=t
                for r,t in zip(truth,times,strict=True))
            or observations['times_s']!=settings['training_s'] or observations['allowance_m']!=1.
            or observations['future_observations_used'] is not False):
        raise ValueError('original generated history, truth and actual training observations required')
    proposal=repair(seed['point'],seed['prediction'],seed['jacobian'],
        [r['prediction'] for r in truth[:5]],spec['coordinate_scale'])
    context.save('proposal-before-native.json',proposal)
    base=dict(identity=task['identity'],passed=True,model=0,profile=spec['profile'],sign=spec['sign'],
        physical_parameter_count=27,linear_solves=1,proposal_valid=proposal['proposal_valid'],
        original_observations_used=True,future_observations_used=False,future_prediction_constraint_used=True,
        original_reads=0,optimizer_starts=0,nonlinear_coverage_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if not proposal['proposal_valid']:
        return dict(base,native_evaluations=0,candidate=None)
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_tangent(directory)
    if (metadata['compiler']!=spec['compiler'] or
            metadata['source_sha256']!=context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']):
        raise ValueError('frozen native source/compiler changed')
    context.save('kernel.json',metadata)
    arrays={k:np.ascontiguousarray(v,float) if k in ('initial_c','initial_v','initial_r','limits') else v
        for k,v in config.items()}
    theta,dv,dt=(np.ascontiguousarray(case[k],float) for k in ('theta','dv','dt'))
    native=query(kernel,arrays,theta,dv,dt,times,proposal['point'],
        lambda count,visits:context.charge(native_calls=1,packet_visits=visits),
        lambda record:context.save('native.json',plain(record)))
    context.save('boundary.json',native['classification'])
    if native['status']!=0:raise ValueError('successful native output required')
    future=[str((F(float(v))-F(float(t)))*F(float(s))) for v,t,s in
        zip(seed['prediction'][-1],truth[-1]['prediction'],spec['coordinate_scale'],strict=True)]
    candidate=compare(native['prediction'],observations['observations'],truth[-1]['prediction'],
        spec['coordinate_scale'],future)
    context.save('comparison.json',candidate)
    return dict(base,native_evaluations=1,candidate=candidate)
