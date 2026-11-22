# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recompute forecast score bounds in the nine surviving ESA ranges."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_attitude_cover_score import GAMMA, INCREASE


ID = 'esa-attitude-survivor-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_ATTITUDE_SURVIVOR_SCORE_PLAN.md'
SCOPE = 'Scaled score proposals for the nine high-bound survivors of the ESA feasibility check'
PARENT_SHA = '7b7b5d87b167ec2b78a0df4404bf353550078afb161739cfd13bad6492b1a393'
RANGES = {'sphere_still': ((4,1),(5,1),(6,0),(7,0)),
          'flat_still': ((0,3),(1,3),(2,2),(2,3),(3,2))}
ROUNDS = 3
STEPS = 6
ITERATIONS = 180
FRACTIONS = (1., .999, .95)


def tasks():
    return [dict(identity=f'{model}-{parent}-{child}',input_key=model,
                 payload=dict(model=model,parent=parent,child=child),
                 limits=dict(native_calls=0,packet_visits=0,bound_calls=ROUNDS,bound_steps=ROUNDS*STEPS))
            for model,indices in RANGES.items() for parent,child in indices]


def evaluate(task, context):
    import numpy as np
    from .esa_calibration_witness import check_point
    from .esa_direct_training_score import feasible_box_and_cuts
    from .esa_linked_training_support import load_projection_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_coupled_training_score import certify, direct_proposal, tangent_proposal
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals

    declared = {k:v for k,v in task.items() if k not in ('shard','index')}
    if context.manifest['scope']!=SCOPE or declared not in tasks():
        raise ValueError('exact saved survivor-score task required')
    identity, model = task['identity'],task['payload']['model']
    box = json.loads(context.input_path(identity+'-domain').read_bytes())
    prior = json.loads(context.input_path(identity+'-feasibility').read_bytes())
    anchors = json.loads(context.input_path(identity+'-anchors').read_bytes())
    residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context,model)
    if (prior['excluded'] or prior['retained_upper']!=box['previous_upper']
            or box['nominal_separation']!=settings['shape']['nominal'] or len(box['static'])!=270):
        raise ValueError('retained original box and score direction required')
    extra = np.zeros((len(residual),9))
    raw, design = np.c_[raw,extra], np.c_[design,extra]
    target = target+((F(0),F(0)),)*9
    objective = np.array([float((a+b)/2) for a,b in target])
    lower, upper = np.asarray(box['lower']),np.asarray(box['upper'])
    static, limits = box['static'],box['limits']
    minimum = prior['trials'][-1]
    if minimum['method']!='earlier_loss':
        raise ValueError('saved minimum-loss proposal required')
    start = np.clip(minimum['point'],lower,upper)
    if minimum['checked_point'] is not None and minimum['checked_point']['loss_passed']:
        anchors.append(dict(point=[str(F(v)) for v in start],score_lower=None))
    known = max(anchors,key=lambda r:r['score_lower'] if r['score_lower'] is not None else -float('inf'),
                default=None)
    anchor = tuple(map(F,known['point'])) if known is not None else None
    if anchor is not None and not feasible_box_and_cuts(anchor,lower,upper,static,limits):
        raise ValueError('verified anchor changed')
    alternate = np.asarray(anchor,float) if anchor is not None else (lower+upper)/2
    radius = sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))+GAMMA
    best_upper = F(box['previous_upper'])
    best_lower = known['score_lower'] if known is not None else None
    rows = []
    for name, point in (('minimum-loss tangent',start),('direct from minimum loss',start),
                        ('direct from alternate',alternate)):
        context.charge(bound_calls=1,bound_steps=STEPS)
        if name=='minimum-loss tangent':
            proposal = tangent_proposal(design,residual,lower,upper,objective,static,limits,
                                        radius=radius,point=point,scaled=True)
            proposal.update(point=point,iterations=0,success=None)
        else:
            proposal = direct_proposal(design,residual,lower,upper,objective,static,limits,
                                       radius=radius,start=point,iterations=ITERATIONS,scaled_tangent=True)
        direction, weights = proposal['direction'],proposal['weights']
        lo, hi = adjoint_intervals(earlier,direction)
        projected = coefficients(lo,hi,np.ones(len(residual)),raw)
        train = tuple(zip(projected['lower'],projected['upper'],strict=True))
        bound = certify(residual,direction,train,target,lower,upper,static,limits,weights,
                        increase=INCREASE,unshared=GAMMA)
        best_upper = min(best_upper,bound)
        proposed = tuple(map(F,proposal['point']))
        checks = []
        for amount in FRACTIONS if anchor is not None else (1.,):
            evaluated = (tuple(a+F(amount)*(v-a) for a,v in zip(anchor,proposed,strict=True))
                         if anchor is not None else proposed)
            box_ok = feasible_box_and_cuts(evaluated,lower,upper,static,limits)
            measured = check_point(earlier,raw,residual,target,evaluated,unshared=GAMMA) if box_ok else {}
            checks.append(dict(fraction=amount,static_passed=box_ok,**measured))
            if measured.get('loss_passed'):
                value = measured['score_lower']
                best_lower = value if best_lower is None else max(best_lower,value)
                break
        rows.append(dict(method=name,exact_upper=str(bound),checks=checks,
                         point=proposal['point'].tolist(),direction=direction.tolist(),weights=weights.tolist(),
                         iterations=proposal['iterations'],success=proposal['success'],
                         tangent_proposed=proposal['tangent_proposed']))
    if best_lower is not None and F(best_lower)>best_upper:
        raise ValueError('certified score upper bound contradicts a verified feasible point')
    result = dict(upper=endpoint(best_upper,True),previous_upper=box['previous_upper'],lower=best_lower,
                  nominal_separation=box['nominal_separation'])
    context.save('survivor-support.json',dict(result,trials=rows))
    return dict(result,passed=True,fit_starts=0,later_observations_used=0,scientific_decision='abstain')


def prepare(root):
    from .esa_attitude_feasibility import ID as FEASIBILITY
    from .esa_attitude_refinement_score import ID as REFINEMENT
    from .esa_direct_training_score import feasible_box_and_cuts
    from .ilvis0_acceleration_products import lift
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing ESA survivor-score freeze')
    staged = {}
    with ExitStack() as stack:
        prior = stack.enter_context(closing(ClosedStudy(root,'data/'+FEASIBILITY)))
        refined = stack.enter_context(closing(ClosedStudy(root,'data/'+REFINEMENT,store=prior.store)))
        cover = prior.input('cover')
        if (prior.completion['manifest_sha256']!=PARENT_SHA or not prior.summary['passed']
                or refined.completion['manifest_sha256']!=cover['manifest_sha256']):
            raise ValueError('exact completed parent cover and feasibility studies required')
        staged['cover.json'] = encoded(cover)
        staged['later-operator.npz'] = refined.input('later-operator',raw=True)
        for model,indices in RANGES.items():
            for suffix,ext in (('', '.npz'), ('-weights','.npz'), ('-settings','.json')):
                staged[model+suffix+ext] = prior.input(model+suffix,raw=True)
            products = refined.input(model+'-products')['cuts']
            center = tuple(map(F,refined.input(model+'-force')['center']+[0.]*24))
            linked = [r for r in refined.input(model+'-witnesses')['rows']
                      if r['variant']=='linked_shared' and r['loss_passed']]
            for task in prior.tasks.values():
                if task['payload']['model']!=model:
                    continue
                identity = task['identity']
                parent,child = task['payload']['parent'],task['payload']['child']
                saved = prior.artifact(identity,'feasibility.json')
                if saved['excluded']!=((parent,child) not in indices):
                    raise ValueError('freeze must retain every surviving high-bound range')
                staged[identity+'-feasibility.json'] = encoded(saved)
                if saved['excluded']:
                    continue
                box = prior.input(identity+'-domain')
                anchors = []
                for row in linked:
                    point = lift(products,[F(v)-c for v,c in zip(
                        row['physical_point']+row['shared'],center,strict=True)])
                    if feasible_box_and_cuts(point,box['lower'],box['upper'],box['static'],box['limits']):
                        anchors.append(dict(point=list(map(str,point)),score_lower=row['score_lower']))
                if bool(anchors)!=box['contains_feasible_witness']:
                    raise ValueError('exact archived linked membership required')
                staged[identity+'-domain.json'] = encoded(box)
                staged[identity+'-anchors.json'] = encoded(anchors)
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name,payload in staged.items():
        path = base/name
        atomic(path,payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID,adapter=adapter,sources=source_closure(root,[adapter,PLAN]),
        inputs=inputs,tasks=tasks(),scope=SCOPE,workers=4,threads=1,maximum_wall_s=120.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


def collect(root):
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root,'data/'+ID)) as study:
        cover = study.input('cover')
        results = []
        for model in cover['rows']:
            kept, checked = [], []
            for row in model['rows']:
                identity = f"{model['model']}-{row['parent_index']}-{row['cell_index']}"
                if row['upper']<=model['nominal_separation']/2:
                    kept.append(row['upper'])
                    continue
                old = study.input(identity+'-feasibility')
                if old['excluded']:
                    if F(old['trials'][-1]['exact_upper'])>=0:
                        raise ValueError('nonnegative certificate cannot exclude a range')
                    continue
                envelope = study.envelope(identity)['result'] if identity in study.rows else {}
                if not envelope.get('passed'):
                    kept.append(row['upper'])
                    continue
                record = study.artifact(identity,'survivor-support.json')
                if record['previous_upper']!=row['upper'] or record['upper']>row['upper'] or len(record['trials'])!=ROUNDS:
                    raise ValueError('new bound must preserve the original scope and fallback')
                kept.append(record['upper'])
                checked.append(dict(identity=identity,upper=record['upper'],previous_upper=row['upper'],
                    lower=record['lower'],successful_proposals=sum(t['success'] is True for t in record['trials'])))
            results.append(dict(model=model['model'],upper=max(kept),
                                nominal_separation=model['nominal_separation'],checked=checked))
        return dict(rows=results,manifest_sha256=study.completion['manifest_sha256'],
                    state=study.completion['state'],scientific_decision='abstain')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','report'),nargs='?',default='prepare')
    if parser.parse_args().action=='report':
        print(json.dumps(collect(Path.cwd()),sort_keys=True))
    else:
        prepare(Path.cwd())
