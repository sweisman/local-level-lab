# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-result audit of forecast spread among near-minimum optimizer starts.

This is a diagnostic added after the first two-start study closed. It never
changes that study's frozen equivalence decision.
"""

import math
import hashlib
import json
from pathlib import Path

from .ilvis0_start_equivalence import compare_start_sets
from .ilvis0_start_equivalence_v2 import compare_start_sets_v2


def audit_start_spread(reference, candidate, *, relative_cost_tolerance,
                       forecast_tolerance_m, absolute_cost_tolerance=None):
    """Add within-method forecast spread to the frozen cross-method report."""
    frozen = compare_start_sets(
        reference, candidate,
        relative_cost_tolerance=relative_cost_tolerance,
        forecast_tolerance_m=forecast_tolerance_m)
    ref = {row['start']: row for row in reference}
    cand = {row['start']: row for row in candidate}

    def spread(rows, ties):
        return max((math.dist(a, b)
                    for i in ties for j in ties
                    for a, b in zip(rows[i]['forecast'], rows[j]['forecast'],
                                    strict=True)), default=0.0)

    within_reference = spread(ref, frozen['reference_near_ties'])
    within_candidate = spread(cand, frozen['candidate_near_ties'])
    cost_differences = [
        (abs(ref[start]['training_cost']-cand[start]['training_cost']),
         abs(ref[start]['training_cost']-cand[start]['training_cost']) /
         max(ref[start]['training_cost'], cand[start]['training_cost'])
         if max(ref[start]['training_cost'], cand[start]['training_cost']) else 0.0)
        for start in ref]
    result = dict(
        frozen_rule=frozen,
        reference_within_maximum_m=within_reference,
        candidate_within_maximum_m=within_candidate,
        same_start_cost_absolute_maximum=max(item[0] for item in cost_differences),
        same_start_cost_relative_maximum=max(item[1] for item in cost_differences),
        forecast_spread_stable=bool(max(
            frozen['cross_start_maximum_m'], within_reference, within_candidate)
            <= forecast_tolerance_m))
    if absolute_cost_tolerance is not None:
        result['revised_rule_development_diagnostic'] = compare_start_sets_v2(
            reference, candidate,
            relative_cost_tolerance=relative_cost_tolerance,
            absolute_cost_tolerance=absolute_cost_tolerance,
            forecast_tolerance_m=forecast_tolerance_m)
    return result


def audit_sealed_study(root, prefix, *, absolute_cost_tolerance=None):
    """Verify a sealed two-start study, then audit its saved forecast artifacts."""
    from .ilvis0_start_equivalence_study import inspect, recipe, world_coordinates
    from .studies.artifacts import digest, encoded
    from .studies.closed import ClosedStudy

    sealed = inspect(root, prefix)
    if not sealed['verified'] or sealed['complete'] != sealed['total']:
        raise ValueError('complete verified study required')
    settings = recipe()
    study = ClosedStudy(root, prefix)
    try:
        groups = []
        for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
            for profile in (False, True):
                variants = {'wide': [], 'hybrid': []}
                for start in (0, 1):
                    identity = f'{model}-{int(profile)}-{start}'
                    if identity not in study.rows:
                        raise ValueError('missing sealed start')
                    result = study.envelope(identity)['result']
                    for variant, key in (('wide', 'reference'),
                                         ('hybrid', 'candidate')):
                        forecast = study.artifact(identity, variant+'-forecast.json')
                        input_binding = study.artifact(
                            identity, variant+'-input-binding.json')
                        variants[variant].append(dict(
                            start=start,
                            training_cost=result[key]['training_cost'],
                            passed=result[key]['passed'],
                            binding=digest(encoded(dict(input=input_binding,
                                times_s=forecast['times_s']))),
                            forecast=world_coordinates(
                                forecast['coordinates'], model)))
                # The original verified report already checks exact input/time
                # bindings. Preserve its result; this audit only adds spread.
                row = audit_start_spread(
                    variants['wide'], variants['hybrid'],
                    relative_cost_tolerance=settings['relative_cost_tolerance'],
                    forecast_tolerance_m=settings['paired_prediction_tolerance_m'],
                    absolute_cost_tolerance=absolute_cost_tolerance)
                groups.append(dict(model=model, profile=profile, **row))
        return dict(verified=sealed['verified'],
                    frozen_qualified=sealed['qualified'],
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    absolute_cost_tolerance=absolute_cost_tolerance,
                    groups=groups)
    finally:
        study.close()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--study', default='data/model-declared-start-equivalence-v1')
    parser.add_argument('--absolute-cost-tolerance', type=float, required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh diagnostic output required')
    report = audit_sealed_study(args.root, args.study,
        absolute_cost_tolerance=args.absolute_cost_tolerance)
    report.update(version='saved-start-spread-v2-diagnostic',
        study=args.study,
        diagnostic_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        comparator_source_sha256=hashlib.sha256(
            Path(compare_start_sets_v2.__code__.co_filename).read_bytes()).hexdigest(),
        new_numerical_fits=0,
        retrospective_only=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    print(json.dumps(dict(verified=report['verified'],
        frozen_qualified=report['frozen_qualified'],
        revised_passing_groups=sum(row['revised_rule_development_diagnostic']['equivalent']
            for row in report['groups']), groups=len(report['groups'])), sort_keys=True))


if __name__ == '__main__':
    main()
