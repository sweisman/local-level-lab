# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only joint Gaussian expansion of generated marginal forecast bounds.

This is conditional affine arithmetic, not empirical coverage calibration.
"""

import hashlib
import json
from pathlib import Path

from .generated_esa_bounded_pilot_v2 import ID, PLAN, recipe
from .generated_esa_bounded_pilot_v2_report import (
    build as verified_pilot, interval_coverage, interval_span)


AUDIT_PLAN = ('docs/prediction-observed-development/'
              'GENERATED_SIMULTANEOUS_BOUND_PLAN.md')


def expand(bounds, covariance, *, calibration_alpha, future_alpha):
    """Apply a future-noise union bound to unchanged calibration intervals."""
    import numpy as np
    from scipy.stats import norm

    lo = np.asarray(bounds.get('lower'), dtype=float)
    hi = np.asarray(bounds.get('upper'), dtype=float)
    cov = np.asarray(covariance, dtype=float)
    if (bounds.get('scope') != 'affine_known_gaussian_box'
            or bounds.get('simultaneous_coverage_established') is not False
            or bounds.get('marginal_coverage_lower_bound') != .95
            or calibration_alpha != .025 or future_alpha != .025
            or cov.ndim != 3 or not len(cov)
            or cov.shape[1] != cov.shape[2] or cov.shape[1] < 1
            or lo.shape != (cov.shape[0] * cov.shape[1],)
            or hi.shape != lo.shape
            or not all(np.all(np.isfinite(x)) for x in (lo, hi, cov))
            or np.any(lo >= hi)
            or not np.allclose(cov, np.swapaxes(cov, 1, 2),
                               rtol=1e-10, atol=1e-20)):
        raise ValueError('matched sealed marginal bounds and covariance required')
    variance = np.diagonal(cov, axis1=1, axis2=2)
    if np.any(variance <= 0):
        raise ValueError('positive conditional variance required')
    count = lo.size
    marginal_z = norm.isf(future_alpha / 2)
    joint_z = norm.isf(future_alpha / (2 * count))
    extra = (joint_z - marginal_z) * np.sqrt(variance.ravel())
    lower = lo - extra
    upper = hi + extra
    if not all(np.all(np.isfinite(x)) for x in (extra, lower, upper)):
        raise ValueError('finite expanded interval required')
    return dict(lower=lower.tolist(), upper=upper.tolist(),
                coordinate_count=count, marginal_future_z=float(marginal_z),
                simultaneous_future_z=float(joint_z),
                nominal_joint_coverage_lower_bound=1-calibration_alpha-future_alpha,
                future_union_method='Bonferroni across all later coordinates',
                assumptions_qualified_for_aircraft=False)


def build(root):
    """Verify and report both sealed generated cases without native work."""
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    original = verified_pilot(root)
    if (original['tasks_total'] != 2
            or original['technical_passing'] != 2
            or original['original_physical_passing'] != 0
            or original['scientific_decision'] != 'abstain'):
        raise ValueError('exact closed generated technical pilot required')
    study = ClosedStudy(root, 'data/' + ID)
    try:
        if study.input('recipe') != recipe():
            raise ValueError('generated recipe changed')
        rows = {}
        for law in ('increment', 'point'):
            bound_bytes = study.artifact(law, 'bounded-physical.json', raw=True)
            if hashlib.sha256(bound_bytes).hexdigest() != original['laws'][law][
                    'bound_artifact_sha256']:
                raise ValueError('bound artifact differs from verified pilot')
            bound = json.loads(bound_bytes)
            diagnostic_bytes = study.artifact(
                law, 'forecast-error-diagnostic.json', raw=True)
            diagnostic = json.loads(diagnostic_bytes)
            scoring = study.artifact(law, 'scoring-observations.json')
            fixed = diagnostic.get('fixed_parameters', {})
            if (diagnostic.get('prediction_target') != 'physical_position'
                    or diagnostic.get('later_observations_used') is not False
                    or diagnostic.get('training_epochs') != 600
                    or diagnostic.get('prediction_epochs') != 300
                    or diagnostic.get('error_operator', {}).get(
                        'operator_configuration') != bound.get(
                            'error_operator_configuration')
                    or fixed.get('conditioning_epochs') != 600
                    or fixed.get('forecast_epochs') != 300
                    or fixed.get('later_observations_used') is not False
                    or fixed.get('parameter_uncertainty_included') is not False
                    or bound.get('true_calibration_inside_box_assumed') is not True
                    or bound.get('error_covariance_known_assumed') is not True
                    or bound.get('retained_calibration_columns') != 26
                    or len(scoring.get('coordinates', [])) != 900):
                raise ValueError('mismatched or non-earlier-only forecast')
            covariance = fixed['covariance']
            if len(covariance) != 300:
                raise ValueError('all later conditional variances required')
            expanded = expand(bound, covariance, calibration_alpha=.025,
                              future_alpha=.025)
            if expanded['coordinate_count'] != 900:
                raise ValueError('exact 900-coordinate union required')
            truth = scoring['coordinates'][600:]
            coverage = interval_coverage(expanded, truth)
            marginal_span = interval_span(bound, truth)
            joint_span = interval_span(expanded, truth)
            rows[law] = dict(
                original_physical_passed=False,
                all_generated_truth_coordinates_covered=(
                    coverage['all_coordinates_covered']),
                covered_epochs=coverage['covered_epochs'],
                marginal_median_neu_span_m=(
                    marginal_span['median_neu_span_m']),
                simultaneous_median_neu_span_m=(
                    joint_span['median_neu_span_m']),
                maximum_simultaneous_neu_span_m=(
                    joint_span['maximum_neu_span_m']),
                marginal_future_z=expanded['marginal_future_z'],
                simultaneous_future_z=expanded['simultaneous_future_z'],
                bound_artifact_sha256=hashlib.sha256(bound_bytes).hexdigest(),
                diagnostic_artifact_sha256=hashlib.sha256(
                    diagnostic_bytes).hexdigest())
        return dict(version='generated-esa-simultaneous-bound-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    original_plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    audit_plan_sha256=hashlib.sha256((root / AUDIT_PLAN).read_bytes()).hexdigest(),
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    tasks_total=2, original_physical_passing=0,
                    nominal_joint_coverage_lower_bound=.95,
                    coordinate_count_per_case=900, laws=rows,
                    new_fits=0, original_reads=0, protected_reads=0,
                    nonlinear_coverage_qualified=False,
                    aircraft_error_law_qualified=False,
                    scientific_decision='abstain')
    finally:
        study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh saved-data report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps(dict(tasks_total=result['tasks_total'],
                          original_physical_passing=result[
                              'original_physical_passing'],
                          covered_epochs={name: row['covered_epochs']
                                          for name, row in result['laws'].items()}),
                     sort_keys=True))


if __name__ == '__main__':
    main()
