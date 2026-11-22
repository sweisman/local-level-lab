# SPDX-License-Identifier: AGPL-3.0-or-later
"""Attribute the recorded position-bound growth without changing its arithmetic."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path

from .esa_packet_bound_growth import BASE, INDICES, LIMITS, MODELS, PACKETS, task_for
from .esa_packet_bound_growth import ID as PARENT, RESULT as PRIOR
from .esa_shape_prefix_preflight import evaluate_prepared
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_position_budget import PARTS
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-position-bound-budget-v1'
SCOPE = 'Unchanged ESA 187 recorded prefix with per-packet position remainder attribution'
PLAN = BASE+'ESA_POSITION_BOUND_BUDGET_PLAN.md'
RESULT = BASE+'esa-position-bound-budget-result.json'
REQUEST = BASE+'esa-position-bound-budget-qualification-v2.json'
REPORT = BASE+'esa-position-bound-budget-tests-v2.xml'
TEST = 'analysis/tests/test_ilvis0_position_budget.py'
REQUIRED = 'test_terms_reconstruct_bound_and_child_does_not_change_parent'


def qualification(root, *, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST,
        'analysis/lll/ilvis0_source_prefix_reference.cpp', 'analysis/lll/ilvis0_source_prefix_intervals.cpp'))
    env = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=(REQUIRED,), minimum_tests=1)
    return sources, env


def prepare(root):
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the existing position-budget allowance')
    saved = json.loads((root/PRIOR).read_bytes())
    sources, env = qualification(root, verify=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=550)))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (parent.completion != saved['completion'] or not parent.summary['passed']
                or parent.manifest['environment'] != env or set(parent.rows) != set(MODELS)):
            raise ValueError('verified four-query growth study under the same environment required')
        for model in MODELS:
            row = parent.envelope(model)
            if row['result'] != saved['rows'][model]['result'] or row['charged'] != LIMITS:
                raise ValueError('identical saved propagation and charges required')
            staged[model] = parent.input(model, raw=True)
            staged[model+'-metadata'] = parent.input(model+'-metadata', raw=True)
            staged[model+'-gold'] = encoded(dict(bounds_sha256=digest(parent.artifact(model, 'bounds.json', raw=True)),
                packet_work=row['result']['work']))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, value in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                     sources=sources, tasks=[task_for(model) for model in MODELS], workers=2, threads=1, maximum_wall_s=550.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from .ilvis0_solver_position import physical_metric

    model = task['identity']
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or model not in MODELS or declared != task_for(model):
        raise ValueError('exact sealed trace task and packet allowance required')
    with np.load(context.input_path(model), allow_pickle=False) as material:
        metrics = physical_metric(material['positions']).tolist()
        times = material['times'].tolist()
    budgets = []

    def observe(index, terms, reference):
        if index != len(budgets) or tuple(terms) != PARTS or len(reference) != 3:
            raise ValueError('ordered complete budget checkpoints required')
        scale = metrics[index]
        components = {key: [a*b for a, b in zip(terms[key], scale, strict=True)] for key in PARTS}
        total = [a*b for a, b in zip(reference, scale, strict=True)]
        error = [math.fsum(values)-expected for values, expected in zip(zip(*components.values(), strict=True), total, strict=True)]
        if any(not math.isfinite(value) or abs(value) > 1e-9 for value in error):
            raise ValueError('rate contributions did not reconstruct their departure remainder')
        budget = dict(query=INDICES[index], time_s=times[index], terms_m=components, total_m=total, error_m=error)
        budgets.append(budget)
        context.save(f'budget-{index:02d}.json', budget)

    result = evaluate_prepared(task, context, packet_limit=PACKETS, step_limit=LIMITS['bound_steps'],
                               seconds=480., save_queries=True, on_position_budget=observe)
    gold = json.loads(context.input_path(model+'-gold').read_bytes())
    actual = digest((context.directory/'bounds.json').read_bytes())
    matches = actual == gold['bounds_sha256'] and result['work'] == gold['packet_work']
    outcome = dict(model=model, budget=budgets, unchanged_bounds=matches, bounds_sha256=actual,
                   passed=result['passed'] and matches, scientific_decision='abstain')
    context.save('position-budget.json', outcome)
    return outcome


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        rows = {}
        for model in MODELS:
            record = study.envelope(model)
            item = record['result']
            if (record['status'] != 'complete' or record['charged'] != LIMITS
                    or item != study.artifact(model, 'position-budget.json')
                    or item['budget'] != [study.artifact(model, f'budget-{i:02d}.json') for i in range(len(INDICES))]):
                raise ValueError('complete budget and exact charged trace required')
            rows[model] = item
        result = dict(rows=rows, completion=study.completion)
    _write_equal(root/RESULT, encoded(result))
    return {model: row['passed'] for model, row in rows.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    value = qualification(root, verify=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(value, sort_keys=True))
