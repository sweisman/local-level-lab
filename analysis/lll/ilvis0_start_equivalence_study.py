# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite generated two-start check for model-declared tangent arithmetic."""

import math
from pathlib import Path

import numpy as np


ID = 'model-declared-start-equivalence-v1'
SCOPE = 'generated two-start model-declared tangent comparison; no observed or protected inputs'
PARENT = ('data/model-declared-paired-fit-20261115-v2',
          '8a8f0e687d8556f2d6e9e699d76acfee3abd0e34d116e74f8f3d1471656a8458',
          '227070f95c16d67bd545b91b1824c0648c1fcd2a5e7a7446e31b14c904a2ef2f')
PLAN = 'docs/mixed-tangent-hybrid/START_EQUIVALENCE_STUDY_PLAN.md'


def recipe():
    from .ilvis0_dispatched_fit_study import recipe as base
    return dict(base(), version='model-declared-start-equivalence-v1',
                starts=2, maximum_wall_s=3600., relative_cost_tolerance=1e-8)


def tasks(settings=None):
    from .ilvis0_dispatched_fit_study import tasks as base
    if settings is not None and settings != recipe():
        raise ValueError('unchanged two-start recipe required')
    result = []
    for row in base():
        for start in (0, 1):
            result.append(dict(row, identity=f"{row['identity']}-{start}",
                               payload=dict(row['payload'], start=start)))
    return result


def world_coordinates(coordinates, model):
    """Convert one model's forecast chart to its Euclidean metre space."""
    from .airquantumgrav_truth import A, E2, DISC_RADIUS, MODELS

    p = np.asarray(coordinates, float)
    if (model not in MODELS or p.ndim != 2 or p.shape[1] != 3 or not len(p)
            or not np.all(np.isfinite(p)) or np.any(abs(p[:, 0]) >= math.pi/2)):
        raise ValueError('finite nonpolar three-coordinate forecast required')
    phi, longitude, h = p.T
    if model.startswith('sphere'):
        rn = A/np.sqrt(1-E2*np.sin(phi)**2)
        radius = (rn+h)*np.cos(phi)
        height = (rn*(1-E2)+h)*np.sin(phi)
    else:
        radius = DISC_RADIUS*(math.pi/2-phi)
        height = h
    return np.column_stack((radius*np.cos(longitude),
                            radius*np.sin(longitude), height)).tolist()


def assess_group(group, *, model, settings):
    """Compare complete two-start output without reading later receiver truth."""
    from .ilvis0_start_equivalence import compare_start_sets
    from .studies.artifacts import digest, encoded

    if (settings != recipe() or set(group) != {'wide', 'hybrid'} or
            any(set(group[name]) != {0, 1} for name in ('wide', 'hybrid'))):
        raise ValueError('complete unchanged two-start group required')
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
            binding = digest(encoded(dict(input=row['input_binding'], times_s=times)))
            prepared[variant].append(dict(start=start,
                training_cost=row['training_cost'], forecast=forecast,
                binding=binding, passed=row['passed']))
    return compare_start_sets(prepared['wide'], prepared['hybrid'],
        relative_cost_tolerance=settings['relative_cost_tolerance'],
        forecast_tolerance_m=settings['paired_prediction_tolerance_m'])


def pair(spec, settings, **kwargs):
    from .ilvis0_hybrid_fit_study import pair as existing
    if settings != recipe():
        raise ValueError('unchanged two-start recipe required')
    return existing(spec, settings,
                    allowed_specs=[row['payload'] for row in tasks(settings)],
                    **kwargs)


def parent_proof():
    return dict(generated_dispatch=dict(manifest_sha256=PARENT[1],
                                        summary_sha256=PARENT[2],
                                        six_cases_passed=True))


def qualification_sources(root):
    from .ilvis0_dispatched_fit_study import qualification_sources as earlier
    from .studies.dependencies import source_closure

    return sorted(set(earlier(root)) | set(source_closure(Path(root).resolve(), [
        'analysis/lll/ilvis0_start_equivalence.py',
        'analysis/lll/ilvis0_start_equivalence_study.py',
        'analysis/tests/test_ilvis0_start_equivalence.py',
        'analysis/tests/test_ilvis0_start_equivalence_study.py',
        PLAN])))


def required_tests():
    from .ilvis0_dispatched_fit_study import required_tests as earlier

    return earlier() + (
        'test_pair_accepts_a_second_start_only_when_explicitly_declared',
        'test_switched_near_tied_starts_are_equivalent_only_when_all_forecasts_agree',
        'test_near_tied_start_with_different_forecast_blocks_equivalence',
        'test_material_cost_change_or_unqualified_fit_blocks_equivalence',
        'test_zero_cost_is_not_near_a_positive_cost_on_an_absolute_floor',
        'test_changed_input_or_time_grid_is_rejected',
        'test_invalid_limits_and_nonfinite_values_are_rejected',
        'test_two_start_study_covers_all_models_and_profiles_with_finite_limits',
        'test_forecast_conversion_uses_each_candidate_metric_in_metres',
        'test_group_checks_cross_start_paths_without_later_receiver_positions',
        'test_preparation_requires_source_bound_qualification',
        'test_second_start_pair_uses_existing_matched_fit_runner',
        'test_source_binding_includes_new_method_and_recovery_checks',
        'test_old_one_start_study_cannot_be_reinterpreted_as_two_start_release')


def prepare(root, *, qualification):
    if qualification is None:
        raise ValueError('source-bound qualification required before preparation')
    from . import ilvis0_paired_fit_runtime as runtime
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    parent = ClosedStudy(root, PARENT[0])
    try:
        if (len(parent.rows) != 6 or
                parent.completion['manifest_sha256'] != PARENT[1] or
                parent.completion['summary_sha256'] != PARENT[2] or
                not all(parent.envelope(name)['result']['passed']
                        for name in parent.tasks)):
            raise ValueError('complete passing generated dispatch parent required')
    finally:
        parent.close()
    return runtime.prepare(root, qualification=qualification,
                           identity=ID, recipe=recipe, scope=SCOPE,
                           sources=qualification_sources(root),
                           required_tests=required_tests(),
                           parent_proof=parent_proof(),
                           adapter='analysis/lll/ilvis0_start_equivalence_study.py',
                           tasks=tasks)


def evaluate(task, context):
    from . import ilvis0_paired_fit_runtime as runtime
    from .ilvis0_hybrid_fit_study import construction_limits
    from .ilvis0_tangent_dispatch import load_for_model

    return runtime.evaluate(task, context, recipe=recipe, scope=SCOPE,
                            parent_proof=parent_proof(), tasks=tasks,
                            construction_limits=construction_limits, pair=pair,
                            candidate_loader=load_for_model)


def inspect(root, prefix='data/'+ID):
    """Replay every pair, then compare both primary-start choices by forecast."""
    from . import ilvis0_paired_fit_runtime as runtime
    from .ilvis0_hybrid_fit_study import construction_limits
    from .ilvis0_tangent_dispatch import method_for_model, VERSION
    from .studies.closed import ClosedStudy

    report = runtime.inspect(root, prefix, recipe=recipe, scope=SCOPE,
                             parent_proof=parent_proof(), tasks=tasks,
                             construction_limits=construction_limits)
    study = ClosedStudy(root, prefix)
    try:
        groups = []
        choices = []
        for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
            for profile in (False, True):
                group = {'wide': {}, 'hybrid': {}}
                for start in (0, 1):
                    identity = f'{model}-{int(profile)}-{start}'
                    if identity not in study.rows:
                        continue
                    result = study.envelope(identity)['result']
                    wide = study.artifact(identity, 'wide-compilation.json')['tangent']
                    candidate = study.artifact(identity, 'hybrid-compilation.json')['tangent']
                    method = method_for_model(model)
                    if (wide.get('dispatch_method') is not None or
                            candidate.get('dispatch_version') != VERSION or
                            candidate.get('dispatch_model') != model or
                            candidate.get('dispatch_method') != method):
                        raise ValueError('model-declared tangent choice differs')
                    choices.append(dict(identity=identity, model=model, method=method))
                    for variant, key in (('wide', 'reference'), ('hybrid', 'candidate')):
                        forecast = study.artifact(identity, variant+'-forecast.json')
                        group[variant][start] = dict(
                            training_cost=result[key]['training_cost'],
                            passed=result[key]['passed'],
                            input_binding=study.artifact(identity,
                                variant+'-input-binding.json'),
                            times_s=forecast['times_s'],
                            forecast=forecast['coordinates'])
                if all(len(group[name]) == 2 for name in group):
                    assessment = assess_group(group, model=model, settings=recipe())
                else:
                    assessment = dict(equivalent=False, reason='missing sealed start')
                groups.append(dict(model=model, profile=profile, **assessment))
        report.update(groups=groups, dispatch_choices=choices,
                      qualified=bool(report['qualified'] and len(choices) == 12 and
                                     all(row['equivalent'] for row in groups)))
        return report
    finally:
        study.close()
