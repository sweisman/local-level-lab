# SPDX-License-Identifier: AGPL-3.0-or-later
"""Split sealed affine forecast widths into calibration and future noise."""

import hashlib
import json
from pathlib import Path

from .generated_esa_bounded_pilot_v2 import ID, PLAN, recipe
from .generated_esa_bounded_pilot_v2_report import build as verified_pilot


AUDIT_PLAN = ('docs/prediction-observed-development/'
              'GENERATED_BOUND_COMPONENTS_PLAN.md')
INDICES = (0, 59, 119, 299)
AXES = ('north', 'east', 'up')


def decompose(bounds, covariance):
    """Recover two nonnegative half-width components under the fixed law."""
    import numpy as np
    from scipy.stats import norm

    lo = np.asarray(bounds.get('lower'), dtype=float)
    hi = np.asarray(bounds.get('upper'), dtype=float)
    cov = np.asarray(covariance, dtype=float)
    if (bounds.get('scope') != 'affine_known_gaussian_box'
            or bounds.get('marginal_coverage_lower_bound') != .95
            or type(bounds.get('calibration_directions')) is not int
            or bounds['calibration_directions'] < 1
            or bounds.get('discarded_directions') != 0
            or cov.ndim != 3 or not len(cov) or
            cov.shape[1] != cov.shape[2] or cov.shape[1] < 1
            or lo.shape != (cov.shape[0]*cov.shape[1],)
            or hi.shape != lo.shape
            or any(not np.all(np.isfinite(item)) for item in (lo, hi, cov))
            or np.any(lo >= hi)):
        raise ValueError('full-rank matched affine intervals required')
    variance = np.diagonal(cov, axis1=1, axis2=2).ravel()
    if np.any(variance <= 0):
        raise ValueError('positive finite conditional variance required')
    half = (hi-lo)/2
    future = norm.isf(.025/2)*np.sqrt(variance)
    calibration = half-future
    if np.any(calibration < -1e-10*np.maximum(half, future)):
        raise ValueError('future radius exceeds saved interval width')
    calibration = np.maximum(calibration, 0.)
    return dict(calibration_halfwidth=calibration,
                future_halfwidth=future,
                total_halfwidth=half,
                calibration_fraction=calibration/half)


def build(root):
    from .studies.closed import ClosedStudy
    import numpy as np

    root = Path(root).resolve()
    original = verified_pilot(root)
    if (original['tasks_total'] != 2 or original['technical_passing'] != 2
            or original['original_physical_passing'] != 0):
        raise ValueError('closed two-law technical pilot required')
    study = ClosedStudy(root, 'data/' + ID)
    try:
        if study.input('recipe') != recipe():
            raise ValueError('generated recipe changed')
        rows = {}
        for law in ('increment', 'point'):
            bound_raw = study.artifact(law, 'bounded-physical.json', raw=True)
            bound = json.loads(bound_raw)
            diagnostic_raw = study.artifact(
                law, 'forecast-error-diagnostic.json', raw=True)
            diagnostic = json.loads(diagnostic_raw)
            fixed = diagnostic.get('fixed_parameters', {})
            if (hashlib.sha256(bound_raw).hexdigest() !=
                    original['laws'][law]['bound_artifact_sha256']
                    or bound.get('prediction_epochs') != 300
                    or bound.get('training_epochs') != 600
                    or bound.get('retained_calibration_columns') != 26
                    or bound.get('calibration_directions') != 26
                    or bound.get('discarded_directions') != 0
                    or fixed.get('conditioning_epochs') != 600
                    or fixed.get('forecast_epochs') != 300
                    or fixed.get('later_observations_used') is not False
                    or diagnostic.get('error_operator', {}).get(
                        'operator_configuration') != bound.get(
                            'error_operator_configuration')):
                raise ValueError('mismatched full-rank earlier-only forecast')
            values = decompose(bound, fixed['covariance'])
            fractions = values['calibration_fraction'].reshape(300, 3)
            rows[law] = dict(
                calibration_directions=26, discarded_directions=0,
                median_calibration_fraction_by_axis={
                    name: float(np.median(fractions[:, axis]))
                    for axis, name in enumerate(AXES)},
                selected_epoch_calibration_fraction={
                    str(index): {name: float(fractions[index, axis])
                                 for axis, name in enumerate(AXES)}
                    for index in INDICES},
                bound_artifact_sha256=hashlib.sha256(bound_raw).hexdigest(),
                diagnostic_artifact_sha256=hashlib.sha256(
                    diagnostic_raw).hexdigest())
        return dict(version='generated-esa-bound-components-report-v1',
                    verified=True, study='data/' + ID,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    plan_sha256=hashlib.sha256((root / AUDIT_PLAN).read_bytes()).hexdigest(),
                    original_plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
                    tasks_total=2, laws=rows, new_fits=0,
                    original_reads=0, protected_reads=0,
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
        raise ValueError('fresh saved-width report required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps({law: row['median_calibration_fraction_by_axis']
                      for law, row in result['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
