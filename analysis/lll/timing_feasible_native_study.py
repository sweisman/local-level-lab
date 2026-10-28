# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six exposed regression definitions; shared native worker and auditor."""
from lll.timing_feasible_study import TESTS as ANALYTICAL_TESTS
IDENTITY='timing-feasible-native-regression-20261027'
PLAN='docs/TIMING_FEASIBLE_NATIVE_PLAN.md'
ADAPTER='analysis/lll/timing_feasible_native_study.py'
SCOPE='six exposed feasible-start native regressions; no calibration, original or protected observations'
GATE='docs/timing-feasible-optimizer-qualification'
GATE_MANIFEST='6817fc26d467d791722f0ee4ac290e368e99c5ae6320c3ece96ed1ea9f004ae3'
GATE_SUMMARY='003aa3cb3951ba2935a5dcf7264f502cdd19c3cebc4a96e142c6ba88f35d7390'
LATEST='docs/prediction-calibration-timing'
LATEST_MANIFEST='c790afcb47fd0d142ebb2006c0ff5e182458f7993eaef7a466c34a971947cb42'
LATEST_SUMMARY='1214749f96e6cd274670be1b636700878dd4f11d92cf82da18e10fac68a0d83e'
SEEDS=(281474977010692,281474977010693,281474977210667)
POPULATIONS={s:('45e7fd8a1dcc11b713103dc2d9298515aa16def755a9007cc4387f9482909071'
    if s==SEEDS[-1] else '61b5a76d0eb4adaf14cb217fa400339bcd7e21f0c22e9d92b82625202b63f828') for s in SEEDS}
expected_point_count=6
TESTS=ANALYTICAL_TESTS+['analysis/tests/'+name for name in (
    'test_timing_feasible_native_study.py','test_timing_optimizer_native_study.py',
    'test_timing_optimizer_native_report.py','test_timing_native_providers.py',
    'test_structured_noisy_study.py','test_ilvis0_solver_trust_v2.py','test_ilvis0_near_zero.py',
    'test_timing_matrix_study.py','test_timing_local_native_study.py','test_ilvis0_training_forecast.py')]
allowed_source_updates=('analysis/lll/timing_cells.py','analysis/lll/timing_optimizer_native_study.py',
                        'analysis/lll/timing_optimizer_native_report.py')
required_tests=['test_native_reference_count_preserves_four_and_accepts_explicit_six',
    'test_native_reference_replay_audit_requires_all_six_and_preserves_four_default',
    'test_feasible_native_has_six_unchanged_cases_and_exact_finite_caps',
    'test_feasible_native_keeps_original_cohorts_separate',
    'test_six_reference_worker_checks_inventory_before_native_work_and_keeps_charges[4]',
    'test_six_reference_worker_checks_inventory_before_native_work_and_keeps_charges[6]']
required_report_tests=['test_native_reference_replay_audit_requires_all_six_and_preserves_four_default',
    'test_native_matrix_audit_keeps_all_declared_profile_columns[26]',
    'test_native_matrix_audit_keeps_all_declared_profile_columns[27]']


def configuration():
    from lll.timing_optimizer_native_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE,maximum_fits=6,maximum_wall_s=5400.)


def case_recipe(seed):
    if type(seed) is not int or seed not in SEEDS:raise ValueError('one of three exposed regression seeds required')
    if seed==SEEDS[-1]:
        from lll.timing_prediction_release import case_recipe as recipe
    else:
        from lll.timing_optimizer_native_study import case_recipe as recipe
    return recipe(seed)


def tasks():
    from lll.structured_noisy_training import tasks as matrix
    rows=[]
    for seed in SEEDS:
        law,profile=('increment',False) if seed==SEEDS[-1] else ('point',True)
        for t in matrix(case_recipe(seed)):
            p=t['payload']
            if (p['law'],p['model'],p['profile'])==(law,'sphere_rotating',profile):
                rows.append(dict(identity=f"feasible-seed-{seed}-{law}-sphere_rotating-{int(profile)}-{p['start']}",
                    input_key='points',native_kind='tangent',payload=dict(draw_seed=seed,case=p),limits=t['limits']))
    if len(rows)!=6:raise ValueError('all six prescribed regression starts required')
    return rows


def computational_payload(original):
    from lll.timing_optimizer_native_study import computational_payload as shared
    seed=original['draw_seed']
    if type(seed) is not int or seed not in POPULATIONS:raise ValueError('exposed source cohort required')
    return shared(original,population=POPULATIONS[seed])


def column_count(spec):return 27 if spec['profile'] else 26


def pair_key(task):
    p=task['payload'];s=p['case']
    return p['draw_seed'],s['law'],s['model'],s['profile']


def pair_metadata(key):return dict(zip(('seed','law','model','profile'),key,strict=True))


def row_metadata(task):return {k:task['payload']['case'][k] for k in ('law','model','profile')}


def verify_gate(report,binding,current,environment):
    from lll.timing_optimizer_native_study import verify_gate as shared
    return shared(report,binding,current,environment,expected=dict(complete=44,fit_passed=36,pairs=9,
        manifest_sha256=GATE_MANIFEST,summary_sha256=GATE_SUMMARY))


def gate_report(root):
    from lll import timing_feasible_study as definition
    from lll.timing_stopping_report import inspect
    return inspect(root,GATE,definition=definition)


def selection(root):
    from lll import timing_optimizer_native_study as original
    from lll.studies.closed import ClosedStudy
    from lll.studies.artifacts import digest,encoded
    from lll.airquantumgrav_inventory import environment
    points,_=original.selection(root)
    s=ClosedStudy(root,LATEST)
    try:
        if (s.completion['manifest_sha256']!=LATEST_MANIFEST or s.completion['summary_sha256']!=LATEST_SUMMARY
                or s.input('qualification-environment')!=environment()):
            raise ValueError('exact closed latest calibration and unchanged environment required')
        for t in tasks()[4:]:
            p=t['payload'];identity=f"calibration-seed-{p['draw_seed']}-increment-sphere_rotating-0-{p['case']['start']}"
            old=s.tasks[identity];envelope=s.envelope(identity);fit=s.artifact(identity,'fit.json')
            if (computational_payload(old['payload'])!=p or fit['converged']
                    or len(fit['active_parameters'])!=26
                    or fit['stability_probe'].get('reason')!='timing_cell_not_stable'):
                raise ValueError('both exact exposed timing failures required')
            artifacts={name:s.artifact(identity,name) for name in
                ('input-binding.json','training-observations.json','training-error-operator.json')}
            point=dict(identity=identity,payload=old['payload'],saved_converged=False,artifacts=artifacts,
                artifact_sha256={name:envelope['artifacts']['artifacts/'+identity+'/'+name]
                    for name in ('fit.json',*artifacts)},source_completion=s.completion)
            point['selection_sha256']=digest(encoded(point));points.append(point)
        if (len(points)!=6 or len({p['identity'] for p in points})!=6
                or [computational_payload(p['payload']) for p in points]!=[t['payload'] for t in tasks()]):
            raise ValueError('all six original input bindings required in declared order')
        return points,s.manifest['sources']
    finally:s.close()


def sources(root):
    from lll.timing_optimizer_native_study import sources as original
    from lll.studies.dependencies import source_closure
    return source_closure(root,original(root)+TESTS+[ADAPTER,PLAN])


def prepare(root,*,qualification):
    import sys
    from lll.timing_optimizer_native_study import prepare as shared
    return shared(root,qualification=qualification,definition=sys.modules[__name__])


def evaluate(task,context):
    import sys
    from lll.timing_optimizer_native_study import run_task
    return run_task(task,context,definition=sys.modules[__name__])
