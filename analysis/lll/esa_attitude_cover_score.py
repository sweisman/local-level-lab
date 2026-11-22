# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound the saved ESA shape score on a complete attitude-box cover."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_linked_training_support import INCREASE, MODELS
from .ilvis0_physical_partition import audit, split


ID = 'esa-attitude-cover-score-v1-20261119'
PLAN = 'docs/prediction-observed-development/ESA_ATTITUDE_COVER_SCORE_PLAN.md'
SCOPE = 'Complete eight-box attitude cover of the saved ESA 187 shape score'
PRODUCT_SHA = '11d734bbb0f4543059b4645d4327697cc7d36533b6ccfa6e1fb3e2de175d8100'
GAMMA = .1
CELLS = 8
STEPS = 17
ITERATIONS = 200


def attitude_cover(lower, upper):
    vertical = split(lower, upper, axes=(2,))
    audit(vertical, lower, upper, axes=(2,))
    covers, cells = [], []
    for half in vertical['children']:
        horizontal = split(half['lower'], half['upper'], axes=(0,1))
        audit(horizontal, half['lower'], half['upper'], axes=(0,1))
        covers.append(horizontal)
        for child in horizontal['children']:
            cells.append(dict(child, index=len(cells)))
    if len(cells)!=CELLS:
        raise ValueError('expected three nondegenerate attitude axes and eight closed cells')
    return dict(vertical=vertical, horizontal=covers, cells=cells)


def tasks():
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=CELLS, bound_steps=CELLS*STEPS)) for model in MODELS]


def evaluate(task, context):
    model = task['identity']
    declared = {key: value for key,value in task.items() if key not in ('index','shard')}
    if context.manifest['scope']!=SCOPE or declared not in tasks():
        raise ValueError('exact attitude-cover task required')
    force = json.loads(context.input_path(model+'-force').read_bytes())
    partition = attitude_cover(force['lower'], force['upper'])
    context.save('cover.json', partition)
    result = score_cells(context, model, partition['cells'])
    if len(result['retained'])!=10 or len(result['rows'])!=CELLS:
        raise ValueError('complete calibration cover and witness retention required')
    context.save('cover-support.json', result)
    return dict(passed=True, cells=len(result['rows']), upper=result['upper'],
                previous_upper=result['previous_upper'], linked_points_checked=len(result['retained']),
                fit_starts=0, later_observations_used=0, map_allowance_qualified=False,
                unshared_error_qualified=False, scientific_decision='abstain')


def score_cells(context, model, cells, *, parent=None):
    import numpy as np
    from .esa_direct_training_score import feasible_box_and_cuts
    from .esa_linked_training_support import load_projection_inputs
    from .esa_shared_profile_score import support as coefficients
    from .ilvis0_acceleration_products import lift
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_coupled_prediction import audit_cuts, build
    from .ilvis0_coupled_training_score import certify, direct_proposal, translate_rows
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals

    def read(suffix):
        return json.loads(context.input_path(model+suffix).read_bytes())

    residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context, model)
    force, sample, expected = read('-force'), read('-first-sample'), read('-reference')
    reference = restore_static_reference(force['configuration'], sample['dv'], sample['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=expected)
    products = read('-products')['cuts']
    if products['source_binding']!=reference.parent.binding:
        raise ValueError('archived product rows must share the original reference')
    mapping = StaticMap(reference, expected_report=expected, numerical_allowance=products['map_allowance'])
    cuts = read('-cuts')
    static = [row+[0.]*9 for name in ('coupling','consistency','orientation')
              for row in cuts[name]['design']]+products['design']
    limits = cuts['translated_upper']+products['limits']
    ancestor = read('-parent')
    if ancestor['nominal_separation']!=settings['shape']['nominal']:
        raise ValueError('exact preceding score direction required')
    selected = next(row for row in ancestor['rows'] if row['earlier_unshared']==GAMMA)
    previous = min(selected['proposals'], key=lambda row:F(row['exact_upper']))
    center = tuple(map(F, force['center']+[0.]*24))
    if parent is None:
        previous_upper = selected['upper']
        previous_direction, previous_weights = previous['direction'], previous['weights']
    else:
        parent_cuts = parent['cuts']
        static += [row+[0.]*9 for row in parent_cuts['design']]
        limits += translate_rows(parent_cuts['design'],parent_cuts['upper'],center)
        previous_upper = parent['upper']
        previous_direction, previous_weights = parent['proposal_direction'], parent['proposal_weights']
    if len(previous_weights)!=len(static):
        raise ValueError('preceding support must bind all parent rows')
    witnesses = []
    for row in read('-witnesses')['rows']:
        if row['variant']=='linked_shared':
            delta = [F(x)-z for x,z in zip(row['physical_point']+row['shared'], center, strict=True)]
            witnesses.append((row, lift(products, delta)))
    if len(witnesses)!=10:
        raise ValueError('all ten saved linked checks required')
    extra = np.zeros((len(residual),9))
    raw, design = np.c_[raw,extra], np.c_[design,extra]
    target = target+((F(0),F(0)),)*9
    objective = np.array([float((a+b)/2) for a,b in target])

    def training(direction):
        lo, hi = adjoint_intervals(earlier,direction)
        projected = coefficients(lo,hi,np.ones(len(residual)),raw)
        return tuple(zip(projected['lower'],projected['upper'],strict=True))

    previous_training = training(previous_direction)
    radius = sqrt_upper(sum(F(float(v))**2 for v in residual)+F(INCREASE))+GAMMA
    rows, retained = [], set()
    for cell in cells:
        context.charge(bound_calls=1,bound_steps=STEPS)
        lo, hi = cell['lower'], cell['upper']
        child = build(mapping,lo,hi,reserve=lambda:None)
        audit_cuts(child,mapping.report(),lo,hi)
        lower = np.array([endpoint(F(a)-z,False) for a,z in zip(lo,center[:27],strict=True)]
                         +products['lower'][27:])
        upper = np.array([endpoint(F(b)-z,True) for b,z in zip(hi,center[:27],strict=True)]
                         +products['upper'][27:])
        child_static = static+[row+[0.]*9 for row in child['design']]
        child_limits = limits+translate_rows(child['design'],child['upper'],center)
        members = []
        for index,(row,point) in enumerate(witnesses):
            if all(a<=v<=b for a,v,b in zip(lo,row['physical_point'],hi,strict=True)):
                if not feasible_box_and_cuts(point,lower,upper,child_static,child_limits):
                    raise ValueError('child constraints exclude an archived linked calibration')
                members.append(index)
        retained.update(members)
        anchor = np.clip(previous['point'],lower,upper)
        proposal = direct_proposal(design,residual,lower,upper,objective,child_static,child_limits,
                                   radius=radius,start=anchor,iterations=ITERATIONS)
        exact = certify(residual,proposal['direction'],training(proposal['direction']),target,
            lower,upper,child_static,child_limits,proposal['weights'],increase=INCREASE,unshared=GAMMA)
        reused = certify(residual,previous_direction,previous_training,target,lower,upper,static,
                         limits,previous_weights,increase=INCREASE,unshared=GAMMA)
        bound = min(F(previous_upper),exact,reused)
        if any(row['loss_passed'] and F(row['score_lower'])>bound for row,_ in
               (witnesses[index] for index in members)):
            raise ValueError('child upper bound contradicts a preserved feasible point')
        result = dict(index=cell['index'],upper=endpoint(bound,True),exact_upper=str(bound),
                      proposed_exact=str(exact),reused_exact=str(reused),
                      success=proposal['success'],iterations=proposal['iterations'],members=members)
        context.save(f"cell-{cell['index']}.json",dict(result,cuts=child,
            proposal_direction=proposal['direction'].tolist(),proposal_weights=proposal['weights'].tolist()))
        rows.append(result)
    expected = set(range(len(witnesses))) if parent is None else set(parent['members'])
    if retained!=expected or len(rows)!=len(cells):
        raise ValueError('complete scored cover and witness retention required')
    return dict(rows=rows,upper=max(row['upper'] for row in rows),
                previous_upper=previous_upper,nominal_separation=settings['shape']['nominal'],
                retained=sorted(retained))


def prepare(root):
    from .esa_acceleration_product_score import ID as PRODUCT
    from .esa_coupled_training_score import ID as COUPLED
    from .esa_direct_training_score import PARENT_SHA
    from .studies.artifacts import atomic
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing attitude-cover freeze')
    staged = {}
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root,'data/'+PRODUCT)))
        prior = stack.enter_context(closing(ClosedStudy(root,'data/'+COUPLED,store=parent.store)))
        for study, expected in ((parent,PRODUCT_SHA),(prior,PARENT_SHA)):
            if study.completion['manifest_sha256']!=expected or not study.summary['passed']:
                raise ValueError('exact completed parent studies required')
        staged['later-operator.npz'] = parent.input('later-operator',raw=True)
        for model in MODELS:
            for suffix, ext in (('', '.npz'), ('-weights','.npz'), ('-settings','.json'),
                                ('-force','.json'), ('-first-sample','.json'), ('-cuts','.json'),
                                ('-witnesses','.json')):
                staged[model+suffix+ext] = parent.input(model+suffix,raw=True)
            staged[model+'-reference.json'] = prior.input(model+'-reference',raw=True)
            staged[model+'-products.json'] = parent.artifact(model,'product-cuts.json',raw=True)
            staged[model+'-parent.json'] = parent.artifact(model,'product-support.json',raw=True)
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, payload in staged.items():
        path = base/name
        atomic(path,payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID,adapter=adapter,
        sources=source_closure(root,[adapter,PLAN]),inputs=inputs,tasks=tasks(),scope=SCOPE,
        workers=2,threads=1,maximum_wall_s=150.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


if __name__=='__main__':
    prepare(Path.cwd())
