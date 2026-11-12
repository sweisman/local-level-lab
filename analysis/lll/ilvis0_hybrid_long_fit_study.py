# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite twenty-minute generated fit/forecast arithmetic comparison."""
from pathlib import Path

from lll import ilvis0_hybrid_fit_study as shared
from lll import ilvis0_paired_fit_runtime as runtime


SCOPE = 'generated twenty-minute paired wide/selective training and forecast; no observed or protected inputs'
LONG_KERNEL = ('data/hybrid-tangent-long-controls-20261110',
               '98d11063bd193578761d0fa4c79f56e4815bf03fbca9d3aa979f8c49cd789c77',
               '403a495e75010708c80921ebe42639f3687a18d38abf4ac17d06c9f80b422a21')
SHORT_FIT = ('data/hybrid-paired-training-20261110',
             '98809b0d3c25647b59741cc36141cd0eb1c419174268decad11c2644de014848',
             '5d8b2f41448591120db2152ea84d80282817ca0a78080e96cd336b2a62156af8')


def recipe():
    return dict(shared.recipe(), version='hybrid-long-paired-training-v2',
                duration_s=1200., queries=1199, maximum_wall_s=21600.)


def tasks(r=None):
    return shared.tasks(recipe() if r is None else r)


def parent_proof():
    return {
        'long_kernel': dict(manifest_sha256=LONG_KERNEL[1], summary_sha256=LONG_KERNEL[2],
                            six_cases_passed=True),
        'short_fit': dict(manifest_sha256=SHORT_FIT[1], summary_sha256=SHORT_FIT[2],
                          six_cases_passed=True),
    }


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return sorted(set(shared.qualification_sources(root)) | set(source_closure(root, [
        'analysis/lll/ilvis0_hybrid_long_fit_study.py',
        'analysis/tests/test_ilvis0_hybrid_long_fit_study.py',
        'docs/mixed-tangent-hybrid/LONG_FIT_PLAN.md'])))


def required_tests():
    return shared.required_tests() + (
        'test_long_recipe_keeps_six_matched_cases_and_finite_allowances',
        'test_long_worker_adapter_loads_from_frozen_file_without_package_context',
        'test_long_preparation_requires_source_bound_tests_before_writing',
        'test_long_worker_rejects_short_recipe_before_construction',
        'test_long_worker_rejects_changed_parent_before_construction',
        'test_long_report_rejects_unclosed_study',
    )


def prepare(root, *, qualification, identity='hybrid-long-paired-training-20261110-v2'):
    if qualification is None:
        raise ValueError('source-bound software qualification required before preparation')
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    for prefix, manifest_sha, summary_sha in (LONG_KERNEL, SHORT_FIT):
        parent = ClosedStudy(root, prefix)
        try:
            if (len(parent.rows) != 6
                    or parent.completion['manifest_sha256'] != manifest_sha
                    or parent.completion['summary_sha256'] != summary_sha
                    or not all(parent.envelope(name)['result']['passed']
                               for name in parent.tasks)):
                raise ValueError('complete passing matched parent required: ' + prefix)
        finally:
            parent.close()
    return runtime.prepare(root, qualification=qualification, identity=identity,
                           recipe=recipe, scope=SCOPE,
                           sources=qualification_sources(root),
                           required_tests=required_tests(), parent_proof=parent_proof(),
                           adapter='analysis/lll/ilvis0_hybrid_long_fit_study.py',
                           tasks=tasks)


def evaluate(task, context):
    return runtime.evaluate(task, context, recipe=recipe, scope=SCOPE,
                            parent_proof=parent_proof(), tasks=tasks,
                            construction_limits=shared.construction_limits,
                            pair=shared.pair)


def inspect(root, prefix='data/hybrid-long-paired-training-20261110-v2'):
    return runtime.inspect(root, prefix, recipe=recipe, scope=SCOPE,
                           parent_proof=parent_proof(), tasks=tasks,
                           construction_limits=shared.construction_limits)
