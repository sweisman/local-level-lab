# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite same-trajectory error scales for two sealed generated forecasts."""

import argparse
import json
from pathlib import Path

ID = 'esa-oracle-matched-scale-v1-20261115'
SCOPE = ('two matched generated oracle error scales; no fit, original or '
         'protected reads, or Earth-model decision')
PLAN = 'docs/prediction-observed-development/ORACLE_MATCHED_SCALE_DESIGN.md'
DIRECTORY = 'docs/prediction-observed-development/qualification/'
LAWS = ('increment', 'point')
LIMITS = dict(native_calls=270_900, packet_visits=270_900,
              bound_calls=0, bound_steps=0)
CONSTRUCTION = dict(generated_samples=270_901,
                    constructed_intervals=270_000, summary_epochs=300)


def recipe():
    return dict(version='esa-oracle-matched-scale-v1', laws=list(LAWS),
                duration_s=900., rate_hz=300, queries=900,
                query_start_s=.5, query_step_s=1., training_epochs=600,
                maximum_operator_bytes=64*1024**2,
                workers=2, threads=1, maximum_wall_s=7200.,
                random_draws=0, optimizer_starts=0,
                original_reads=0, protected_reads=0,
                scientific_decision='abstain')


def tasks():
    return [dict(identity=law, input_key='recipe', native_kind='tangent',
                 payload=dict(law=law, duration_s=900.), limits=dict(LIMITS))
            for law in LAWS]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(), [
        'analysis/lll/esa_oracle_matched_scale_study.py',
        'analysis/lll/esa_oracle_matched_scale_recovery.py',
        'analysis/lll/generated_noise_benchmark.py',
        'analysis/lll/noise_conditioning_comparison.py',
        'analysis/lll/noise_benchmark_study.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_esa_oracle_matched_scale_study.py', PLAN])


def request_qualification(root):
    from .airquantumgrav_inventory import environment
    from .studies.qualification import request
    return request(Path(root).resolve(), sources=sources(root),
                   environment=environment(),
                   output=DIRECTORY+'oracle-matched-scale-request.json',
                   report=DIRECTORY+'oracle-matched-scale-tests.xml')


def prepare(root, *, qualification=None, recovery_qualification=None):
    if qualification is None or recovery_qualification is None:
        raise ValueError('source and recovery qualification required')
    from .airquantumgrav_inventory import environment
    from .compute_budget import environment as numerical_environment
    from .ilvis0_control_shards import runtime_environment
    from .studies.artifacts import atomic, encoded, safe_path
    from .studies.closed import ClosedStudy
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import (qualification_sources as recovery_sources,
                                      REQUIRED_TESTS as recovery_tests)
    from .esa_oracle_clean_study import ID as CLEAN_ID
    from .esa_oracle_study import ID as NOISY_ID

    root = Path(root).resolve()
    staged = safe_path(root, 'data/'+ID+'-inputs')
    if staged.exists() or safe_path(root, 'data/'+ID).exists():
        raise ValueError('fresh finite matched-scale identity required')
    env = environment()
    if env['numerical_environment'] != numerical_environment(workers=2,threads=1):
        raise ValueError('guarded two-thread allocation required')
    checked(root, qualification, sources=sources(root), environment=env,
            required_tests=(
                'test_matched_scale_tasks_have_finite_allowance',
                'test_matched_scale_requires_qualification',
                'test_matched_scale_rejects_changed_task',
                'test_matched_scale_prepays_and_preserves_failure',
                'test_matched_scale_recovery_binds_two_tasks',
                'test_same_operator_scales_match_dense_unconditional_and_conditional'),
            minimum_tests=6)
    checked(root, recovery_qualification, sources=recovery_sources(root),
            environment=runtime_environment(),required_tests=recovery_tests,
            minimum_tests=len(recovery_tests))
    bindings = {}
    for key, parent in (('clean', CLEAN_ID), ('noisy', NOISY_ID)):
        study = ClosedStudy(root, 'data/'+parent)
        try:
            if (study.completion['state'] != 'complete' or
                    study.summary['completed'] != (1 if key=='clean' else 2)):
                raise ValueError('complete sealed oracle parents required')
            bindings[key] = study.completion['manifest_sha256']
            if key == 'clean':
                clean_hashes = study.artifact('clean','clean-forecast.json')[
                    'imu_array_sha256']
        finally:
            study.close()
    staged.mkdir(parents=True)
    inputs = {}
    for name, value in (('recipe',recipe()),
                        ('parent-binding',dict(bindings,clean_raw_sha256=clean_hashes)),
                        ('numerical-environment',env)):
        path=staged/(name+'.json');atomic(path,encoded(value))
        inputs[name]=path.relative_to(root).as_posix()
    definition=dict(id=ID,scope=SCOPE,
        adapter='analysis/lll/esa_oracle_matched_scale_study.py',
        sources=sources(root),inputs=inputs,tasks=tasks(),
        workers=2,threads=1,maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(staged/'definition.json',encoded(definition))
    manifest=Definition.from_dict(definition,root).prepare(root)
    return dict(path='data/'+ID,total=2,allocation=manifest['allocation'])


def evaluate(task,context):
    from .airquantumgrav_inventory import environment
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (context.manifest.get('scope') != SCOPE or
            declared != {row['identity']:row for row in tasks()}.get(task['identity']) or
            json.loads(context.input_path('recipe').read_bytes()) != recipe() or
            json.loads(context.input_path('numerical-environment').read_bytes()) != environment()):
        raise ValueError('unchanged matched-scale task and environment required')
    return run_case(task,context)


def run_case(task,context):
    from .studies.artifacts import digest
    from .studies.journal import Journal
    from .ilvis0_control_shards import _check_continue
    from .noise_benchmark_study import kernel
    from .generated_noise_benchmark import material,build_operator
    from .noise_conditioning_comparison import compare
    import numpy as np

    if task['limits'] != LIMITS:
        raise ValueError('finite matched-scale allowance changed')
    law=task['identity'];budget=None
    journal=Journal(context.directory/'construction.sqlite',
        freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={law:CONSTRUCTION})
    journal.start(law)
    def reserve_construction(**counts):
        _check_continue(context.root,context.manifest)
        for name,value in counts.items():journal.reserve(law,name,value)
    try:
        native=kernel(context)
        with context.prepay_native(native_calls=LIMITS['native_calls'],
                                   packet_visits=LIMITS['packet_visits']) as budget:
            data=material(duration_s=900.,queries=900,
                          query_start_s=.5,query_step_s=1.,
                          reserve=reserve_construction)
            binding=json.loads(context.input_path('parent-binding').read_bytes())
            actual={name:digest(np.asarray(data['raw_'+name] if name!='dt' else data[name],
                                        dtype='<f8').tobytes())
                    for name in ('theta','dv','dt')}
            if (data['training_epochs'] != 600 or
                    actual != binding['clean_raw_sha256']):
                raise ValueError('generated increments differ from sealed clean oracle')
            def reserve_native(**counts):
                if (counts != dict(native_calls=1,packet_steps=1)):
                    raise ValueError('one charged native step required')
                budget.reserve(native_calls=1,packet_visits=1)
            operator,_,descriptor=build_operator(
                data,law=law,kernel=native,reserve=reserve_native,
                maximum_bytes=recipe()['maximum_operator_bytes'])
            reserve_construction(summary_epochs=300)
            result=compare(operator,training_epochs=600,
                           physical_scales=data['nominal_metric'][600:])
            context.save('error-operator.json',descriptor)
            context.save('variance-comparison.json',result)
        journal.verify()
        if any(journal.count(law,key)!=value for key,value in CONSTRUCTION.items()):
            raise ValueError('matched-scale construction differs from allowance')
        return dict(passed=True,law=law,scientific_decision='abstain',
            unconditional_horizontal_rms_scale_m=result['unconditional'][
                'horizontal_rms_scale_m'],
            unconditional_height_rms_scale_m=result['unconditional'][
                'height_rms_scale_m'],
            native_calls_attempted=budget.snapshot()['attempted']['native_calls'],
            optimizer_starts=0,random_draws=0,original_reads=0,protected_reads=0,
            confidence_calibrated=False)
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(journal.path)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare'))
    parser.add_argument('--root',default='.')
    args=parser.parse_args(argv);root=Path(args.root).resolve()
    result=(request_qualification(root) if args.action=='request' else
            prepare(root,qualification=DIRECTORY+'oracle-matched-scale-request.json',
                    recovery_qualification=DIRECTORY+'oracle-matched-scale-recovery-request.json'))
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
