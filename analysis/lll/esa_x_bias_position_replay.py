# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the reversing X accelerometer correction in the original earlier fits."""
import argparse
from contextlib import closing
import json
from pathlib import Path
import sys

ID = 'esa-x-bias-position-replay-v1'
PLAN = 'docs/prediction-observed-development/ESA_X_BIAS_POSITION_REPLAY_PLAN.md'
SCOPE = 'No-refit ESA X accelerometer bias endpoint and bounded affine compensation'
SHARED = ('interval','training','forecast_times','recipe','environment','parent','frozen_python_native')
MODELS = ('sphere_rotating','sphere_still','flat_still')
MODEL_INPUTS = ('fit','forecast','training_observations','compiler','weights','weights-receipt')
COMPANIONS = tuple('analysis/lll/'+name+'.py' for name in (
    'esa_tangent_remainder','esa_original_whitening','innovations_snapshot'))
TRAIN,PREDICT,PACKETS = 400,120,155868
CALLS = 3
EXACT_ALLOWANCE = .01


def endpoint_proposal(point,residual,jacobian,axis):
    """Propose a compensating point in the original normalized box."""
    import numpy as np
    from scipy.optimize import lsq_linear
    from lll.esa_original_whitening import score_change

    point,residual,jacobian = [np.asarray(value,float) for value in (point,residual,jacobian)]
    if (point.ndim!=1 or residual.ndim!=1 or jacobian.shape!=(len(residual),len(point))
            or len(point)<2 or not 0<=axis<len(point)
            or not all(np.isfinite(a).all() for a in (point,residual,jacobian))
            or np.any(abs(point)>1.)):
        raise ValueError('finite saved loss and normalized calibration box required')
    fixed = point.copy()
    fixed[axis] = 1.
    active = np.arange(len(point))!=axis
    initial_change = jacobian@(fixed-point)
    adjusted = lsq_linear(jacobian[:,active], -residual-initial_change,
        bounds=(-1.-point[active],1.-point[active]),method='bvls',tol=1e-12,max_iter=100)
    proposed = fixed.copy()
    proposed[active] = np.clip(point[active]+adjusted.x,-1.,1.)
    return dict(fixed=fixed.tolist(),proposed=proposed.tolist(),settled=bool(adjusted.success),
                iterations=int(adjusted.nit),affine_loss_increase=score_change(
                    residual,jacobian@(proposed-point)),
                fixed_affine_loss_increase=score_change(residual,initial_change))


def tasks():
    return [dict(identity=model,input_key='interval',native_kind='value',payload=dict(model=model),
        limits=dict(native_calls=CALLS,packet_visits=CALLS*PACKETS*(TRAIN+PREDICT),
                    bound_calls=0,bound_steps=0)) for model in MODELS]


def prepare(root):
    from .airquantumgrav_inventory import environment
    from .esa_calibration_contrast import WEIGHTS, WEIGHTS_SHA
    from .esa_conditional_forecast_study import require_guarded_environment
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('the frozen replay already exists')
    materials = {}
    with closing(ClosedStudy(root,WEIGHTS)) as prior:
        if (prior.completion['manifest_sha256']!=WEIGHTS_SHA
                or prior.completion['state']!='complete'
                or not all(prior.rows[model]['passed'] for model in MODELS)
                or prior.input('environment')!=require_guarded_environment(environment())
                or prior.input('recipe')['limits']['accel_bias_x']!=.10):
            raise ValueError('original three covariance receipts and X bias allowance required')
        materials.update({name:prior.input(name,raw=True) for name in SHARED})
        for model in MODELS:
            materials.update({model+'-'+name:prior.input(model+'-'+name,raw=True)
                              for name in MODEL_INPUTS[:4]})
            receipt = prior.artifact(model,'exact-earlier-cost.json')
            weights = prior.artifact(model,'training-factors.npz',raw=True)
            if digest(weights)!=receipt['snapshot_sha256']:
                raise ValueError('exact archived whitening factors required')
            materials[model+'-weights'] = weights
            materials[model+'-weights-receipt'] = encoded(receipt)
    base.mkdir(parents=True)
    inputs = {'plan':PLAN}
    for name,payload in materials.items():
        path = base/name
        atomic(path,payload)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID,adapter=adapter,
        sources=source_closure(root,[adapter,PLAN,*COMPANIONS,
            'analysis/tests/test_esa_x_bias_position_replay.py']),
        inputs=inputs,tasks=tasks(),scope=SCOPE,workers=1,threads=1,maximum_wall_s=180.)
    atomic(base/'definition.json',encoded(definition))
    manifest = Definition.from_dict(definition,root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen

    model = task['identity']
    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if (context.manifest['scope']!=SCOPE or declared not in tasks()
            or environment()!=json.loads(context.input_path('environment').read_bytes())):
        raise ValueError('exact X bias replay task and original environment required')
    inputs = (*SHARED,*(model+'-'+name for name in MODEL_INPUTS))
    data = invoke_frozen(context,entry=Path(__file__),calls=CALLS,inputs=inputs,companions=COMPANIONS)
    outcome = json.loads(data)
    if outcome['model']!=model or set(outcome['checks'])!={'fixed','compensated'}:
        raise ValueError('both endpoint replays were required')
    context.save_bytes('x-bias-replay.json',data)
    return dict(outcome,passed=True)


def frozen_replay(inputs,output):
    import numpy as np
    from lll.esa_original_whitening import score_change
    from lll.esa_tangent_remainder import scalar_replay
    from lll.ilvis0_solver_position import physical_metric
    from lll.innovations_snapshot import restore
    from lll.studies.artifacts import encoded

    model, = [m for m in MODELS if m+'-fit' in inputs]
    inputs.update({name[len(model)+1:]:value for name,value in inputs.copy().items()
                   if name.startswith(model+'-')})

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit, point, _, _, baseline, baseline_max, displacement = scalar_replay(
        inputs,output,expected_model=model)
    forecast = read('forecast')
    earlier = read('training_observations')
    receipt = read('weights-receipt')
    covariance = restore(Path(inputs['weights']).read_bytes(),expected_sha256=receipt['snapshot_sha256'],
        expected_configuration=forecast['error_training_configuration'],maximum_bytes=2**26)
    nominal = np.asarray(forecast['training_coordinate_difference'])
    local = fit['local_linearization']
    residual = np.asarray(local['residual'])
    if not np.array_equal(covariance.whiten(nominal.ravel()),residual):
        raise ValueError('sealed earlier residual did not reproduce')
    axis = fit['active_parameters'].index('accel_bias_x')
    proposal = endpoint_proposal(point,residual,local['jacobian'],axis)
    metric = physical_metric(np.asarray(earlier['coordinates']))
    checks = {}
    for label,name in (('fixed','fixed'),('compensated','proposed')):
        target = np.asarray(proposal[name])
        if target[axis]!=1.:
            raise ValueError('X accelerometer bias was moved during compensation')
        offsets = (displacement(target)-baseline)[:TRAIN]
        loss = score_change(residual,covariance.whiten(offsets.ravel()))
        position_error = (nominal+offsets)*metric
        earlier_metrics = dict(horizontal_rms_m=float(np.linalg.norm(position_error[:,:2])/np.sqrt(TRAIN)),
                               vertical_rms_m=float(np.linalg.norm(position_error[:,2])/np.sqrt(TRAIN)))
        checks[label] = dict(loss_increase=loss,within_original_loss_allowance=loss<=EXACT_ALLOWANCE,
                            earlier_metrics=earlier_metrics,normalized_point=target.tolist())
    output.write_bytes(encoded(dict(model=model,nominal_x_bias_mps2=float(.10*point[axis]),
        baseline_replay_max_m=baseline_max,nominal_earlier_squared_loss=float(residual@residual),
        earlier_loss_allowance=EXACT_ALLOWANCE,proposal=proposal,checks=checks,
        original_parameter_names=fit['active_parameters'],new_full_fits=0,
        later_receiver_reads=0,reserved_reads=0,scientific_decision='abstain')))


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='_frozen':
        frozen_replay(json.loads(sys.argv[2]),Path(sys.argv[3]))
    else:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('action',choices=('prepare',))
        parser.parse_args()
        prepare(Path.cwd())
