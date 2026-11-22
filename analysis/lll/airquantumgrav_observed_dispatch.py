# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded observed ESA comparison for model-declared tangent precision."""

import hashlib
import json
import math
from pathlib import Path

from lll.airquantumgrav_observed_hybrid import (
    evaluate_variant, prepare_variant,
    qualification_sources as original_sources,
    required_tests as original_tests,
    recipe as original_recipe,
    tasks as original_tasks,
)


IDENTITY = 'esa-observed-model-dispatch-globe-pairs-v2'
SCOPE = ('sixteen model-declared ESA globe pairs; saved recording-187 inputs; '
         'no original or protected reads; software substitution only')
GENERATED_PARENT = 'data/model-declared-paired-fit-20261115-v2'
GENERATED_MANIFEST = '8a8f0e687d8556f2d6e9e699d76acfee3abd0e34d116e74f8f3d1471656a8458'
GENERATED_SUMMARY = '227070f95c16d67bd545b91b1824c0648c1fcd2a5e7a7446e31b14c904a2ef2f'
SAVED_AUDIT = 'docs/mixed-tangent-hybrid/MODEL_DISPATCH_RESULT.json'
SAVED_AUDIT_SHA256 = 'f3558bbb8b0f760c738d888a6c6074570dd8f03ba3ddcb685d3317355c263ebd'
RECOVERY_REQUEST = 'docs/mixed-tangent-hybrid/observed-dispatch-recovery-request.json'
RECOVERY_PLAN = 'docs/mixed-tangent-hybrid/OBSERVED_DISPATCH_RECOVERY.md'


def recipe(*, maximum_wall_s):
    if (type(maximum_wall_s) not in (int, float) or
            not math.isfinite(maximum_wall_s) or
            not 0 < maximum_wall_s <= 108000):
        raise ValueError('explicit finite thirty-hour observed allowance required')
    return dict(original_recipe(maximum_wall_s=57600),
                version='esa-observed-model-dispatch-v1',
                workers=4, threads=1, maximum_wall_s=float(maximum_wall_s))


def tasks(layout):
    selected = [case for case in original_tasks(layout)
                if case['payload']['model'] in ('sphere_rotating',
                                                'sphere_still')]
    if (len(selected) != 16 or
            {case['payload']['model'] for case in selected} !=
            {'sphere_rotating', 'sphere_still'} or
            sum(case['limits']['native_calls'] for case in selected) != 6432 or
            sum(case['limits']['packet_visits'] for case in selected) !=
            1241944115200):
        raise ValueError('unchanged sixteen-case ESA globe matrix required')
    return selected


def sources(root):
    from lll.studies.dependencies import source_closure
    from lll.studies.task_resume import qualification_sources as recovery_sources

    return source_closure(root, [
        *original_sources(root),
        'analysis/lll/airquantumgrav_observed_dispatch.py',
        'analysis/lll/ilvis0_tangent_dispatch.py',
        'analysis/tests/test_airquantumgrav_observed_dispatch.py',
        'analysis/tests/test_task_resume.py',
        'docs/mixed-tangent-hybrid/OBSERVED_DISPATCH_PLAN.md',
        'docs/mixed-tangent-hybrid/OBSERVED_DISPATCH_V2_ADDENDUM.md',
        RECOVERY_PLAN,
        SAVED_AUDIT,
        *recovery_sources(root),
    ])


def required_tests():
    from lll.studies.task_resume import REQUIRED_TESTS as recovery_tests
    return original_tests() + [
        'test_dispatch_selects_exact_sixteen_globe_cases_and_limits',
        'test_dispatch_budget_is_finite_and_source_bound',
        'test_dispatch_loader_receives_model_before_fit',
    ] + list(recovery_tests)


def _extra_inputs(root):
    from lll.studies.artifacts import encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.task_resume import qualification_sources as recovery_sources
    from lll.studies.task_resume import REQUIRED_TESTS as recovery_tests
    from lll.ilvis0_control_shards import runtime_environment

    recovery_request, recovery_report = checked(
        root, RECOVERY_REQUEST, sources=recovery_sources(root),
        environment=runtime_environment(), required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))

    audit_raw = (Path(root)/SAVED_AUDIT).read_bytes()
    if hashlib.sha256(audit_raw).hexdigest() != SAVED_AUDIT_SHA256:
        raise ValueError('unchanged saved 24-case dispatch audit required')
    audit = json.loads(audit_raw)
    if (audit['matching_saved_numerical_dispositions'] != 24 or
            audit['counts'] != {'selective': {'cases': 16, 'numerical_passes': 16},
                                'wide': {'cases': 8, 'numerical_passes': 7}} or
            len(audit['selected']) != 24):
        raise ValueError('complete saved dispatch audit required')
    parent = ClosedStudy(root, GENERATED_PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.completion['manifest_sha256'] != GENERATED_MANIFEST or
                parent.completion['summary_sha256'] != GENERATED_SUMMARY or
                len(parent.rows) != 6 or
                not all(parent.envelope(case)['result']['passed']
                        for case in parent.rows)):
            raise ValueError('complete generated model-declared parent required')
    finally:
        parent.close()
    return {'dispatch-recovery-request': recovery_request,
            'dispatch-recovery-report': recovery_report,
            'dispatch-parent-proof': encoded(dict(
        generated_parent=GENERATED_PARENT,
        generated_manifest_sha256=GENERATED_MANIFEST,
        generated_summary_sha256=GENERATED_SUMMARY,
        saved_audit_sha256=SAVED_AUDIT_SHA256,
        generated_pairs_passed=6, flat_saved_cases=8,
        globe_saved_cases=16,
        recovery_request_sha256=hashlib.sha256(recovery_request).hexdigest(),
        recovery_report_sha256=hashlib.sha256(recovery_report).hexdigest()))}


def prepare(root, *, qualification, maximum_wall_s=108000):
    if qualification is None:
        raise ValueError('source-bound qualification required before preparation')
    return prepare_variant(
        root, qualification=qualification, maximum_wall_s=maximum_wall_s,
        identity=IDENTITY, recipe_fn=recipe, task_fn=tasks,
        sources_fn=sources, required_fn=required_tests,
        expected_tasks=16, scope=SCOPE,
        adapter='analysis/lll/airquantumgrav_observed_dispatch.py',
        extra_inputs=_extra_inputs)


def evaluate(task, context):
    from lll.ilvis0_tangent_dispatch import load_for_model

    proof = json.loads(context.input_path('dispatch-parent-proof').read_bytes())
    if {key: proof.get(key) for key in (
            'generated_parent', 'generated_manifest_sha256',
            'generated_summary_sha256', 'saved_audit_sha256',
            'generated_pairs_passed', 'flat_saved_cases',
            'globe_saved_cases')} != dict(
                generated_parent=GENERATED_PARENT,
                generated_manifest_sha256=GENERATED_MANIFEST,
                generated_summary_sha256=GENERATED_SUMMARY,
                saved_audit_sha256=SAVED_AUDIT_SHA256,
                generated_pairs_passed=6, flat_saved_cases=8,
                globe_saved_cases=16):
        raise ValueError('unchanged generated and saved-audit proof required')
    request = context.input_path('dispatch-recovery-request').read_bytes()
    report = context.input_path('dispatch-recovery-report').read_bytes()
    if (hashlib.sha256(request).hexdigest() !=
            proof.get('recovery_request_sha256') or
            hashlib.sha256(report).hexdigest() !=
            proof.get('recovery_report_sha256')):
        raise ValueError('unchanged qualified reboot recovery required')
    model = task['payload']['model']
    if model not in ('sphere_rotating', 'sphere_still'):
        raise ValueError('observed candidate work restricted to globe cases')

    def load_declared(directory, *, expected_source_sha256,
                      expected_loader_sha256, gravity_anchor_height_m):
        return load_for_model(
            model, directory,
            expected_source_sha256=expected_source_sha256,
            expected_wide_loader_sha256=expected_loader_sha256,
            expected_selective_loader_sha256=context.manifest['sources'][
                'analysis/lll/ilvis0_hybrid_tangent.py'],
            gravity_anchor_height_m=gravity_anchor_height_m)

    return evaluate_variant(task, context, load_hybrid=load_declared,
                            recipe_fn=recipe, task_fn=tasks, scope=SCOPE)
