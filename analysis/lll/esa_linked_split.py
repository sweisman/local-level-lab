# SPDX-License-Identifier: AGPL-3.0-or-later
"""Refine the archived nine-range linked calibration cover without refitting."""

from contextlib import closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_attitude_cover_score import INCREASE
from .esa_linked_directional import ID as PARENT, RANGES, SENSITIVITY_SHA
from .esa_linked_directional_result import RESULT as PRIOR
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-split-v1-20261121'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_SPLIT_PLAN.md'
RESULT = 'docs/prediction-observed-development/esa-linked-split.json'
SCOPE = 'Two-child subdivision of nine archived ESA linked calibration ranges'
PRIOR_SHA = '76068b815a86e295903cccfa3fd498e24335dc952be252f2a1cce11292fc81b9'


def choose_axis(lower, upper, derivatives):
    impacts = [(F(hi) - F(lo)) * max(abs(F(a)), abs(F(b))) for lo, hi, (a, b)
               in zip(lower, upper, derivatives, strict=True)]
    if len(impacts) != 27:
        raise ValueError('all 27 physical coordinates required')
    splittable = [i for i, (lo, hi) in enumerate(zip(lower, upper, strict=True))
                  if lo < float((F(lo) + F(hi)) / 2) < hi]
    return max(splittable, key=lambda i: (impacts[i], -i)), impacts


def retain_upper(old, children):
    if len(children) != 2:
        raise ValueError('both closed children required')
    feasible = [child['upper'] for child in children if not child['excluded']]
    return min(old, max(feasible)) if feasible else None


def tasks():
    return [dict(identity=f'{model}-{first}-{second}', input_key=model,
                 payload=dict(model=model, pair=[first, second]),
                 limits=dict(native_calls=0, packet_visits=0, bound_calls=5, bound_steps=9))
            for model, ranges in RANGES.items() for first, second in ranges]


def stored_certificate(cell, direction_name, objective, residual, design, earlier):
    import numpy as np
    from .esa_shared_profile_score import support
    from .ilvis0_linked_training_support import training_upper
    from .state_space_directional_bound import adjoint_intervals

    proposal = cell[direction_name]
    direction = proposal['direction']
    a, b = adjoint_intervals(earlier, direction)
    projection = support(a, b, np.ones(len(residual)), design)
    loss = training_upper(residual, direction, increase=INCREASE, unshared=0)
    cuts = [(F(weight), row, F(limit)) for weight, row, limit
            in zip(proposal['weights'], cell['static'], cell['limits'], strict=True)
            if weight and not any(row[51:])]
    if any(weight < 0 for weight, _, _ in cuts):
        raise ValueError('nonnegative archived cut weights required')
    shifts = [sum(weight * F(row[i]) for weight, row, _ in cuts if row[i]) for i in range(51)]
    coefficients = [(lo - d - shift, hi - c - shift) for (lo, hi), c, d, shift
                    in zip(objective, projection['lower'], projection['upper'], shifts, strict=True)]
    return coefficients, loss + sum(weight * limit for weight, _, limit in cuts)


def evaluate(task, context):
    from .esa_linked_training_support import load_projection_inputs
    from .ilvis0_coupled_map import StaticMap, restore_static_reference
    from .ilvis0_linked_directional import _linked_expression, directional_bound
    from .ilvis0_physical_partition import audit, split
    from .ilvis0_saved_prediction_audit import endpoint

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in tasks():
        raise ValueError('exact saved calibration range required')
    model, pair = task['payload']['model'], task['payload']['pair']
    residual, design, _, _, _, earlier, target, settings = load_projection_inputs(context, model)
    saved = json.loads(context.input_path(model + '-support').read_bytes())
    cell = next(row for row in saved['ranges'] if row['identity'] == pair)
    prior = json.loads(context.input_path(task['identity'] + '-prior').read_bytes())
    if len(cell['static']) != 270 or prior['identity'] != pair:
        raise ValueError('complete original range and its retained bound required')
    force = saved['force']
    reference = restore_static_reference(force['configuration'], saved['first_sample']['dv'], saved['first_sample']['dt'],
        lower=force['lower'], upper=force['upper'], center=force['center'], expected_report=saved['reference'])
    static = StaticMap(reference, expected_report=saved['reference'], numerical_allowance=saved['map_allowance'])
    lo, hi = cell['physical_lower'], cell['physical_upper']
    necessary = stored_certificate(cell, 'earlier_loss', ((F(0), F(0)),) * 51, residual, design, earlier)
    score = stored_certificate(cell, 'score', target, residual, design, earlier)
    weights = [(a + b) / 2 for a, b in score[0]]
    context.charge(bound_calls=1, bound_steps=1)
    expression = _linked_expression(static, lo, hi, weights)
    axis, impacts = choose_axis(lo, hi, [(v.lo, v.hi) for v in expression.derivative])
    partition = split(lo, hi, axes=(axis,))
    coverage = audit(partition, lo, hi, axes=(axis,))
    witnesses = [(row['point'], F(row['score_lower'])) for row in saved['points']
                 if all(a <= value <= b for a, value, b in zip(lo, row['point'], hi, strict=True))]
    if len(witnesses) != prior['witnesses']:
        raise ValueError('all previously feasible witness memberships required')
    refined = []
    for child in partition['children']:
        bounds = []
        for coefficients, offset in (necessary, score):
            context.charge(bound_calls=1, bound_steps=2)
            interval = directional_bound(static, child['lower'], child['upper'], coefficients)
            bounds.append(offset + F(interval.hi))
        earlier_bound, score_bound = bounds
        members = [value for point, value in witnesses if all(a <= p <= b for a, p, b
                   in zip(child['lower'], point, child['upper'], strict=True))]
        if any(earlier_bound < 0 or score_bound < value for value in members):
            raise ValueError('child certificate contradicts an archived feasible witness')
        refined.append(dict(index=child['index'], excluded=earlier_bound < 0, witnesses=len(members),
            earlier_exact_upper=str(earlier_bound), score_exact_upper=str(score_bound), upper=endpoint(score_bound, True)))
    result = dict(identity=task['identity'], model=model, pair=pair, split=partition, coverage=coverage,
        impacts=[str(value) for value in impacts], children=refined,
        retained_upper=retain_upper(prior['upper'], refined), prior_upper=prior['upper'],
        nominal_separation=settings['shape']['nominal'], passed=True, scientific_decision='abstain')
    context.save('linked-split.json', result)
    return result


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root / 'data' / (ID + '-inputs')
    if base.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen subdivision')
    raw = (root / PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('exact archived linked calibration report required')
    report = json.loads(raw)
    staged = {}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as parent:
        if (parent.completion['manifest_sha256'] != report['manifest_sha256'] or not parent.summary['passed']
                or digest(parent.input('sensitivity', raw=True)) != SENSITIVITY_SHA):
            raise ValueError('exact completed parent bound required')
        for key in ('cover', 'sensitivity', 'later-operator'):
            staged[key] = parent.input(key, raw=True)
        for group in report['rows']:
            model = group['model']
            wanted = list(RANGES[model])
            artifact = parent.artifact(model, 'linked-directional.json')
            if group['ranges'] != artifact['rows'] or [tuple(row['identity']) for row in artifact['rows']] != wanted:
                raise ValueError('all archived high-bound survivors required')
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model + suffix] = parent.input(model + suffix, raw=True)
            for row in group['ranges']:
                a, b = row['identity']
                if row['excluded']:
                    raise ValueError('cannot reintroduce a previously excluded calibration range')
                staged[f'{model}-{a}-{b}-prior'] = encoded(row)
    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR}
    for key, content in staged.items():
        path = base / key
        atomic(path, content)
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=tasks(), sources=source_closure(root, [adapter, PLAN]), workers=2, threads=1,
        maximum_wall_s=120.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_saved_prediction_audit import endpoint

    with closing(ClosedStudy(root, 'data/' + ID)) as study:
        if not study.summary['passed'] or study.summary['completed'] != 9 or study.summary['bound_evaluations'] != 45:
            raise ValueError('all nine range checks must complete within their charges')
        rows = {}
        for identity in study.tasks:
            row = study.artifact(identity, 'linked-split.json')
            if (row != study.envelope(identity)['result'] or row['identity'] != identity
                    or row['scientific_decision'] != 'abstain' or not row['coverage']['passed']):
                raise ValueError('sealed child-cover result differs')
            rows[identity] = row
        old = {row['model']: row for row in study.input('prior')['rows']}
        earlier = {group['model']: group['rows'][0] for group in study.input('sensitivity')['rows']}
        models = {}
        for group in study.input('cover')['rows']:
            model = group['model']
            retained = []
            for case in group['rows']:
                identity = f'{model}-{case["parent_index"]}-{case["cell_index"]}'
                if identity in earlier[model]['excluded_ranges']:
                    if identity in rows:
                        raise ValueError('refinement cannot restore a previously excluded box')
                    continue
                refined = rows[identity]['retained_upper'] if identity in rows else case['upper']
                if refined is not None:
                    retained.append(min(case['upper'], refined))
            models[model] = dict(previous=old[model]['upper'], refined=min(old[model]['upper'], max(retained)))
        gaps = {row['nominal_separation'] for row in old.values()}
        if len(gaps) != 1:
            raise ValueError('both candidates must use the same separation')
        result = encoded(dict(rows=rows, candidate_bounds=models,
            nominal_separation=gaps.pop(), combined_upper=endpoint(sum(F(m['refined']) for m in models.values()), True),
            scientific_decision='abstain', manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / RESULT, result)
    print(digest(result))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
