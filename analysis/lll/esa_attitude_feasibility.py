# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check whether high-bound ranges can satisfy the archived earlier GPS limit."""

from contextlib import closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_attitude_cover_score import GAMMA, INCREASE


ID = 'esa-attitude-feasibility-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_ATTITUDE_FEASIBILITY_PLAN.md'
SCOPE = 'Necessary feasibility of the 26 high-bound ranges in the sealed ESA cover'
PARENT_SHA = '0470bc9ea16d9b63202da3534051f7849881fa3fc8857cfc8496ed771f27e8b9'
RANGES = {
    'sphere_still': ((4,0),(4,1),(4,2),(4,3),(5,0),(5,1),(5,2),(5,3),(6,0),(6,2),(7,0),(7,2)),
    'flat_still': ((0,0),(0,1),(0,2),(0,3),(1,1),(1,3),(2,0),(2,1),(2,2),(2,3),(3,0),(3,1),(3,2),(3,3)),
}
STEPS = 6
ITERATIONS = 120


def tasks():
    return [dict(identity=f'{model}-{parent}-{child}',input_key=model,
                 payload=dict(model=model,parent=parent,child=child),
                 limits=dict(native_calls=0,packet_visits=0,bound_calls=1,bound_steps=STEPS))
            for model,indices in RANGES.items() for parent,child in indices]


def evaluate(task, context):
    import numpy as np
    from .esa_calibration_witness import check_point
    from .esa_direct_training_score import feasible_box_and_cuts
    from .esa_linked_training_support import training_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_coupled_training_score import certify
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_training_feasibility import loss_proposal, static_proposal
    from .state_space_directional_bound import adjoint_intervals

    declared = {k:v for k,v in task.items() if k not in ('index','shard')}
    if context.manifest['scope']!=SCOPE or declared not in tasks():
        raise ValueError('exact registered ESA feasibility task required')
    model = task['payload']['model']
    box = json.loads(context.input_path(task['identity']+'-domain').read_bytes())
    residual, raw, design, _, _, earlier, settings = training_inputs(
        lambda key:context.input_path(key).read_bytes(),model)
    extra = np.zeros((len(residual),9))
    raw, design = np.c_[raw[:len(residual)],extra], np.c_[design,extra]
    lower, upper = np.asarray(box['lower']), np.asarray(box['upper'])
    static, limits = box['static'], box['limits']
    if box['nominal_separation']!=settings['shape']['nominal'] or len(static)!=270 or len(lower)!=60 or len(upper)!=60:
        raise ValueError('all original constraints and unchanged forecast direction required')
    objective = ((F(0),F(0)),)*len(lower)
    direction = np.zeros_like(residual)

    context.charge(bound_calls=1,bound_steps=STEPS)
    start, weights, slack = static_proposal(lower,upper,static,limits)
    bound = certify(residual,direction,objective,objective,lower,upper,static,limits,weights,
                    increase=INCREASE,unshared=GAMMA)
    trials = [dict(method='static',exact_upper=str(bound),slack=slack,
                   weights=weights.tolist(),direction=None)]
    feasible = False
    if bound>=0:
        proposal = loss_proposal(design,residual,lower,upper,static,limits,start,iterations=ITERATIONS)
        direction, weights = proposal['direction'],proposal['weights']
        lo, hi = adjoint_intervals(earlier,direction)
        projected = coefficients(lo,hi,np.ones(len(residual)),raw)
        train = tuple(zip(projected['lower'],projected['upper'],strict=True))
        bound = certify(residual,direction,train,objective,lower,upper,static,limits,weights,
                        increase=INCREASE,unshared=GAMMA)
        point = tuple(map(F,proposal['point']))
        check = None
        if feasible_box_and_cuts(point,lower,upper,static,limits):
            check = check_point(earlier,raw,residual,objective,point,unshared=GAMMA)
            feasible = check['loss_passed']
        trials.append(dict(method='earlier_loss',exact_upper=str(bound),weights=weights.tolist(),
            direction=direction.tolist(),proposal_success=proposal['success'],iterations=proposal['iterations'],
            proposed_norm=proposal['proposed_norm'],
            allowed_norm_upper=sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))+GAMMA,
            point=proposal['point'].tolist(),checked_point=check,tangent_proposed=proposal['tangent_proposed']))
    excluded = bound<0
    if excluded and (box['contains_feasible_witness'] or feasible):
        raise ValueError('exclusion contradicts a verified feasible point')
    result = dict(excluded=excluded,excluded_by=trials[-1]['method'] if excluded else None,
                  has_verified_feasible_point=feasible or box['contains_feasible_witness'],
                  retained_upper=None if excluded else box['previous_upper'])
    context.save('feasibility.json',dict(result,trials=trials))
    return dict(result,passed=True,fit_starts=0,later_observations_used=0,scientific_decision='abstain')


def prepare(root):
    from .esa_attitude_refinement_score import ID as REFINEMENT, collect
    from .ilvis0_coupled_training_score import translate_rows
    from .ilvis0_saved_prediction_audit import endpoint
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing ESA feasibility freeze')
    cover = collect(root)
    if cover['manifest_sha256']!=PARENT_SHA:
        raise ValueError('exact completed refinement required')
    staged = {'cover.json':encoded(cover)}
    with closing(ClosedStudy(root,'data/'+REFINEMENT)) as study:
        for summary in cover['rows']:
            model = summary['model']
            for suffix, ext in (('', '.npz'), ('-weights','.npz'), ('-settings','.json')):
                staged[model+suffix+ext] = study.input(model+suffix,raw=True)
            force = study.input(model+'-force')
            center = tuple(map(F,force['center']+[0.]*24))
            cuts = study.input(model+'-cuts')
            products = study.input(model+'-products')['cuts']
            static = [row+[0.]*9 for name in ('coupling','consistency','orientation')
                      for row in cuts[name]['design']]+products['design']
            limits = cuts['translated_upper']+products['limits']
            witnesses = [r for r in study.input(model+'-witnesses')['rows'] if r['variant']=='linked_shared']
            selected = [r for r in summary['rows'] if r['upper']>summary['nominal_separation']/2]
            if tuple((r['parent_index'],r['cell_index']) for r in selected)!=RANGES[model]:
                raise ValueError('all and only the sealed high-bound ranges required')
            for row in selected:
                parent, child = row['parent_index'], row['cell_index']
                first = study.input(f'{model}-range-{parent}')['cuts']
                saved = study.artifact(f'{model}-{parent}',f'cell-{child}.json')
                second = saved['cuts']
                part = study.artifact(f'{model}-{parent}','subdivision.json')['children'][child]
                if (second['physical_lower']!=part['lower'] or second['physical_upper']!=part['upper']
                        or saved['upper']!=row['upper'] or saved['index']!=child):
                    raise ValueError('the sealed range and its own score bound must agree')
                local = [a+[0.]*9 for stage in (first,second) for a in stage['design']]
                right = translate_rows(first['design'],first['upper'],center)
                right += translate_rows(second['design'],second['upper'],center)
                lower = [endpoint(F(a)-z,False) for a,z in zip(part['lower'],center[:27],strict=True)]
                upper = [endpoint(F(b)-z,True) for b,z in zip(part['upper'],center[:27],strict=True)]
                staged[f'{model}-{parent}-{child}-domain.json'] = encoded(dict(
                    lower=lower+products['lower'][27:],upper=upper+products['upper'][27:],
                    static=static+local,limits=limits+right,previous_upper=row['upper'],
                    nominal_separation=summary['nominal_separation'],
                    contains_feasible_witness=any(witnesses[i]['loss_passed'] for i in saved['members'])))
    base.mkdir(parents=True)
    inputs = {'plan':PLAN}
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
            retained = []
            exclusions, feasible = [], []
            for row in model['rows']:
                identity = f"{model['model']}-{row['parent_index']}-{row['cell_index']}"
                if identity not in study.tasks:
                    retained.append(row['upper'])
                    continue
                envelope = study.envelope(identity)['result'] if identity in study.rows else {}
                if not envelope.get('passed'):
                    retained.append(row['upper'])
                    continue
                record = study.artifact(identity,'feasibility.json')
                excluded = F(record['trials'][-1]['exact_upper'])<0
                if record['excluded']!=excluded or envelope['excluded']!=excluded:
                    raise ValueError('exclusion must follow from a checked strictly negative certificate')
                if excluded:
                    exclusions.append(dict(identity=identity,method=record['excluded_by']))
                else:
                    retained.append(row['upper'])
                    if record['has_verified_feasible_point']:
                        feasible.append(identity)
            if not retained:
                raise ValueError('an empty complete cover contradicts the verified linked points')
            results.append(dict(model=model['model'],upper=max(retained),previous_upper=model['upper'],
                nominal_separation=model['nominal_separation'],exclusions=exclusions,feasible=feasible))
        return dict(rows=results,manifest_sha256=study.completion['manifest_sha256'],
                    state=study.completion['state'],scientific_decision='abstain')


def verify_exclusions(root):
    """Replay every exclusion from sealed inputs, without solver proposals."""
    import numpy as np
    from .esa_linked_training_support import training_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_coupled_training_score import certify
    from .state_space_directional_bound import adjoint_intervals
    from .studies.closed import ClosedStudy

    summary = collect(root)
    verified = 0
    with closing(ClosedStudy(root,'data/'+ID)) as study:
        for item in summary['rows']:
            model = item['model']
            residual, raw, _, _, _, earlier, _ = training_inputs(
                lambda key:study.input(key,raw=True),model)
            raw = raw[:len(residual)]
            extra = ((F(0),F(0)),)*9
            objective = ((F(0),F(0)),)*60
            for exclusion in item['exclusions']:
                identity = exclusion['identity']
                box = study.input(identity+'-domain')
                trial = study.artifact(identity,'feasibility.json')['trials'][-1]
                direction = trial['direction']
                train = objective
                if direction is None:
                    direction = np.zeros_like(residual)
                else:
                    lo, hi = adjoint_intervals(earlier,direction)
                    projected = coefficients(lo,hi,np.ones(len(residual)),raw)
                    train = tuple(zip(projected['lower'],projected['upper'],strict=True))+extra
                bound = certify(residual,direction,train,objective,box['lower'],box['upper'],
                    box['static'],box['limits'],trial['weights'],increase=INCREASE,unshared=GAMMA)
                if bound!=F(trial['exact_upper']) or bound>=0 or box['contains_feasible_witness']:
                    raise ValueError('sealed exclusion proof did not reproduce')
                verified += 1
    return dict(summary,verified_exclusions=verified)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','report','verify'),nargs='?',default='prepare')
    action = parser.parse_args().action
    if action=='report':
        print(json.dumps(collect(Path.cwd()),sort_keys=True))
    elif action=='verify':
        print(json.dumps(verify_exclusions(Path.cwd()),sort_keys=True))
    else:
        prepare(Path.cwd())
