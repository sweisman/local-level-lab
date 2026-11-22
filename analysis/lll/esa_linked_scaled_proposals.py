# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rescale the archived child searches while checking their original boxes."""

from contextlib import closing
from fractions import Fraction as F
import json
from pathlib import Path

from .esa_linked_child_certificates import (ID as PARENT, ITERATIONS, RANGES, RESULT as PRIOR,
    evaluate_child, read_dispositions, recombine_bounds)
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-scaled-proposals-v1-20261121'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_SCALED_PROPOSALS_PLAN.md'
RESULT = 'docs/prediction-observed-development/esa-linked-scaled-proposals.json'
SCOPE = 'Box-scaled proposal searches for eleven surviving ESA calibration children'
PRIOR_SHA = '9a461532e1963cb386f135f2c6f8599906719d7a01677f1e78fea087d901dd2f'


def scaled_problem(design, residual, lower, upper, cuts, limits, objective, start):
    import numpy as np

    lower, upper = np.asarray(lower, float), np.asarray(upper, float)
    cuts, limits = np.asarray(cuts, float), np.asarray(limits, float)
    half_width = (upper - lower) / 2
    center = lower + half_width
    moving = half_width > 0
    lo, hi = -moving.astype(float), moving.astype(float)
    point = np.zeros_like(center)
    np.divide(start - center, half_width, out=point, where=moving)
    return (design * half_width, residual + design @ center, lo, hi,
            cuts * half_width, limits - cuts @ center, objective * half_width, np.clip(point, lo, hi))


def scaled_proposals(context, design, residual, lower, upper, cuts, limits, objective, start, radius):
    from .ilvis0_coupled_training_score import direct_proposal
    from .ilvis0_training_feasibility import loss_proposal

    design, residual, lower, upper, cuts, limits, objective, start = scaled_problem(
        design, residual, lower, upper, cuts, limits, objective, start)
    context.charge(bound_calls=1, bound_steps=1)
    loss = loss_proposal(design, residual, lower, upper, cuts, limits, start, iterations=ITERATIONS)
    context.charge(bound_calls=1, bound_steps=1)
    score = direct_proposal(design, residual, lower, upper, objective, cuts, limits,
        radius=radius, start=loss['point'], iterations=ITERATIONS, scaled_tangent=True)
    # The residual and constraint multipliers retain their respective units.
    # Only proposed points use the normalized coordinates.
    return loss, score


def evaluate(task, context):
    return evaluate_child(task, context, scope=SCOPE, propose=scaled_proposals)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root / 'data' / (ID + '-inputs')
    if base.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen box-scaled study')
    raw = (root / PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('exact child-certificate report required')
    report = json.loads(raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/' + PARENT)) as parent:
        if (any(report[k] != parent.completion[k] for k in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed'] or set(report['rows']) != set(parent.tasks)):
            raise ValueError('exact completed original certificates required')
        records, dispositions = read_dispositions(parent)
        if records != report['rows'] or dispositions != report['dispositions']:
            raise ValueError('original child bounds must match the sealed certificates')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model + suffix] = parent.input(model + suffix, raw=True)
        for key in ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report'):
            staged[key] = parent.input(key, raw=True)
        staged['first-split'] = parent.input('prior', raw=True)
        for identity, task in parent.tasks.items():
            disposition = dispositions[identity]
            if disposition['excluded']:
                continue
            child = parent.input(identity + '-child')
            child['prior']['upper'] = disposition['upper']
            staged[identity + '-child'] = encoded(child)
            tasks.append({key: value for key, value in task.items() if key not in ('index', 'shard')})
    if len(tasks) != 11:
        raise ValueError('exactly eleven surviving children required')
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


def collect(root):
    collect_refinement(root, ID, RESULT)


def collect_refinement(root, study_id, result_path):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .ilvis0_saved_prediction_audit import endpoint

    with closing(ClosedStudy(root, 'data/' + study_id)) as study:
        previous, cover = study.input('prior'), study.input('first-split')
        rows, dispositions = read_dispositions(study)
        combined = dict(previous['dispositions'], **dispositions)
        models = recombine_bounds(study, cover, combined, previous['candidate_bounds'])
        output = encoded(dict(rows=rows, dispositions=combined, completed=study.summary['completed'],
            candidate_bounds=models, nominal_separation=cover['nominal_separation'],
            combined_upper=endpoint(sum(F(row['refined']) for row in models.values()), True),
            scientific_decision='abstain', manifest_sha256=study.completion['manifest_sha256'],
            summary_sha256=study.completion['summary_sha256']))
    _write_equal(root / result_path, output)
    print(digest(output))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    {'prepare': prepare, 'collect': collect}[parser.parse_args().action](Path.cwd())
