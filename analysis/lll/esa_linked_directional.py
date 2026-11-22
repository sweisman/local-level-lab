# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recheck the saved ESA loss directions with a linked calibration range."""

from contextlib import ExitStack, closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_attitude_cover_score import INCREASE
from .esa_attitude_survivor_score import RANGES


ID = 'esa-linked-directional-v1-20261120'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_DIRECTIONAL_PLAN.md'
SCOPE = 'Linked static-map support of nine surviving ESA calibration ranges'
SENSITIVITY_SHA = '39b680feef9eedc725be0ab91b11a77f3825aea996e7da620b29797df92118fa'
LINKED_SHA = '6b79557383a7be83b2427a4f7afed2732307f26ee2ad711bfe97574c926fc530'
MODES = ('direct', 'stored cuts')


def tasks():
    return [dict(identity=model, input_key=model, payload=dict(model=model),
                 limits=dict(native_calls=0, packet_visits=0,
                             bound_calls=4*len(ranges), bound_steps=8*len(ranges)))
            for model, ranges in RANGES.items()]


def evaluate(task, context):
    import numpy as np

    from .esa_linked_training_support import load_projection_inputs
    from .esa_shared_profile_score import support
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_linked_directional import directional_bound
    from .ilvis0_linked_training_support import training_upper
    from .ilvis0_saved_prediction_audit import endpoint
    from .state_space_directional_bound import adjoint_intervals

    model = task['identity']
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact linked directional study task required')
    residual, raw, _, _, _, earlier, target, settings = load_projection_inputs(context, model)
    saved = json.loads(context.input_path(model+'-support').read_bytes())
    force = saved['force']
    reference = restore_static_reference(force['configuration'], saved['first_sample']['dv'], saved['first_sample']['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
    static = StaticMap(reference, expected_report=saved['reference'], numerical_allowance=saved['map_allowance'])
    summary = []
    zero = ((F(0), F(0)),)*51
    for cell, expected in zip(saved['ranges'], RANGES[model], strict=True):
        if tuple(cell['identity']) != expected or len(cell['static']) != 270:
            raise ValueError('complete saved high-bound range required')
        lower, upper = cell['physical_lower'], cell['physical_upper']
        rows = []
        witnesses = [row for row in saved['points']
                     if all(a <= v <= b for a, v, b in zip(lower, row['point'], upper, strict=True))]
        for direction_name, objective in (('earlier_loss', zero), ('score', target)):
            proposal = cell[direction_name]
            direction = proposal['direction']
            a, b = adjoint_intervals(earlier, direction)
            projection = support(a, b, np.ones(len(residual)), raw)
            loss = training_upper(residual, direction, increase=INCREASE, unshared=0)
            kept = [(F(w), row, F(limit)) for w, row, limit in
                    zip(proposal['weights'], cell['static'], cell['limits'], strict=True)
                    if w and not any(row[51:])]
            if any(w < 0 for w, _, _ in kept):
                raise ValueError('static weights must be nonnegative')
            for mode in MODES:
                context.charge(bound_calls=1, bound_steps=2)
                cuts = kept if mode == 'stored cuts' else []
                shift = [sum(w*F(row[i]) for w, row, _ in cuts if row[i]) for i in range(51)]
                coefficients = [(lo-d-s, hi-c-s) for (lo, hi), c, d, s in
                    zip(objective, projection['lower'], projection['upper'], shift, strict=True)]
                band = directional_bound(static, lower, upper, coefficients)
                exact = loss + sum(w*b for w, _, b in cuts) + F(band.hi)
                for witness in witnesses:
                    floor = F(witness['score_lower']) if direction_name == 'score' else F(0)
                    if exact < floor:
                        raise ValueError('linked direction excludes an earlier verified point')
                rows.append(dict(direction=direction_name, mode=mode, exact_upper=str(exact),
                    upper=endpoint(exact, True), terms=len(cuts), static_range=[band.lo, band.hi]))
        excluded = min(F(row['exact_upper']) for row in rows if row['direction'] == 'earlier_loss') < 0
        upper = min(row['upper'] for row in rows if row['direction'] == 'score')
        summary.append(dict(identity=cell['identity'], excluded=excluded, upper=upper, witnesses=len(witnesses), trials=rows))
    context.save('linked-directional.json', dict(rows=summary, nominal_separation=settings['shape']['nominal']))
    return dict(passed=True, ranges=len(summary), excluded=sum(row['excluded'] for row in summary),
                fit_starts=0, later_observations_used=0, scientific_decision='abstain')


def prepare(root):
    from .esa_attitude_refinement_score import ID as REFINEMENT
    from .esa_attitude_survivor_score import ID as SURVIVOR
    from .esa_earlier_allowance_report import RESULT, SURVIVOR_SHA
    from .esa_linked_physical_score import ID as LINKED
    from .studies.artifacts import atomic, digest, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing linked directional study freeze')
    sensitivity = (root/RESULT).read_bytes()
    if digest(sensitivity) != SENSITIVITY_SHA:
        raise ValueError('unchanged archived allowance sensitivity required')
    staged = {'sensitivity.json': sensitivity}
    with ExitStack() as stack:
        old = stack.enter_context(closing(ClosedStudy(root, 'data/'+SURVIVOR)))
        refined = stack.enter_context(closing(ClosedStudy(root, 'data/'+REFINEMENT, store=old.store)))
        linked = stack.enter_context(closing(ClosedStudy(root, 'data/'+LINKED, store=old.store)))
        cover = old.input('cover')
        if (old.completion['manifest_sha256'] != SURVIVOR_SHA
                or refined.completion['manifest_sha256'] != cover['manifest_sha256']
                or linked.completion['manifest_sha256'] != LINKED_SHA or not linked.summary['passed']):
            raise ValueError('exact saved cover and linked-point studies required')
        staged['cover.json'] = encoded(cover)
        staged['later-operator.npz'] = old.input('later-operator', raw=True)
        for model, ranges in RANGES.items():
            for suffix, extension in (('', '.npz'), ('-weights', '.npz'), ('-settings', '.json')):
                staged[model+suffix+extension] = old.input(model+suffix, raw=True)
            saved = dict(force=refined.input(model+'-force'), first_sample=refined.input(model+'-first-sample'),
                         reference=refined.input(model+'-reference'),
                         map_allowance=refined.input(model+'-products')['cuts']['map_allowance'])
            points = {tuple(row['point']): row for key, task in linked.tasks.items()
                      if task['payload']['model'] == model and not task['payload']['gamma']
                      for row in linked.artifact(key, 'linked-points.json')['checks'] if row['loss_passed']}
            cells = []
            for parent, child in ranges:
                identity = f'{model}-{parent}-{child}'
                domain = old.input(identity+'-domain')
                feasibility = old.input(identity+'-feasibility')
                cell = refined.artifact(f'{model}-{parent}', f'cell-{child}.json')
                if feasibility['excluded'] or feasibility['trials'][-1]['method'] != 'earlier_loss':
                    raise ValueError('unchanged high-bound survivor required')
                cells.append(dict(identity=[parent, child], static=domain['static'], limits=domain['limits'],
                    physical_lower=cell['cuts']['physical_lower'], physical_upper=cell['cuts']['physical_upper'],
                    earlier_loss=feasibility['trials'][-1],
                    score=dict(direction=cell['proposal_direction'], weights=cell['proposal_weights'])))
            staged[model+'-support.json'] = encoded(dict(saved, ranges=cells, points=list(points.values())))
    base.mkdir(parents=True)
    inputs = {'plan': PLAN}
    for name, payload in staged.items():
        path = base/name
        atomic(path, payload)
        inputs[path.stem] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, adapter=adapter, sources=source_closure(root, [adapter, PLAN]),
        inputs=inputs, tasks=tasks(), scope=SCOPE, workers=2, threads=1, maximum_wall_s=120.), root).prepare(root)
    print(json.dumps(dict(study=ID, limits=manifest['limits']), sort_keys=True))


if __name__ == '__main__':
    prepare(Path.cwd())
