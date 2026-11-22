# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propose calibrated static-map bounds using tangents to the earlier loss ball."""

from contextlib import closing
from functools import partial
import json
import math
from pathlib import Path

from .esa_linked_child_certificates import RANGES, evaluate_child, read_dispositions, task_for
from .esa_linked_scaled_proposals import (ID as PARENT, RESULT as PRIOR, collect_refinement, scaled_problem)
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-linked-loss-tangents-v1-20261121'
PLAN = 'docs/prediction-observed-development/ESA_LINKED_LOSS_TANGENTS_PLAN.md'
TEST = 'analysis/tests/test_esa_linked_loss_tangents.py'
RESULT = 'docs/prediction-observed-development/esa-linked-loss-tangents.json'
SCOPE = 'Loss-ball tangent proposals for eleven surviving ESA calibration children'
PRIOR_SHA = '1cf8d32df2cb21f08d33f6b5b8b6dfd9b10cae7ab189ef264d99f481020c6de3'
ITERATIONS = 16
frozen_task = partial(task_for, bound_calls=2, bound_steps=ITERATIONS + 2)


def tangent_proposals(context, design, residual, lower, upper, cuts, limits, objective, start, radius, *, seed):
    import numpy as np
    from .ilvis0_coupled_training_score import propose

    design, residual, lower, upper, cuts, limits, objective, _ = scaled_problem(
        design, residual, lower, upper, cuts, limits, objective, start)
    row_scale = np.maximum(1e-20, np.maximum(np.max(abs(cuts), axis=1), abs(limits)))
    score_scale = max(1., np.max(abs(objective)))
    context.charge(bound_calls=1, bound_steps=ITERATIONS)
    proposal = propose(design, residual, lower, upper, objective / score_scale, cuts / row_scale[:, None],
        limits / row_scale, radius=radius, iterations=ITERATIONS, seed=seed)
    if not math.isfinite(proposal['approximate_upper']):
        return None, None
    return None, dict(success=True, iterations=proposal['iterations'],
        direction=proposal['direction'] * score_scale, weights=proposal['weights'] * score_scale / row_scale)


def evaluate(task, context):
    seed = json.loads(context.input_path(task['identity'] + '-earlier-direction').read_bytes())
    return evaluate_child(task, context, scope=SCOPE, task_builder=frozen_task,
                          propose=partial(tangent_proposals, seed=seed))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root / 'data' / (ID + '-inputs')
    if base.exists() or (root / 'data' / ID).exists():
        raise ValueError('reuse the existing frozen tangent study')
    raw = (root / PRIOR).read_bytes()
    if digest(raw) != PRIOR_SHA:
        raise ValueError('exact box-scaled predecessor report required')
    report = json.loads(raw)
    staged, tasks = {}, []
    with closing(ClosedStudy(root, 'data/' + PARENT)) as parent:
        if (any(report[k] != parent.completion[k] for k in ('manifest_sha256', 'summary_sha256'))
                or not parent.summary['passed'] or set(report['rows']) != set(parent.tasks)):
            raise ValueError('exact completed scaled certificates required')
        records, dispositions = read_dispositions(parent)
        if records != report['rows'] or any(row != report['dispositions'][key] for key, row in dispositions.items()):
            raise ValueError('previous certificate bounds must reproduce')
        for model in RANGES:
            for suffix in ('', '-weights', '-settings', '-support'):
                staged[model + suffix] = parent.input(model + suffix, raw=True)
        for key in ('cover', 'sensitivity', 'later-operator', 'earlier-linked-report', 'first-split'):
            staged[key] = parent.input(key, raw=True)
        for identity, task in parent.tasks.items():
            previous = dispositions[identity]
            if previous['excluded']:
                raise ValueError('do not revisit an already excluded box')
            child = parent.input(identity + '-child')
            child['prior']['upper'] = previous['upper']
            staged[identity + '-child'] = encoded(child)
            staged[identity + '-earlier-direction'] = encoded(records[identity]['proposals']['earlier_loss']['direction'])
            payload = task['payload']
            tasks.append(frozen_task(payload['parent'], payload['model'], payload['child']))
    if len(tasks) != 11:
        raise ValueError('exact eleven archived survivor identities required')
    base.mkdir(parents=True)
    inputs = {'plan': PLAN, 'prior': PRIOR}
    for key, content in staged.items():
        path = base / key
        atomic(path, content)
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).resolve().relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=tasks, sources=source_closure(root, [adapter, PLAN, TEST]),
        workers=2, threads=1, maximum_wall_s=120.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'collect'))
    if parser.parse_args().action == 'prepare':
        prepare(Path.cwd())
    else:
        collect_refinement(Path.cwd(), ID, RESULT)
