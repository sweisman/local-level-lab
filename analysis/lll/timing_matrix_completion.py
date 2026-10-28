# SPDX-License-Identifier: AGPL-3.0-or-later
"""Proposed four-case completion controls; original interrupted study stays closed."""
from lll.timing_feasible_matrix_study import (
    GATE,GATE_MANIFEST,GATE_SUMMARY,gate_environment_input,gate_report,verify_gate,
    case_recipe,computational_payload,pair_key,pair_metadata,row_metadata,column_count)
from lll.timing_feasible_matrix_study import TESTS as MATRIX_TESTS

IDENTITY='timing-matrix-completion-20261028'
ADAPTER='analysis/lll/timing_matrix_completion.py'
PLAN='docs/TIMING_MATRIX_COMPLETION_PLAN.md'
SCOPE='four proposed exposed native completion controls; no reopening, original or protected observations'
MATRIX='docs/timing-feasible-matrix'
MATRIX_MANIFEST='625e8b32523807a3ca6f6dcb28665dbc6818e7e3435366fd36e6f4d60fa3b5cc'
MATRIX_SUMMARY='690b3db8286b54c6ae4358f08969a1424586497b9f4e49f4f4f6e85f6cff0dff'
TESTS=MATRIX_TESTS+['analysis/tests/test_timing_matrix_completion.py']
expected_point_count=1
require_original_match=False
allowed_source_updates=()
required_tests=['test_matrix_completion_is_four_new_starts_without_reopening_closed_matrix',
    'test_matrix_completion_only_accepts_exact_four_runtime_interruptions[reason]',
    'test_matrix_completion_reference_is_only_the_original_binding_in_missing_slice']
required_report_tests=['test_native_matrix_audit_keeps_all_declared_profile_columns[26]',
    'test_native_matrix_audit_keeps_all_declared_profile_columns[27]',
    'test_native_auditor_reference_count_survives_original_point_variable_shadowing']


def configuration():
    from lll.timing_feasible_matrix_study import configuration as original
    return dict(original(),id=IDENTITY,scope=SCOPE,maximum_fits=4,maximum_wall_s=3600.)


def tasks():
    from lll.timing_feasible_matrix_study import tasks as original
    return original()[:4]


def verify_interrupted_matrix(report):
    from lll.timing_feasible_matrix_study import tasks as original
    expected={t['identity'] for t in original()};missing={t['identity'] for t in tasks()}
    rows=report.get('rows',[]);failures=report.get('failures',[]);pairs=report.get('pairs',[])
    if (report.get('verified') is not True or report.get('selected')!=48 or report.get('complete')!=44
            or report.get('manifest_sha256')!=MATRIX_MANIFEST or report.get('summary_sha256')!=MATRIX_SUMMARY
            or len(rows)!=44 or {r['identity'] for r in rows}!=expected-missing
            or not all(r['passed'] for r in rows) or report.get('verification_failures')
            or len(failures)!=4 or {r['identity'] for r in failures}!=missing
            or any(r['reason']!='charged work interrupted; not retried' for r in failures)
            or len(pairs)!=24 or sum(r['passed'] for r in pairs)!=22):
        raise ValueError('exact closed runtime-interrupted matrix with 44 passing fits required')


def select_reference(points):
    payloads=[t['payload'] for t in tasks()]
    selected=[p for p in points if computational_payload(p['payload']) in payloads]
    if len(selected)!=1:raise ValueError('one unchanged original binding in missing slice required')
    return selected


def selection(root):
    from lll import timing_feasible_matrix_study as matrix
    from lll.timing_optimizer_native_report import inspect
    from lll.studies.closed import ClosedStudy
    report=inspect(root,MATRIX,definition=matrix);verify_interrupted_matrix(report)
    s=ClosedStudy(root,MATRIX)
    try:
        if any(s.envelope(t['identity'])['status']!='interrupted' for t in tasks()):
            raise ValueError('all four missing starts must retain interrupted envelopes')
        return select_reference(s.input('points')),s.manifest['sources']
    finally:s.close()


def sources(root):
    from lll.timing_feasible_matrix_study import sources as original
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
