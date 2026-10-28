# SPDX-License-Identifier: AGPL-3.0-or-later
"""48-case local-timing policy; shared execution, accounting and audit components."""
from lll.timing_optimizer_native_study import NUMERICAL,ADAPTERS
IDENTITY='timing-local-matrix-20261027'
PLAN='docs/TIMING_LOCAL_MATRIX_PLAN.md'
ADAPTER='analysis/lll/timing_optimizer_matrix_study.py'
SCOPE='48 exposed development-family local-timing optimizer controls; no calibration, original or protected data'
GATE='docs/timing-local-native-regression'
GATE_MANIFEST='d8245a4b37aafc3653b2bdcc0def2dec357be5eef6430f0f5b54dfb69b1bf9e8'
GATE_SUMMARY='f0ca77d348ffd8bf3e32a899f2ff182179fa6c248481c0017fa4dada301278d6'
ORIGINAL_POPULATION='bc181e9ad9b761e6715a1c7edc96469a2683e4edec7011220e29f06241c133bf'
require_original_match=False
gate_environment_input='qualification-environment'
allowed_source_updates=NUMERICAL+ADAPTERS+(
    'analysis/lll/timing_optimizer_native_study.py','analysis/lll/timing_optimizer_native_report.py')
required_tests=['test_timing_matrix_keeps_all_old_computational_cases_and_exact_caps',
    'test_timing_matrix_requires_complete_same_source_native_regression[source]',
    'test_matrix_worker_uses_shared_execution_and_explicit_optional_original_matches',
    'test_matrix_shared_worker_preserves_original_matches_and_charges[False]',
    'test_matrix_shared_worker_preserves_original_matches_and_charges[True]']
required_report_tests=['test_native_matrix_audit_keeps_all_declared_profile_columns[26]',
    'test_native_matrix_audit_keeps_all_declared_profile_columns[27]']


def configuration():
    from lll.timing_optimizer_native_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE,maximum_fits=48,maximum_wall_s=7200.)


def case_recipe(seed):
    from lll.coordinate_optimizer_study import case_recipe as original
    return original(seed)


def tasks():
    from lll.coordinate_optimizer_study import tasks as original
    return [dict(t,input_key='points') for t in original()]


def computational_payload(original):
    from lll.timing_optimizer_native_study import computational_payload as shared
    return shared(original,population=ORIGINAL_POPULATION)


def pair_key(task):
    p=task['payload'];s=p['case']
    return p['draw_seed'],s['law'],s['model'],s['profile']


def pair_metadata(key):
    return dict(zip(('seed','law','model','profile'),key,strict=True))


def row_metadata(task):
    return {k:task['payload']['case'][k] for k in ('law','model','profile')}


def column_count(spec):return 27 if spec['profile'] else 26


def verify_gate(report,binding,current,environment):
    from lll.timing_optimizer_native_study import NUMERICAL
    if (report.get('verified') is not True or report.get('native_qualified') is not True
            or report.get('selected')!=4 or report.get('complete')!=4 or report.get('failures')
            or report.get('original_binding_replays_exact') is not True or len(report.get('rows',[]))!=4
            or len(report.get('pairs',[]))!=2 or not all(r['passed'] for r in report['rows']+report['pairs'])
            or report.get('manifest_sha256')!=GATE_MANIFEST or report.get('summary_sha256')!=GATE_SUMMARY
            or set(binding.get('sources',{}))!=set(NUMERICAL) or binding.get('environment')!=environment
            or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete unchanged native qualification and numerical environment required')


def gate_report(root):
    from lll import timing_optimizer_local_study as definition
    from lll.timing_optimizer_native_report import inspect
    return inspect(root,GATE,definition=definition)


def selection(root):
    from lll.studies.closed import ClosedStudy
    s=ClosedStudy(root,'docs/compensated-optimizer-qualification')
    try:
        if (s.completion['manifest_sha256']!='651ac3a31d5300353dd3e6aab64a6e494e326fbd78c173ffeae0b8daf594d2f3'
                or s.completion['summary_sha256']!='2e7d23b7c40b5bfea9892cb6fa497daf1bb5cf38f1d934a77cc386574a02020b'):
            raise ValueError('original closed 48-case input source required')
        points=s.input('saved-points');expected=[t['payload'] for t in tasks()]
        old_tasks=[{k:v for k,v in t.items() if k not in ('index','shard','input_key')} for t in s.manifest['tasks']]
        current_tasks=[{k:v for k,v in t.items() if k!='input_key'} for t in tasks()]
        if old_tasks!=current_tasks:raise ValueError('original complete 48-case computational matrix required')
        if (len(points)!=4 or len({p['identity'] for p in points})!=4
                or any(computational_payload(p['payload']) not in expected for p in points)):
            raise ValueError('four exact original exposed input bindings required')
    finally:s.close()
    s=ClosedStudy(root,GATE)
    try:
        if s.completion['manifest_sha256']!=GATE_MANIFEST or s.completion['summary_sha256']!=GATE_SUMMARY:
            raise ValueError('qualified native source baseline required')
        return points,s.manifest['sources']
    finally:s.close()


def sources(root):
    from lll.timing_optimizer_native_study import sources as original
    from lll.studies.dependencies import source_closure
    return source_closure(root,original(root)+[ADAPTER,PLAN,'analysis/tests/test_timing_matrix_study.py',
        'analysis/tests/test_timing_local_native_study.py'])


def prepare(root,*,qualification):
    import sys
    from lll import timing_optimizer_native_study as shared
    return shared.prepare(root,qualification=qualification,definition=sys.modules[__name__])


def evaluate(task,context):
    import sys
    from lll.timing_optimizer_native_study import run_task
    return run_task(task,context,definition=sys.modules[__name__])
