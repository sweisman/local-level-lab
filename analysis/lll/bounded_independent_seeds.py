# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind the complete bounded-aircraft matrix to two new noise realizations."""
import json
from pathlib import Path

from lll.airquantumgrav_noisy_inputs import noise_settings, rate_point_noise_settings
from lll.bounded_nonlinear_study import recipe as original_recipe
from lll.bounded_nonlinear_study import tasks as original_tasks


SEEDS = (314159, 161803)
IDENTITY = 'bounded-nonlinear-independent-seeds-v2'
SCOPE = ('48 generated two-minute bound-aware aircraft cases on two independent '
         'seeds; no observed or protected data; no scientific decision')


def seeded_recipe(seed):
    if seed not in SEEDS or type(seed) is not int:
        raise ValueError('one of two frozen independent generator seeds required')
    r = original_recipe()
    r['noise_by_law'] = dict(increment=noise_settings(seed=seed),
                             point=rate_point_noise_settings(seed=seed))
    return r


def tasks():
    rows = []
    for seed in SEEDS:
        for parent in original_tasks(original_recipe()):
            rows.append(dict(parent,
                identity=f'seed{seed}-{parent["identity"]}',
                input_key='protocol',
                payload=dict(parent['payload'], seed=seed,
                             parent_identity=parent['identity'])))
    if len(rows) != 48 or len({row['identity'] for row in rows}) != 48:
        raise ValueError('complete independent 48-case matrix required')
    return rows


def adapted_task(task):
    frozen = {key: value for key, value in task.items()
              if key not in ('index', 'shard')}
    if frozen not in tasks():
        raise ValueError('unchanged frozen seed/task binding required')
    payload = {key: value for key, value in task['payload'].items()
               if key not in ('seed', 'parent_identity')}
    return dict(task, payload=payload)


def require_result(result):
    if (not isinstance(result, dict) or
            type(result.get('passed')) is not bool or
            result.get('scientific_decision') != 'abstain'):
        raise ValueError('explicit scientific abstention and boolean result required')
    return result


def protocol():
    base = original_recipe()
    return dict(version='bounded-independent-seeds-v1', seeds=list(SEEDS),
                total_tasks=48, workers=4, threads=1,
                maximum_wall_s=18000.,
                maximum_evaluations_per_fit=base['maximum_evaluations'],
                per_task_limits=tasks()[0]['limits'],
                base_recipe=base, scientific_decision='abstain',
                observed_reads=0, protected_reads=0)


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/bounded_independent_seeds.py',
        'analysis/lll/bounded_nonlinear_study.py',
        'analysis/tests/test_bounded_independent_seeds.py',
        'docs/bounded-calibration-prediction/INDEPENDENT_SEEDS_PLAN.md'])


def request_qualification(root):
    from lll.airquantumgrav_inventory import environment
    from lll.studies.qualification import request
    return request(Path(root).resolve(), sources=qualification_sources(root),
                   environment=environment(),
                   output='docs/bounded-calibration-prediction/qualification/independent-seeds-v2-request.json',
                   report='docs/bounded-calibration-prediction/qualification/independent-seeds-v2-tests.xml')


def prepare(root, *, qualification,
            recovery_qualification='docs/bounded-calibration-prediction/qualification/recovery-request.json'):
    from lll.airquantumgrav_inventory import environment
    from lll.compute_budget import environment as thread_environment
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.artifacts import atomic, encoded
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                          REQUIRED_TESTS as recovery_tests)
    root = Path(root).resolve()
    setting = environment()
    if setting['numerical_environment'] != thread_environment(workers=4, threads=1):
        raise ValueError('guarded four-thread numerical allocation required')
    source_request, source_report = checked(root, qualification,
        sources=qualification_sources(root), environment=setting,
        required_tests=[
            'test_independent_seed_matrix_preserves_all_24_original_conditions',
            'test_independent_seed_adapter_strips_only_seed_metadata',
            'test_independent_seed_result_contract_rejects_missing_abstention',
            'test_independent_seed_protocol_has_finite_four_thread_allocation',
            'test_independent_seed_evaluate_passes_exact_seed_to_shared_worker'],
        minimum_tests=5)
    recovery_request, recovery_report = checked(root, recovery_qualification,
        sources=recovery_sources(root), environment=runtime_environment(),
        required_tests=recovery_tests, minimum_tests=len(recovery_tests))
    base = root / 'data' / (IDENTITY + '-inputs')
    if base.exists() or (root / 'data' / IDENTITY).exists():
        raise ValueError('fresh independent-seed study required')
    base.mkdir(parents=True)
    records = dict(protocol=encoded(protocol()),
                   qualification_request=source_request,
                   qualification_report=source_report,
                   qualification_environment=encoded(setting),
                   recovery_request=recovery_request,
                   recovery_report=recovery_report)
    inputs = {}
    for name, raw in records.items():
        path = base / (name + ('.xml' if name.endswith('_report') else '.json'))
        atomic(path, raw)
        inputs[name] = path.relative_to(root).as_posix()
    definition = dict(id=IDENTITY, scope=SCOPE,
                      adapter='analysis/lll/bounded_independent_seeds.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks(), workers=4, threads=1,
                      maximum_wall_s=protocol()['maximum_wall_s'])
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + IDENTITY, total=48,
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    from lll.airquantumgrav_inventory import environment
    from lll.bounded_nonlinear_study import run_case
    expected = {row['identity']: row for row in tasks()}
    frozen = {key: value for key, value in task.items()
              if key not in ('index', 'shard')}
    if (frozen != expected.get(task['identity']) or
            context.manifest['scope'] != SCOPE or
            json.loads(context.input_path('protocol').read_bytes()) != protocol() or
            json.loads(context.input_path('qualification_environment').read_bytes()) != environment()):
        raise ValueError('unchanged qualified independent-seed task required')
    seed = task['payload']['seed']
    result = run_case(adapted_task(task), context, r=seeded_recipe(seed))
    return require_result(result)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    result = (request_qualification(args.root) if args.action == 'request' else
              prepare(args.root, qualification=
                      'docs/bounded-calibration-prediction/qualification/independent-seeds-v2-request.json'))
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
