# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh 180-second generated qualification of model-declared tangent starts."""

import math
from pathlib import Path

ID = 'model-declared-start-equivalence-v2'
SCOPE = ('fresh 180-second generated two-start model-declared tangent comparison; '
         'no observed or protected inputs')
OLD = ('data/model-declared-start-equivalence-v1',
       '13662b28a4735862a8a09234229f49a568938ca6b4c199936babf40940539693',
       '583e0fe23e4e4797c1ec012c3841fe9062e47e789290b010611c2e7ae202f592')
PLAN = 'docs/mixed-tangent-hybrid/START_EQUIVALENCE_V2_STUDY_PLAN.md'


def recipe():
    from .ilvis0_start_equivalence_study import recipe as old
    return dict(old(), version='model-declared-start-equivalence-v2',
                duration_s=180., queries=179, maximum_wall_s=7200.,
                absolute_cost_tolerance=1e-8)


def tasks(settings=None):
    from .ilvis0_hybrid_fit_study import tasks as base
    r = recipe()
    if settings is not None and settings != r:
        raise ValueError('unchanged fresh two-start recipe required')
    result = []
    for row in base(r):
        for start in (0, 1):
            result.append(dict(row, identity=f"{row['identity']}-{start}",
                payload=dict(row['payload'], start=start)))
    return result


def assess_group(group, *, model, settings):
    """Apply the revised rule to complete sealed fits, never later truth."""
    from .ilvis0_start_equivalence_study import world_coordinates
    from .ilvis0_start_equivalence_v2 import compare_start_sets_v2
    from .studies.artifacts import digest, encoded

    if (settings != recipe() or set(group) != {'wide', 'hybrid'} or
            any(set(group[name]) != {0, 1} for name in ('wide', 'hybrid'))):
        raise ValueError('complete unchanged fresh two-start group required')
    prepared = {}
    for variant in ('wide', 'hybrid'):
        prepared[variant] = []
        for start in (0, 1):
            row = group[variant][start]
            times = row['times_s']
            if (not isinstance(times, list) or not times or any(
                    type(t) not in (int, float) or not math.isfinite(t)
                    for t in times) or any(b <= a for a, b in zip(times, times[1:]))):
                raise ValueError('ordered finite forecast time grid required')
            forecast = world_coordinates(row['forecast'], model)
            if len(forecast) != len(times):
                raise ValueError('forecast grid and coordinates differ')
            prepared[variant].append(dict(start=start,
                training_cost=row['training_cost'], forecast=forecast,
                binding=digest(encoded(dict(input=row['input_binding'],
                                            times_s=times))),
                passed=row['passed']))
    return compare_start_sets_v2(prepared['wide'], prepared['hybrid'],
        relative_cost_tolerance=settings['relative_cost_tolerance'],
        absolute_cost_tolerance=settings['absolute_cost_tolerance'],
        forecast_tolerance_m=settings['paired_prediction_tolerance_m'])


def pair(spec, settings, **kwargs):
    from .ilvis0_hybrid_fit_study import pair as base
    if settings != recipe():
        raise ValueError('unchanged fresh two-start recipe required')
    return base(spec, settings,
        allowed_specs=[row['payload'] for row in tasks(settings)], **kwargs)


def parent_proof():
    from .ilvis0_start_equivalence_study import parent_proof as old
    return dict(old(), previous_failed_gate=dict(
        manifest_sha256=OLD[1], summary_sha256=OLD[2], qualified=False))


def qualification_sources(root):
    from .ilvis0_start_equivalence_study import qualification_sources as old
    from .studies.dependencies import source_closure
    return sorted(set(old(root)) | set(source_closure(Path(root).resolve(), [
        'analysis/lll/ilvis0_start_equivalence_v2.py',
        'analysis/lll/ilvis0_start_equivalence_v2_study.py',
        'analysis/tests/test_ilvis0_start_equivalence_v2.py',
        'analysis/tests/test_ilvis0_start_equivalence_v2_study.py',
        PLAN])))


def required_tests():
    from .ilvis0_start_equivalence_study import required_tests as old
    return old() + (
        'test_v2_absolute_floor_handles_near_zero_cost_without_hiding_material_gap',
        'test_v2_checks_within_method_spread_even_if_cross_method_passes',
        'test_v2_rejects_invalid_absolute_tolerance',
        'test_v2_study_freezes_new_geometry_and_finite_limits',
        'test_v2_study_requires_complete_group_and_early_only_binding',
        'test_v2_study_preserves_failed_parent_and_qualification',
        'test_v2_study_uses_shared_paired_calculation')


def verify_parent(root):
    from .ilvis0_start_equivalence_study import inspect as old_inspect
    from .studies.closed import ClosedStudy
    old = ClosedStudy(root, OLD[0])
    try:
        if (old.completion != dict(state='complete',
                manifest_sha256=OLD[1], summary_sha256=OLD[2]) or
                old.summary['total'] != old.summary['completed'] or
                old.summary['total'] != 12):
            raise ValueError('exact completed failed-rule parent required')
    finally:
        old.close()
    report = old_inspect(root, OLD[0])
    if not report['verified'] or report['qualified']:
        raise ValueError('original failed qualification must remain unchanged')
    return True


def prepare(root, *, qualification=None):
    if qualification is None:
        raise ValueError('fresh source-bound qualification required')
    from . import ilvis0_paired_fit_runtime as runtime
    verify_parent(root)
    return runtime.prepare(Path(root).resolve(), qualification=qualification,
        identity=ID, recipe=recipe, scope=SCOPE,
        sources=qualification_sources(root), required_tests=required_tests(),
        parent_proof=parent_proof(),
        adapter='analysis/lll/ilvis0_start_equivalence_v2_study.py', tasks=tasks)


def evaluate(task, context):
    from . import ilvis0_paired_fit_runtime as runtime
    from .ilvis0_hybrid_fit_study import construction_limits
    from .ilvis0_tangent_dispatch import load_for_model
    return runtime.evaluate(task, context, recipe=recipe, scope=SCOPE,
        parent_proof=parent_proof(), tasks=tasks,
        construction_limits=construction_limits, pair=pair,
        candidate_loader=load_for_model)


def inspect(root, prefix='data/'+ID):
    from . import ilvis0_paired_fit_runtime as runtime
    from .ilvis0_hybrid_fit_study import construction_limits
    from .studies.closed import ClosedStudy

    report = runtime.inspect(root, prefix, recipe=recipe, scope=SCOPE,
        parent_proof=parent_proof(), tasks=tasks,
        construction_limits=construction_limits)
    study = ClosedStudy(root, prefix)
    try:
        groups = []
        for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
            for profile in (False, True):
                group = {'wide': {}, 'hybrid': {}}
                for start in (0, 1):
                    identity = f'{model}-{int(profile)}-{start}'
                    if identity not in study.rows:
                        continue
                    result = study.envelope(identity)['result']
                    for variant, key in (('wide', 'reference'),
                                         ('hybrid', 'candidate')):
                        forecast = study.artifact(identity, variant+'-forecast.json')
                        group[variant][start] = dict(
                            training_cost=result[key]['training_cost'],
                            passed=result[key]['passed'],
                            input_binding=study.artifact(identity,
                                variant+'-input-binding.json'),
                            times_s=forecast['times_s'],
                            forecast=forecast['coordinates'])
                assessment = (assess_group(group, model=model, settings=recipe())
                    if all(len(group[name]) == 2 for name in group)
                    else dict(equivalent=False, reason='missing sealed start'))
                groups.append(dict(model=model, profile=profile, **assessment))
        report.update(groups=groups,
            qualified=bool(report['qualified'] and len(groups) == 6 and
                           all(row['equivalent'] for row in groups)))
        return report
    finally:
        study.close()
