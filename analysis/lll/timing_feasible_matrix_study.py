# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full exposed matrix after feasible-start qualification; shared worker/audit."""
from lll.timing_optimizer_matrix_study import (
    tasks,case_recipe,computational_payload,pair_key,pair_metadata,row_metadata,column_count)
from lll.timing_feasible_native_study import TESTS as NATIVE_TESTS

IDENTITY='timing-feasible-matrix-20261027'
PLAN='docs/TIMING_FEASIBLE_MATRIX_PLAN.md'
ADAPTER='analysis/lll/timing_feasible_matrix_study.py'
SCOPE='48 exposed feasible-start native matrix controls; no calibration, original or protected observations'
GATE='docs/timing-feasible-native-regression'
GATE_MANIFEST='f2c63e792616bcaf9909a61da562339314935f552f3d1df73fbf7395e41bbd6b'
GATE_SUMMARY='b9031118b5a3d5fef32e6907e33dcc339c4f15698dead97bacddbad9aaa02adf'
gate_environment_input='qualification-environment'
require_original_match=False
expected_point_count=4
TESTS=NATIVE_TESTS+['analysis/tests/test_timing_feasible_matrix_study.py']
# The gate's execution freeze predates its reporting-only metadata repair.
# None of its seven numerical method bodies may change.
allowed_source_updates=('analysis/lll/timing_optimizer_native_report.py',
                        'analysis/tests/test_timing_feasible_native_study.py')
required_tests=['test_feasible_matrix_keeps_48_original_cases_and_closed_allowances',
    'test_feasible_matrix_requires_all_six_corrected_native_regressions[source]',
    'test_feasible_matrix_uses_shared_worker_and_six_case_auditor',
    'test_feasible_matrix_keeps_four_old_references_but_binds_new_native_sources']
required_report_tests=['test_native_matrix_audit_keeps_all_declared_profile_columns[26]',
    'test_native_matrix_audit_keeps_all_declared_profile_columns[27]',
    'test_native_auditor_reference_count_survives_original_point_variable_shadowing']


def configuration():
    from lll.timing_optimizer_matrix_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE)


def verify_gate(report,binding,current,environment):
    from lll.timing_optimizer_native_study import NUMERICAL
    if (report.get('verified') is not True or report.get('native_qualified') is not True
            or report.get('selected')!=6 or report.get('complete')!=6 or report.get('failures')
            or report.get('original_binding_replays_exact') is not True or len(report.get('rows',[]))!=6
            or len(report.get('pairs',[]))!=3 or not all(r['passed'] for r in report['rows']+report['pairs'])
            or report.get('manifest_sha256')!=GATE_MANIFEST or report.get('summary_sha256')!=GATE_SUMMARY
            or set(binding.get('sources',{}))!=set(NUMERICAL) or binding.get('environment')!=environment
            or any(current.get(k)!=v for k,v in binding['sources'].items())):
        raise ValueError('complete unchanged six-case native qualification and environment required')


def gate_report(root):
    from lll import timing_feasible_native_study as definition
    from lll.timing_optimizer_native_report import inspect
    return inspect(root,GATE,definition=definition)


def selection(root):
    from lll.timing_optimizer_matrix_study import selection as original
    from lll.studies.closed import ClosedStudy
    points,_=original(root)  # Validates the original 48 payloads and four references.
    s=ClosedStudy(root,GATE)
    try:
        if s.completion['manifest_sha256']!=GATE_MANIFEST or s.completion['summary_sha256']!=GATE_SUMMARY:
            raise ValueError('qualified six-case native source baseline required')
        return points,s.manifest['sources']
    finally:s.close()


def sources(root):
    from lll.timing_optimizer_matrix_study import sources as original
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
