# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite whole-fit CPU timing for the qualified generated long-record pairs."""

import statistics
from pathlib import Path

from lll import ilvis0_hybrid_long_fit_study as long_fit
from lll import ilvis0_paired_fit_runtime as runtime
from lll.ilvis0_fit_timing import timed_pair


SCOPE = ('generated twenty-minute paired whole-fit timing; '
         'no observed or protected inputs')
PARENT = ('data/hybrid-long-paired-training-20261110-v2',
          'f4d8609c51a918493d1b9b0a83c719201b49426fe2d98938451bfbfa7f4ee956',
          '2df075a347a694e908608306bd05ed384602fd53b9c2bc3739d4af74521689f8')


def recipe():
    return dict(long_fit.recipe(), version='hybrid-timed-paired-training-v1')


def tasks(r=None):
    return long_fit.tasks(recipe() if r is None else r)


def parent_proof():
    return {'long_paired_fit': dict(manifest_sha256=PARENT[1],
                                    summary_sha256=PARENT[2], six_cases_passed=True)}


def qualification_sources(root):
    from lll.studies.dependencies import source_closure
    return sorted(set(long_fit.qualification_sources(root)) | set(source_closure(root, [
        'analysis/lll/ilvis0_fit_timing.py',
        'analysis/lll/ilvis0_hybrid_timed_fit_study.py',
        'analysis/tests/test_ilvis0_fit_timing.py',
        'analysis/tests/test_ilvis0_hybrid_timed_fit_study.py',
        'docs/mixed-tangent-hybrid/TIMED_FIT_PLAN.md'])))


def required_tests():
    return long_fit.required_tests() + (
        'test_timer_excludes_kernel_compilation_and_forecast_from_fit_cpu',
        'test_timer_rejects_incomplete_or_misordered_fit_markers[missing_fit]',
        'test_timer_rejects_incomplete_or_misordered_fit_markers[duplicate_fit]',
        'test_timer_rejects_incomplete_or_misordered_fit_markers[fit_before_kernel]',
        'test_timer_rejects_nonpositive_elapsed_time',
        'test_timed_pair_preserves_matched_result_and_records_two_variants',
        'test_timed_recipe_keeps_six_long_cases_and_finite_allowances',
        'test_timed_adapter_loads_from_a_frozen_file_without_package_context',
        'test_timed_preparation_requires_qualified_sources_before_writing',
        'test_timed_worker_rejects_changed_recipe_before_construction',
        'test_timed_report_rejects_unclosed_study',
        'test_operational_speed_gate_uses_fit_cpu_not_total_cpu',
    )


def prepare(root, *, qualification, identity='hybrid-timed-paired-training-20261110'):
    if qualification is None:
        raise ValueError('source-bound software qualification required before preparation')
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    parent = ClosedStudy(root, PARENT[0])
    try:
        if (len(parent.rows) != 6
                or parent.completion['manifest_sha256'] != PARENT[1]
                or parent.completion['summary_sha256'] != PARENT[2]
                or not all(parent.envelope(name)['result']['passed']
                           for name in parent.tasks)):
            raise ValueError('complete qualified long paired-fit parent required')
    finally:
        parent.close()
    return runtime.prepare(root, qualification=qualification, identity=identity,
                           recipe=recipe, scope=SCOPE,
                           sources=qualification_sources(root),
                           required_tests=required_tests(), parent_proof=parent_proof(),
                           adapter='analysis/lll/ilvis0_hybrid_timed_fit_study.py',
                           tasks=tasks)


def evaluate(task, context):
    return runtime.evaluate(task, context, recipe=recipe, scope=SCOPE,
                            parent_proof=parent_proof(), tasks=tasks,
                            construction_limits=long_fit.shared.construction_limits,
                            pair=timed_pair)


def speed_summary(rows):
    """Apply the predeclared operational CPU criterion to six saved timings."""
    if len(rows) != 6:
        raise ValueError('six complete timed cases required')
    ratios = []
    for row in rows:
        if set(row) != {'wide', 'hybrid'}:
            raise ValueError('matched wide and selective timings required')
        for name in ('wide', 'hybrid'):
            values = row[name]
            if (set(values) != {'complete_cpu_ns', 'complete_wall_ns',
                                'fit_cpu_ns', 'fit_wall_ns'}
                    or any(type(value) is not int or value <= 0
                           for value in values.values())
                    or values['fit_cpu_ns'] > values['complete_cpu_ns']
                    or values['fit_wall_ns'] > values['complete_wall_ns']):
                raise ValueError('positive ordered whole-fit timing required')
        ratios.append(row['wide']['fit_cpu_ns'] / row['hybrid']['fit_cpu_ns'])
    median = statistics.median(ratios)
    minimum = min(ratios)
    return dict(fit_cpu_ratios=ratios,
                median_fit_cpu_ratio=median, minimum_fit_cpu_ratio=minimum,
                worthwhile_substitution=median > 1.25 and minimum >= 1.0)


def inspect(root, prefix='data/hybrid-timed-paired-training-20261110'):
    from lll.studies.artifacts import encoded
    from lll.studies.closed import ClosedStudy

    root = Path(root).resolve()
    report = runtime.inspect(root, prefix, recipe=recipe, scope=SCOPE,
                             parent_proof=parent_proof(), tasks=tasks,
                             construction_limits=long_fit.shared.construction_limits)
    study = ClosedStudy(root, prefix)
    try:
        timings = []
        for task in tasks():
            identity = task['identity']
            result = study.envelope(identity)['result']
            saved = study.artifact(identity, 'whole-fit-timing.json')
            if encoded(result['timing']) != encoded(saved):
                raise ValueError('saved whole-fit timing differs from result envelope')
            timings.append(saved)
        report['timing'] = dict(cases=timings, **speed_summary(timings))
        return report
    finally:
        study.close()
