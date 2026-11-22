# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite 120-second generated SciPy-TRF versus trust-region comparison."""

import json
from pathlib import Path

from .ilvis0_fullcal_solver_pilot import recipe as pilot_recipe
from .ilvis0_multimodel_solver_study import MODELS
from . import ilvis0_solver_matrix_core as core

ID='ilvis0-long-independent-solver-v1-20261118'
PREFLIGHT_ID=ID+'-preflight'
PLAN='docs/prediction-group-transfer/LONG_INDEPENDENT_SOLVER_PLAN.md'
REQUEST='docs/prediction-group-transfer/long-independent-solver-qualification-request.json'
REPORT='docs/prediction-group-transfer/long-independent-solver-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE='six 120-second generated distinct-optimizer histories; no aircraft input'
PREFLIGHT_SCOPE='one short SciPy real-worker check for long independent study'
CLOCKS=('header_elapsed','nominal_200Hz')
SOLVERS=('trust_v2','scipy_trf')


def case_key(model,clock):
    if model not in MODELS or clock not in CLOCKS:
        raise ValueError('declared model and clock required')
    return model+'-'+clock


def recipes(*,preflight=False):
    from .airquantumgrav_noisy_inputs import noise_settings
    pairs=((('flat_still','nominal_200Hz'),) if preflight else
           tuple((model,clock) for model in MODELS for clock in CLOCKS))
    result={}
    for model,clock in pairs:
        seed=2026111921+MODELS.index(model)*len(CLOCKS)+CLOCKS.index(clock)
        r=dict(pilot_recipe(),version='ilvis0-long-independent-preflight-v1'
               if preflight else 'ilvis0-long-independent-solver-v1',
               models=[model],sensor_case='z_gyro_boundary',
               rate_hz=200 if clock=='nominal_200Hz' else 300,
               clock=clock,noise_by_law=dict(increment=noise_settings(seed=seed)),
               duration_s=10. if preflight else 120.,
               queries=9 if preflight else 119,
               starts=1 if preflight else 2,
               workers=1 if preflight else 4,
               maximum_wall_s=900. if preflight else 21600.)
        if preflight:r['maximum_evaluations']=30
        result[case_key(model,clock)]=r
    return result


def tasks(*,preflight=False):
    from .structured_noisy_training import limits
    declared=recipes(preflight=preflight)
    if not preflight:
        return core.make_tasks(declared,solvers=SOLVERS)
    key,r=next(iter(declared.items()))
    return [dict(identity=f'{key}-scipy_trf-0',input_key=key,
        native_kind='tangent',payload=dict(model=r['models'][0],
            sensor_case=r['sensor_case'],solver='scipy_trf',law='increment',
            latitude_deg=55.,profile=False,start=0,
            policy_id='reported-short-v1'),
        limits=limits(r,'increment')[0])]


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_long_independent_solver_study.py',
        'analysis/lll/ilvis0_solver_matrix_core.py',
        'analysis/lll/ilvis0_independent_scipy_adapter.py',
        'analysis/lll/independent_bounded_solver.py',
        'analysis/lll/ilvis0_fullcal_solver_pilot.py',
        'analysis/lll/ilvis0_multimodel_solver_study.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/ilvis0_solver_trust_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_ilvis0_long_independent_solver_study.py',
        'analysis/tests/test_ilvis0_independent_scipy_adapter.py',
        'analysis/tests/test_structured_noisy_study.py',PLAN])


def required_tests():
    return ('test_six_long_histories_cover_models_clocks_and_distinct_seeds',
            'test_twenty_four_distinct_optimizer_tasks_and_scipy_preflight',
            'test_long_freeze_includes_independent_solver_and_recovery',
            'test_changed_long_task_rejected_before_generated_input_access',
            'test_independent_scipy_method_recovers_known_optimum_and_counts_calls',
            'test_uncounted_problem_is_rejected_before_optimizer',
            'test_worker_prepays_native_work_and_keeps_construction_separate',
            'test_worker_preserves_prepayment_and_artifacts_after_failure',
            'test_reboot_resume_skips_sealed_and_preserves_charges',
            'test_source_input_environment_mutation_blocks',
            'test_recovery_caps_and_completed_failure')


def request_qualification(root):
    return core.request_qualification(root,sources=sources,
        request_path=REQUEST,report_path=REPORT)


def prepare(root,*,qualification,preflight=False):
    return core.prepare(root,name=ID,preflight_name=PREFLIGHT_ID,
        scope=SCOPE,preflight_scope=PREFLIGHT_SCOPE,
        adapter='analysis/lll/ilvis0_long_independent_solver_study.py',
        sources=sources,recipes=recipes,tasks=tasks,request_path=REQUEST,
        recovery_path=RECOVERY,required_tests=required_tests,
        qualification=qualification,preflight=preflight)


def evaluate(task,context):
    from .airquantumgrav_prediction import train_and_forecast
    from .ilvis0_independent_scipy_adapter import fit_candidate as scipy_trf
    from .ilvis0_solver_trust_v2 import fit_candidate as trust_v2
    from .structured_noisy_study import run_case
    scope=context.manifest['scope']
    preflight=scope==PREFLIGHT_SCOPE
    declared={key:value for key,value in task.items()
              if key not in ('index','shard')}
    if (scope not in (SCOPE,PREFLIGHT_SCOPE) or
            declared not in tasks(preflight=preflight)):
        raise ValueError('unchanged finite long independent task required')
    key=task['input_key'];r=recipes(preflight=preflight)[key]
    if (json.loads(context.input_path(key).read_bytes())!=r or
            json.loads(context.input_path('environment').read_bytes())!=
                core.guarded_environment()):
        raise ValueError('changed long independent recipe or environment')
    solver=scipy_trf if task['payload']['solver']=='scipy_trf' else trust_v2
    def protocol(**kwargs):
        return train_and_forecast(**kwargs,solver_provider=solver)
    payload={key:value for key,value in task['payload'].items()
             if key not in ('solver','sensor_case')}
    result=run_case(task,context,r=r,payload=payload,
                    training_provider=protocol)
    cut=2*r['queries']//3
    if (result.get('forecast_saved_before_scoring') is not True or
            result.get('training_epochs')!=cut or
            result.get('prediction_epochs')!=r['queries']-cut or
            result.get('original_reads')!=0 or
            result.get('protected_reads')!=0):
        raise ValueError('complete earlier-only generated worker required')
    return dict(result,passed=True,technical_completion_only=True,
        preflight_only=preflight,
        physical_accuracy_passed=bool(result['passed']),
        solver=task['payload']['solver'],
        sensor_case=task['payload']['sensor_case'],
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('request','prepare-preflight',
                                         'run-preflight','prepare','run'))
    args=parser.parse_args(argv)
    root=Path('.').resolve()
    if args.action=='request':result=request_qualification(root)
    elif args.action.startswith('prepare'):
        result=prepare(root,qualification=REQUEST,
                       preflight=args.action=='prepare-preflight')
    else:
        from .ilvis0_control_shards import launch
        name=PREFLIGHT_ID if args.action=='run-preflight' else ID
        summary=launch(root/'data'/name,reserved_threads=0)
        result={key:summary[key] for key in
                ('state','completed','total','passed','charged')}
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
