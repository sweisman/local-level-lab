# SPDX-License-Identifier: AGPL-3.0-or-later
"""Longer generated, independently seeded solver forecast confirmation."""

import json
from pathlib import Path

from .ilvis0_fullcal_solver_pilot import recipe as pilot_recipe
from .ilvis0_multimodel_solver_study import MODELS,SOLVERS
from . import ilvis0_solver_matrix_core as core

ID='ilvis0-long-solver-confirmation-v1-20261118'
PREFLIGHT_ID=ID+'-preflight'
PLAN='docs/prediction-group-transfer/LONG_HORIZON_SOLVER_PLAN.md'
REQUEST='docs/prediction-group-transfer/long-solver-qualification-request.json'
REPORT='docs/prediction-group-transfer/long-solver-qualification-tests.xml'
RECOVERY='docs/prediction-group-transfer/remaining-recovery-request.json'
SCOPE='six longer generated model/clock histories; no aircraft input'
PREFLIGHT_SCOPE='one short long-solver real-worker wiring check'
CLOCKS=('header_elapsed','nominal_200Hz')


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
        seed=2026111901+MODELS.index(model)*len(CLOCKS)+CLOCKS.index(clock)
        r=dict(pilot_recipe(),version='ilvis0-long-solver-preflight-v1'
               if preflight else 'ilvis0-long-solver-confirmation-v1',
               models=[model],sensor_case='z_gyro_boundary',
               rate_hz=200 if clock=='nominal_200Hz' else 300,
               clock=clock,noise_by_law=dict(increment=noise_settings(seed=seed)),
               duration_s=10. if preflight else 120.,
               queries=9 if preflight else 119,
               starts=1 if preflight else 2,
               workers=1 if preflight else 4,
               maximum_wall_s=900. if preflight else 21600.)
        if preflight:r['maximum_evaluations']=8
        result[case_key(model,clock)]=r
    return result


def tasks(*,preflight=False):
    return core.make_tasks(recipes(preflight=preflight),solvers=SOLVERS,
                           preflight=preflight)


def sources(root):
    from .studies.dependencies import source_closure
    return source_closure(Path(root).resolve(),[
        'analysis/lll/ilvis0_long_solver_study.py',
        'analysis/lll/ilvis0_solver_matrix_core.py',
        'analysis/lll/ilvis0_fullcal_solver_pilot.py',
        'analysis/lll/ilvis0_multimodel_solver_study.py',
        'analysis/lll/structured_noisy_study.py',
        'analysis/lll/structured_noisy_training.py',
        'analysis/lll/ilvis0_near_zero.py',
        'analysis/lll/ilvis0_solver_trust_v2.py',
        'analysis/lll/ilvis0_tangent.cpp',
        'analysis/lll/ilvis0_noise_bridge.cpp',
        'analysis/tests/test_ilvis0_long_solver_study.py',
        'analysis/tests/test_structured_noisy_study.py',PLAN])


def required_tests():
    return ('test_six_histories_cover_models_clocks_and_distinct_seeds',
            'test_twenty_four_bounded_tasks_and_separate_preflight',
            'test_freeze_contains_shared_worker_native_and_recovery',
            'test_changed_task_rejected_before_generated_input_access',
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
        adapter='analysis/lll/ilvis0_long_solver_study.py',
        sources=sources,recipes=recipes,tasks=tasks,request_path=REQUEST,
        recovery_path=RECOVERY,required_tests=required_tests,
        qualification=qualification,preflight=preflight)


def evaluate(task,context):
    return core.evaluate(task,context,scope=SCOPE,
        preflight_scope=PREFLIGHT_SCOPE,recipes=recipes,tasks=tasks)


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
