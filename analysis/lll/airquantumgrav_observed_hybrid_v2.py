# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three-pair development gate for the revised selective ESA tangent."""

from lll.airquantumgrav_observed_hybrid import (
    prepare_variant, evaluate_variant, qualification_sources as original_sources,
    required_tests as original_tests, recipe as original_recipe,
    tasks as original_tasks)


IDENTITY = 'esa-observed-hybrid-v2-three-pair-development'
SCOPE = ('three failed ESA development pairs; revised attitude precision; '
         'saved measurements only; no originals, protected reads or decision')
FAILED = frozenset({
    'flat_still-0-reported-short-v1-1',
    'flat_still-0-reported-persistent-v1-0',
    'flat_still-1-reported-short-v1-0',
})
SAVED_POINT_PARENT = 'data/esa-same-point-tangent-v2-20261111-r1'
SAVED_POINT_MANIFEST = '55f08ddc8a6ee283d594635c9888f7c76f74231f493ec38ff32510a4f4120da4'
SAVED_POINT_SUMMARY = '92a3083969235076fc86113c1fe48ca3642ba032f840f1e1d6ec805f613cbdb4'


def recipe(*, maximum_wall_s):
    if not 0 < maximum_wall_s <= 14400:
        raise ValueError('finite four-hour paired development allowance required')
    return dict(original_recipe(maximum_wall_s=maximum_wall_s),
                version='esa-observed-hybrid-v2-three-pair-v1',
                workers=3, threads=1, maximum_wall_s=float(maximum_wall_s))


def tasks(layout):
    selected = [case for case in original_tasks(layout)
                if case['identity'] in FAILED]
    if len(selected) != 3 or {case['identity'] for case in selected} != FAILED:
        raise ValueError('exact three failed historical case identities required')
    if (sum(case['limits']['native_calls'] for case in selected) != 1206 or
            sum(case['limits']['packet_visits'] for case in selected) !=
            232864521600):
        raise ValueError('exact unchanged finite paired charge grid required')
    return selected


def sources(root):
    from lll.studies.dependencies import source_closure
    return source_closure(root, [
        *original_sources(root),
        'analysis/lll/airquantumgrav_observed_hybrid_v2.py',
        'analysis/lll/airquantumgrav_observed_hybrid_v2_report.py',
        'analysis/lll/ilvis0_hybrid_tangent_v2.py',
        'analysis/tests/test_airquantumgrav_observed_hybrid_v2.py',
        'analysis/tests/test_airquantumgrav_observed_hybrid_v2_report.py',
        'analysis/tests/test_task_resume.py',
        'analysis/tests/test_task_continuation.py',
        'docs/mixed-tangent-hybrid/V2_PAIRED_PLAN.md',
        'docs/mixed-tangent-hybrid/V2_PAIRED_RECOVERY.md'])


def required_tests():
    return original_tests() + [
        'test_v2_three_pair_grid_keeps_original_limits',
        'test_v2_recipe_limits_workers_and_wall',
        'test_v2_requires_source_bound_qualification',
        'test_v2_loader_and_sealed_source_are_explicit',
        'test_v2_evaluator_injects_only_revised_loader',
        'test_v2_preparation_binds_saved_point_and_recovery_receipts',
        'test_v2_generated_pair_fits_share_inputs_and_forecast',
        'test_reboot_resume_skips_sealed_and_preserves_charges',
        'test_source_input_environment_mutation_blocks',
        'test_v2_report_keeps_unreturned_and_technical_failures',
        'test_v2_report_rejects_missing_pair_evidence_and_protected_reads',
        'test_v2_report_preserves_matched_numerical_failure',
        'test_v2_report_replays_passing_pair_before_publication',
    ]


def saved_point_proof(root):
    from lll.studies.artifacts import encoded
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.task_resume import (
        qualification_sources as recovery_sources, runner,
        REQUIRED_TESTS as recovery_tests)
    recovery_request, recovery_report = checked(
        root, 'docs/mixed-tangent-hybrid/v2-paired-recovery-request.json',
        sources=recovery_sources(root),
        environment=runner.runtime_environment(),
        required_tests=recovery_tests, minimum_tests=5)
    parent = ClosedStudy(root, SAVED_POINT_PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.completion['manifest_sha256'] != SAVED_POINT_MANIFEST or
                parent.completion['summary_sha256'] != SAVED_POINT_SUMMARY or
                len(parent.tasks) != 3 or len(parent.rows) != 3 or
                set(parent.rows) != FAILED or
                not all(parent.envelope(identity)['result'].get('passed')
                        for identity in parent.rows)):
            raise ValueError('exact passing revised saved-point parent required')
        return {'v2-saved-point-proof': encoded(dict(
                    parent=SAVED_POINT_PARENT,
                    manifest_sha256=SAVED_POINT_MANIFEST,
                    summary_sha256=SAVED_POINT_SUMMARY, passing_pairs=3)),
                'v2-recovery-request': recovery_request,
                'v2-recovery-report': recovery_report}
    finally:
        parent.close()


def prepare(root, *, qualification, maximum_wall_s=14400):
    return prepare_variant(
        root, qualification=qualification, maximum_wall_s=maximum_wall_s,
        identity=IDENTITY, recipe_fn=recipe, task_fn=tasks,
        sources_fn=sources, required_fn=required_tests, expected_tasks=3,
        scope=SCOPE,
        adapter='analysis/lll/airquantumgrav_observed_hybrid_v2.py',
        extra_inputs=saved_point_proof)


def evaluate(task, context):
    import json
    from lll.ilvis0_hybrid_tangent_v2 import load as load_revised
    proof = json.loads(context.input_path('v2-saved-point-proof').read_bytes())
    if proof != dict(parent=SAVED_POINT_PARENT,
                     manifest_sha256=SAVED_POINT_MANIFEST,
                     summary_sha256=SAVED_POINT_SUMMARY, passing_pairs=3):
        raise ValueError('passing revised saved-point source proof required')
    if ('analysis/lll/ilvis0_hybrid_tangent_v2.py' not in
            context.manifest['sources']):
        raise ValueError('revised tangent source must be frozen')
    return evaluate_variant(
        task, context, load_hybrid=load_revised,
        recipe_fn=recipe, task_fn=tasks, scope=SCOPE,
        expected_precision_revision='attitude-x-y-wide')
