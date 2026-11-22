# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the strongest linked ESA points in the archived integrating model."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
from io import BytesIO
import json
from pathlib import Path
import sys


ID = 'esa-linked-physical-replay-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_PHYSICAL_REPLAY_PLAN.md'
SCOPE = 'Archived scalar replay of the four strongest linked ESA calibration points'
LINKED_SHA = '6b79557383a7be83b2427a4f7afed2732307f26ee2ad711bfe97574c926fc530'
SCALAR_SHA = '199aa293a49cf8738c3f6161e78165fe10f948f0d1e3f36f156e62224d26ad60'
MODELS = ('sphere_still','flat_still')
GAMMAS = (0.,.1)
EARLIER, LATER, PACKETS = 400,120,155868
CALLS = 1+len(GAMMAS)


def tasks():
    return [dict(identity=model,input_key='interval',native_kind='value',payload=dict(model=model),
                 limits=dict(native_calls=CALLS,packet_visits=CALLS*PACKETS*(EARLIER+LATER),
                             bound_calls=0,bound_steps=0)) for model in MODELS]


def prepare(root):
    import numpy as np
    from .airquantumgrav_inventory import environment
    from .esa_calibration_witness import check_point
    from .esa_linked_physical_score import ID as LINKED
    from .esa_linked_training_support import projection_inputs
    from .ilvis0_coupled_map import restore_static_reference
    from .shape_remainder_witness import ID as SCALAR, SHARED, MODEL_INPUTS, COMPANIONS
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing linked replay freeze')
    materials = {}
    with ExitStack() as stack:
        linked = stack.enter_context(closing(ClosedStudy(root,'data/'+LINKED)))
        scalar = stack.enter_context(closing(ClosedStudy(root,'data/'+SCALAR,store=linked.store)))
        if (linked.completion['manifest_sha256']!=LINKED_SHA or not linked.summary['passed']
                or scalar.completion['manifest_sha256']!=SCALAR_SHA or not scalar.summary['passed']
                or scalar.input('environment')!=environment()
                or scalar.input('later-operator',raw=True)!=linked.input('later-operator',raw=True)):
            raise ValueError('exact linked search, scalar archive, score operator and environment required')
        materials.update({name:scalar.input(name,raw=True)
                          for name in (*SHARED,'shape-direction','later-operator')})
        shape = scalar.input('shape-direction')
        for model in MODELS:
            materials.update({model+'-'+name:scalar.input(model+'-'+name,raw=True)
                              for name in MODEL_INPUTS})
            if materials[model+'-weights']!=linked.input(model+'-weights',raw=True):
                raise ValueError('same original earlier whitening factors required')
            residual,raw,_,_,_,earlier,target,settings = projection_inputs(
                lambda name:linked.input(name,raw=True),model)
            if any(settings['shape'][key]!=shape[key] for key in
                   ('configuration','factors_sha256','direction','metric','nominal')):
                raise ValueError('unchanged saved shape direction required')
            with np.load(BytesIO(linked.input(model,raw=True)),allow_pickle=False) as data:
                coordinates = data['design']
            force, sample = (linked.input(model+suffix) for suffix in ('-force','-first-sample'))
            reference = restore_static_reference(force['configuration'],sample['dv'],sample['dt'],
                lower=force['lower'],upper=force['upper'],center=force['center'],
                expected_report=linked.input(model+'-reference'))
            if force['center']!=scalar.input(model+'-fit')['normalized_parameters']:
                raise ValueError('shared physical reference must use the original fit')
            rows = [(identity,linked.artifact(identity,'linked-points.json'))
                    for identity in linked.rows if linked.rows[identity]['identity'].startswith(model+'-')]
            probes, approximations = [], []
            for gamma in GAMMAS:
                identity, row = max(((i,r) for i,r in rows if r['earlier_unshared']==gamma),
                                   key=lambda item:item[1]['best']['score_lower'])
                best = row['best']
                point = np.asarray(best['point'])
                common = reference.normalized_values_at(point)
                vector = [*(F(x)-F(c) for x,c in zip(point,reference.parent.center,strict=True)),*common]
                checked = check_point(earlier,raw,residual,target,vector,unshared=gamma)
                if not checked['loss_passed'] or any(best[key]!=value for key,value in checked.items()):
                    raise ValueError('saved best linked score and loss must reproduce exactly')
                approximations.append((coordinates@np.asarray(vector,float)).reshape(EARLIER+LATER,3))
                probes.append(dict(gamma=gamma,source=identity,point=point.tolist(),linked=checked))
            payload = BytesIO()
            np.save(payload,np.asarray(approximations),allow_pickle=False)
            materials[model+'-approximations'] = payload.getvalue()
            materials[model+'-probes'] = encoded(probes)
    base.mkdir(parents=True)
    inputs = {'plan':PLAN}
    for name,payload in materials.items():
        path = base/name
        atomic(path,payload)
        inputs[name] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID,adapter=adapter,
        sources=source_closure(root,[adapter,PLAN,*COMPANIONS]),inputs=inputs,tasks=tasks(),
        scope=SCOPE,workers=2,threads=1,maximum_wall_s=120.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    from .esa_tangent_remainder import invoke_frozen
    from .shape_remainder_witness import SHARED, MODEL_INPUTS, COMPANIONS

    model = task['identity']
    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if (context.manifest['scope']!=SCOPE or declared not in tasks()
            or environment()!=json.loads(context.input_path('environment').read_bytes())):
        raise ValueError('exact scalar replay task and environment required')
    inputs = (*SHARED,'shape-direction','later-operator',
              *(model+'-'+name for name in (*MODEL_INPUTS,'probes','approximations')))
    raw = invoke_frozen(context,entry=Path(__file__),calls=CALLS,inputs=inputs,companions=COMPANIONS)
    result = json.loads(raw)
    if result['model']!=model or [r['gamma'] for r in result['checks']]!=list(GAMMAS):
        raise ValueError('both fixed replay checks required')
    context.save_bytes('linked-replay.json',raw)
    return dict(result,passed=True)


def score_replay(change, approximate, residual, earlier, later, metric, direction, *, split, sign):
    import numpy as np
    from lll.esa_original_whitening import score_change

    original = earlier.whiten(change[:split].ravel())
    remainder = earlier.whiten((change-approximate)[:split].ravel())

    def projected(values):
        return sign*float(direction@later.whiten((values*metric).ravel())[3*split:])

    loss = score_change(residual,original)
    return dict(full_loss_increase=loss,original_loss_passed=loss<=.01,
                earlier_unshared_norm=float(np.linalg.norm(remainder)),
                full_score=projected(change),linked_score=projected(approximate),
                later_signed_unshared=projected(change-approximate))


def frozen_replay(inputs,output):
    import numpy as np
    from lll.esa_tangent_remainder import scalar_replay
    from lll.innovations_snapshot import restore
    from lll.studies.artifacts import encoded

    model, = [m for m in MODELS if m+'-fit' in inputs]
    inputs.update({name[len(model)+1:]:value for name,value in inputs.copy().items()
                   if name.startswith(model+'-')})

    def read(name):
        return json.loads(Path(inputs[name]).read_bytes())

    fit, _, _, _, baseline, baseline_max, displacement = scalar_replay(inputs,output,expected_model=model)
    shape = read('shape-direction')
    earlier = restore(Path(inputs['weights']).read_bytes(),
        expected_sha256=read('weights-receipt')['snapshot_sha256'],
        expected_configuration=read('forecast')['error_training_configuration'],maximum_bytes=2**26)
    later = restore(Path(inputs['later-operator']).read_bytes(),expected_sha256=shape['factors_sha256'],
                    expected_configuration=shape['configuration'],maximum_bytes=2**26)
    approximations = np.load(inputs['approximations'],allow_pickle=False)
    probes = read('probes')
    if (approximations.shape!=(len(GAMMAS),EARLIER+LATER,3)
            or not np.isfinite(approximations).all() or [p['gamma'] for p in probes]!=list(GAMMAS)):
        raise ValueError('all and only frozen linked points required')
    residual = np.asarray(fit['local_linearization']['residual'])
    checks = []
    for probe,approximate in zip(probes,approximations,strict=True):
        point = np.asarray(probe['point'])
        if point.shape!=(27,) or np.any(abs(point)>1.) or not np.isfinite(point).all():
            raise ValueError('finite physical replay point inside the original calibration box required')
        measured = score_replay(displacement(point)-baseline,approximate,residual,earlier,later,
            np.asarray(shape['metric']),np.asarray(shape['direction']),split=EARLIER,
            sign=1 if model==MODELS[0] else -1)
        checks.append(dict(probe,**measured))
    output.write_bytes(encoded(dict(model=model,baseline_scalar_max_m=baseline_max,checks=checks,
        fit_starts=0,later_receiver_positions_read=0,protected_reads=0,scientific_decision='abstain')))


if __name__ == '__main__':
    if len(sys.argv)==4 and sys.argv[1]=='_frozen':
        frozen_replay(json.loads(sys.argv[2]),Path(sys.argv[3]))
    else:
        prepare(Path.cwd())
