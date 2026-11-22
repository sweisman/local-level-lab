# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite exact earlier-position search at or above the X-bias boundary."""
import argparse
from contextlib import closing
import json
import math
from pathlib import Path
import sys

ID = 'esa-x-bias-nonlinear-range-v1'
BASE = 'docs/prediction-observed-development/'
PLAN = BASE+'ESA_X_BIAS_NONLINEAR_RANGE_PLAN.md'
RANGE = BASE+'esa-x-bias-range-position-result.json'
RANGE_SHA = '4cd344639b7068054fd51f22c28e5584513b090605cb9b7ef07d184e0dcc9969'
SCOPE = 'Earlier-only scalar replay and two bounded X-bias range adjustments'
MODEL = 'sphere_rotating'
CALLS,PACKETS,TRAIN,PREDICT = 7,155868,400,120
RADIUS = .05
SHARED = ('interval','training','forecast_times','recipe','environment','parent','frozen_python_native')
MODEL_INPUTS = ('fit','forecast','training_observations','compiler','weights','weights-receipt')
COMPANIONS = tuple('analysis/lll/'+name+'.py' for name in (
    'esa_tangent_remainder','esa_original_whitening','innovations_snapshot'))
INPUTS = (*SHARED,*MODEL_INPUTS,'proposal')


def local_proposal(point,residual,jacobian,lower):
    import numpy as np
    from scipy.optimize import lsq_linear

    point,r,j,lo = [np.asarray(value,float) for value in (point,residual,jacobian,lower)]
    if (point.ndim!=1 or lo.shape!=point.shape or j.shape!=(len(r),len(point))
            or np.any(point<lo) or np.any(point>1.)):
        raise ValueError('finite point within the declared calibration range required')
    lower_step = np.maximum(lo-point,-RADIUS)
    upper_step = np.minimum(1.-point,RADIUS)
    fitted = lsq_linear(j,-r,bounds=(lower_step,upper_step),
                        method='bvls',tol=1e-12,max_iter=100)
    proposed = np.clip(point+fitted.x,lo,1.)
    return dict(point=proposed.tolist(),settled=bool(fitted.success),iterations=int(fitted.nit))


def task():
    return dict(identity=MODEL,input_key='interval',native_kind='value',payload=dict(model=MODEL),
        limits=dict(native_calls=CALLS,packet_visits=CALLS*PACKETS*(TRAIN+PREDICT),
                    bound_calls=0,bound_steps=0))


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_x_bias_position_replay import ID as PARENT
    from .studies.artifacts import atomic,digest,encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('the exact nonlinear check is already frozen')
    reference = json.loads((root/RANGE).read_bytes())['result']
    if digest(encoded(reference))!=RANGE_SHA:
        raise ValueError('same sealed affine region result required')
    upper = next(row for row in reference['results'] if row['model']==MODEL)
    with closing(ClosedStudy(root,'data/'+PARENT)) as prior:
        if (prior.completion['state']!='complete' or not prior.rows[MODEL]['passed']
                or environment()!=prior.input('environment')):
            raise ValueError('same finished earlier replay and compiler required')
        materials = {name:prior.input(name,raw=True) for name in SHARED}
        materials.update({name:prior.input(MODEL+'-'+name,raw=True) for name in MODEL_INPUTS})
        materials['proposal'] = encoded(dict(parent_manifest_sha256=prior.completion['manifest_sha256'],
            boundary_mps2=reference['minimum_restricted_x_bias_mps2'],model=upper,
            range_sha256=RANGE_SHA))
    base.mkdir(parents=True)
    inputs = {'plan':PLAN}
    for name,payload in materials.items():
        path = base/name
        atomic(path,payload)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID,adapter=adapter,
        sources=source_closure(root,[adapter,PLAN,*COMPANIONS,
            'analysis/tests/test_esa_x_bias_nonlinear_range.py']),
        inputs=inputs,tasks=[task()],scope=SCOPE,workers=1,threads=1,maximum_wall_s=120.)
    atomic(base/'definition.json',encoded(definition))
    manifest = Definition.from_dict(definition,root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


def evaluate(declared,context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen

    if (context.manifest['scope']!=SCOPE or environment()!=json.loads(context.input_path('environment').read_bytes())
            or {k:v for k,v in declared.items() if k not in ('index','shard')}!=task()):
        raise ValueError('same earlier-only nonlinear replay required')
    raw = invoke_frozen(context,entry=Path(__file__),calls=CALLS,inputs=INPUTS,companions=COMPANIONS)
    result = json.loads(raw)
    if result['model']!=MODEL or len(result['checks'])!=CALLS-1:
        raise ValueError('complete finite earlier search required')
    context.save_bytes('nonlinear-x-range.json',raw)
    return dict(passed=True,**result)


def frozen_replay(inputs,output):
    import numpy as np
    from lll.esa_original_whitening import score_change
    from lll.esa_tangent_remainder import scalar_replay
    from lll.ilvis0_solver_position import physical_metric
    from lll.innovations_snapshot import restore
    from lll.studies.artifacts import encoded

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit,center,_,_,baseline,baseline_max,displacement = scalar_replay(inputs,output,expected_model=MODEL)
    saved,earlier,recipe,receipt,meta = (read(name) for name in (
        'forecast','training_observations','recipe','weights-receipt','proposal'))
    if (meta['range_sha256']!=RANGE_SHA or meta['model']['model']!=MODEL
            or meta['model']['parameter_names']!=fit['active_parameters']
            or recipe['limits']['accel_bias_x']!=.10):
        raise ValueError('unaltered affine proposal and original calibration parameters required')
    cached = restore(Path(inputs['weights']).read_bytes(),expected_sha256=receipt['snapshot_sha256'],
        expected_configuration=saved['error_training_configuration'],maximum_bytes=2**26)
    nominal = np.asarray(saved['training_coordinate_difference'])
    r0 = np.asarray(fit['local_linearization']['residual'])
    jac = np.asarray(fit['local_linearization']['jacobian'])
    if not np.array_equal(cached.whiten(nominal.ravel()),r0):
        raise ValueError('original earlier whitened residual did not replay')
    metric = physical_metric(np.asarray(earlier['coordinates']))
    axis = fit['active_parameters'].index('accel_bias_x')
    lo = -np.ones(len(center))
    lo[axis] = math.nextafter(meta['boundary_mps2']/.10,math.inf)

    def check(label,x):
        if np.any(x<lo) or np.any(x>1.):
            raise ValueError('trial left the remaining bias region')
        delta = (displacement(x)-baseline)[:TRAIN]
        change = cached.whiten(delta.ravel())
        loss = score_change(r0,change)
        raw_earlier = (nominal+delta)*metric
        return dict(label=label,point=x.tolist(),loss_increase=loss,
            original_allowance_met=loss<=.01,
            nonlinear_remainder_norm=float(np.linalg.norm(change-jac@(x-center))),
            horizontal_rms_m=float(np.linalg.norm(raw_earlier[:,:2])/math.sqrt(TRAIN)),
            height_rms_m=float(np.linalg.norm(raw_earlier[:,2])/math.sqrt(TRAIN))),r0+change

    only = center.copy()
    only[axis] = lo[axis]
    affine = np.clip(meta['model']['restricted_proposal'],lo,1.)
    candidates = [check('boundary_only',only),check('affine_proposal',affine)]
    steps = []
    for turn in (1,2):
        record,residual = min(candidates,key=lambda item:item[0]['loss_increase'])
        point = np.asarray(record['point'])
        proposal = local_proposal(point,residual,jac,lo)
        steps.append(proposal|dict(base=record['label']))
        delta = np.asarray(proposal['point'])-point
        candidates.extend(check(f'round_{turn}_{tag}',np.clip(point+s*delta,lo,1.))
                          for tag,s in (('half',.5),('full',1.)))
    reports = [row for row,_ in candidates]
    output.write_bytes(encoded(dict(model=MODEL,baseline_max_m=baseline_max,
        boundary_mps2=meta['boundary_mps2'],checks=reports,proposals=steps,
        best=min(reports,key=lambda row:row['loss_increase'])['label'],native_calls=CALLS,
        old_fit_resumed=False,later_receiver_reads=0,reserved_reads=0,
        whole_region_excluded=False,scientific_decision='abstain')))


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='_frozen':
        frozen_replay(json.loads(sys.argv[2]),Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action',choices=('prepare',))
        parser.parse_args()
        prepare(Path.cwd())
