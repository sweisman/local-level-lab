# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check new child-specific calibration certificates against the frozen cover."""

from contextlib import closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_attitude_survivor_score import ID as DOMAIN_ID
from .esa_linked_split import ID as PARENT, RESULT as PRIOR, INCREASE, RANGES, stored_certificate
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-child-certificates-v1-20261121'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_CHILD_CERTIFICATES_PLAN.md'
RESULT = 'docs/prediction-observed-development/esa-linked-child-certificates.json'
SCOPE = 'Child-specific stored-cut calibration certificates on the frozen ESA 187 subdivision'
PRIOR_SHA = '887055f39e00eccff1b3f1b7c4b2ef69ebc46d8e2cfcc56cd8ae69acc5b2eb7c'
ITERATIONS = 120


def certified_disposition(old, earlier, score, witnesses):
    from .ilvis0_saved_prediction_audit import endpoint

    if any(earlier < 0 or min(F(old), score) < value for value in witnesses):
        raise ValueError('certificate contradicts a saved feasible witness')
    return (True, None) if earlier < 0 else (False, endpoint(min(F(old), score), True))


def task_for(parent, model, index, *, bound_calls=4, bound_steps=6):
    identity = f'{parent}-{index}'
    return dict(identity=identity, input_key=model, payload=dict(parent=parent, model=model, child=index),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=bound_calls, bound_steps=bound_steps))


def evaluate(task, context):
    return evaluate_child(task, context, scope=SCOPE, propose=unscaled_proposals)


def unscaled_proposals(context, design, residual, lower, upper, cuts, limits, objective, start, radius):
    from .ilvis0_coupled_training_score import direct_proposal
    from .ilvis0_training_feasibility import loss_proposal

    context.charge(bound_calls=1, bound_steps=1)
    loss = loss_proposal(design, residual, lower, upper, cuts, limits, start, iterations=ITERATIONS)
    context.charge(bound_calls=1, bound_steps=1)
    score = direct_proposal(design, residual, lower, upper, objective, cuts, limits,
        radius=radius, start=loss['point'], iterations=ITERATIONS, scaled_tangent=True)
    return loss, score


def evaluate_child(task, context, *, scope, propose, task_builder=task_for):
    import numpy as np
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_exact_scale import sqrt_upper
    from .ilvis0_linked_directional import directional_bound
    from .ilvis0_saved_prediction_audit import endpoint

    identity = task['identity']
    parent, model, index = (task['payload'][key] for key in ('parent', 'model', 'child'))
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != scope or declared != task_builder(parent, model, index):
        raise ValueError('exact frozen child task required')
    residual, raw, design, _, _, earlier, target, settings = load_projection_inputs(context, model)
    source = json.loads(context.input_path(model + '-support').read_bytes())
    frozen = json.loads(context.input_path(identity + '-child').read_bytes())
    child, prior = frozen['child'], frozen['prior']
    cell = next(cell for cell in source['ranges'] if cell['identity'] == frozen['pair'])
    if (child['index'] != index or prior['index'] != index or prior['excluded']
            or len(cell['static']) != 270 or settings['shape']['nominal'] != frozen['nominal']):
        raise ValueError('unchanged surviving child and earlier-fit design required')
    force = source['force']
    reference = restore_static_reference(force['configuration'], source['first_sample']['dv'], source['first_sample']['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=source['reference'])
    static_map = StaticMap(reference, expected_report=source['reference'], numerical_allowance=source['map_allowance'])
    lo, hi, center = child['lower'], child['upper'], tuple(map(F, force['center']))
    lower = [endpoint(F(x) - c, False) for x, c in zip(lo, center, strict=True)] + frozen['lower'][27:]
    upper = [endpoint(F(x) - c, True) for x, c in zip(hi, center, strict=True)] + frozen['upper'][27:]
    full_design = np.c_[design, np.zeros((len(residual), 9))]
    objective = np.r_[[float((a + b) / 2) for a, b in target], np.zeros(9)]
    start = np.clip(cell['earlier_loss']['point'], lower, upper)
    cuts, limits = cell['static'], cell['limits']
    radius = sqrt_upper(sum(F(float(v))**2 for v in residual) + F(INCREASE))

    loss, score = propose(context, full_design, residual, lower, upper, cuts, limits, objective, start, radius)
    proposals = [('earlier_loss', ((F(0), F(0)),) * 51, loss), ('score', target, score)]
    bounds = {}
    for name, objective, proposal in proposals:
        if proposal is None:
            continue
        context.charge(bound_calls=1, bound_steps=2)
        coefficients, offset = stored_certificate(dict(cell, **{name: proposal}), name, objective, residual, raw, earlier)
        interval = directional_bound(static_map, lo, hi, coefficients)
        bounds[name] = offset + F(interval.hi)

    witnesses = [F(row['score_lower']) for row in source['points']
                 if all(a <= x <= b for a, x, b in zip(lo, row['point'], hi, strict=True))]
    if len(witnesses) != prior['witnesses']:
        raise ValueError('all saved feasible witness memberships required')
    excluded, upper = certified_disposition(prior['upper'], bounds.get('earlier_loss', F(0)),
                                            bounds.get('score', F(prior['upper'])), witnesses)
    result = dict(identity=identity, parent=parent, model=model, child=index, excluded=excluded,
        upper=upper, previous_upper=prior['upper'], witnesses=len(witnesses),
        proposals={name: dict(success=proposal['success'], iterations=proposal['iterations'],
            direction=proposal['direction'].tolist(), weights=proposal['weights'].tolist(), exact_upper=str(bounds[name]))
            for name, _, proposal in proposals if proposal is not None},
        passed=True, scientific_decision='abstain')
    context.save('child-certificate.json', result)
    return result


def prepare(root):
    from .ilvis0_physical_partition import audit
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root / 'data' / (ID + '-inputs')
    if base.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen child-certificate study')
    raw = (root / PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('exact prior subdivision report required')
    report = json.loads(raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/' + PARENT)) as parent, closing(
            ClosedStudy(root, 'data/' + DOMAIN_ID, store=parent.store)) as domains:
        if any(report[key] != parent.completion[key] for key in ('manifest_sha256', 'summary_sha256')):
            raise ValueError('prior subdivision report must match its completion')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model + suffix] = parent.input(model + suffix, raw=True)
        for name in ('cover', 'sensitivity', 'later-operator'):
            staged[name] = parent.input(name, raw=True)
        staged['earlier-linked-report'] = parent.input('prior', raw=True)
        for identity, row in report['rows'].items():
            if row != parent.artifact(identity, 'linked-split.json'):
                raise ValueError('each subdivision must match its sealed result')
            model = row['model']
            cell = next(c for c in json.loads(staged[model + '-support'])['ranges'] if c['identity'] == row['pair'])
            partition = row['split']
            audit(partition, cell['physical_lower'], cell['physical_upper'], axes=tuple(partition['axes']))
            box = domains.input(identity + '-domain')
            if (box['static'] != cell['static'] or box['limits'] != cell['limits']
                    or box['nominal_separation'] != row['nominal_separation']
                    or len(box['lower']) != 60 or len(box['upper']) != 60):
                raise ValueError('all archived static constraints and calibration columns required')
            for child, previous in zip(partition['children'], row['children'], strict=True):
                if child['index'] != previous['index']:
                    raise ValueError('preserve each frozen child identity')
                if previous['excluded']:
                    continue
                task = task_for(identity, model, child['index'])
                tasks.append(task)
                staged[task['identity'] + '-child'] = encoded(dict(child=child, prior=previous, pair=row['pair'],
                    lower=box['lower'], upper=box['upper'], nominal=row['nominal_separation']))
    if len(tasks) != 15:
        raise ValueError('all fifteen surviving children required')
    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR}
    for key, content in staged.items():
        path = base / key
        atomic(path, content)
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=tasks, sources=source_closure(root, [adapter, PLAN]), workers=2, threads=1,
        maximum_wall_s=120.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def read_dispositions(study):
    rows, dispositions = {}, {}
    for identity in study.tasks:
        frozen = study.input(identity + '-child')['prior']
        row = study.rows.get(identity)
        if row is None or row['passed'] is not True:
            dispositions[identity] = dict(previous_upper=frozen['upper'], upper=frozen['upper'], excluded=False,
                status=row['status'] if row else 'missing')
            continue
        record = study.artifact(identity, 'child-certificate.json')
        if (record != study.envelope(identity)['result'] or record['identity'] != identity
                or record['previous_upper'] != frozen['upper'] or record['witnesses'] != frozen['witnesses']
                or record['scientific_decision'] != 'abstain'):
            raise ValueError('saved certificate does not match its frozen child')
        rows[identity] = record
        dispositions[identity] = dict(previous_upper=record['previous_upper'], upper=record['upper'],
                                      excluded=record['excluded'], status='certified')
    return rows, dispositions


def recombine_bounds(study, prior, dispositions, previous):
    old_linked = {row['model']:row for row in study.input('earlier-linked-report')['rows']}
    excluded = {group['model']: set(group['rows'][0]['excluded_ranges']) for group in study.input('sensitivity')['rows']}
    result = {}
    for group in study.input('cover')['rows']:
        model = group['model']
        bounds = []
        for case in group['rows']:
            key = f'{model}-{case["parent_index"]}-{case["cell_index"]}'
            if key in excluded[model]:
                continue
            if key in prior['rows']:
                split = prior['rows'][key]
                children = [dispositions[f'{key}-{child["index"]}'] for child in split['children'] if not child['excluded']]
                upper = [child['upper'] for child in children if not child['excluded']]
                if not upper:
                    continue
                bounds.append(min(case['upper'], split['retained_upper'], max(upper)))
            else:
                bounds.append(case['upper'])
        old = previous[model]['refined']
        result[model] = dict(previous=old, refined=min(old_linked[model]['upper'], old, max(bounds)))
    return result


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_saved_prediction_audit import endpoint

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        prior = study.input('prior')
        rows, dispositions = read_dispositions(study)
        result = recombine_bounds(study, prior, dispositions, prior['candidate_bounds'])
        output = encoded(dict(rows=rows, dispositions=dispositions, completed=study.summary['completed'],
            candidate_bounds=result, nominal_separation=prior['nominal_separation'],
            combined_upper=endpoint(sum(F(row['refined']) for row in result.values()), True),
            scientific_decision='abstain', manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, output)
    print(digest(output))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
