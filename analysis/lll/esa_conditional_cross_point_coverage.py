# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare saved conditional uncertainty at two ESA development fit points."""

import gzip
import hashlib
import json
import math
from pathlib import Path

from .esa_conditional_cross_point_report import build as checked_comparison
from .esa_conditional_cross_point_v3_study import ID
from .esa_conditional_cross_point_study import WEIGHTED
from .esa_conditional_forecast_report import HISTORICAL, SCORING_SHA256

TASK = 'receiver-only-point-under-weighted-law'
WEIGHTED_TASK = 'single-pass-receiver-conditional'


def matched_forecasts(receiver_only, weighted):
    """Require one sealed early-only grid and identical complete error law."""
    if (receiver_only.get('training_epochs') != 800 or
            receiver_only.get('prediction_epochs') != 400 or
            receiver_only.get('times_s') != weighted.get('times_s') or
            receiver_only.get('full_operator_configuration') !=
                weighted.get('full_operator_configuration') or
            any(value.get('later_receiver_values_used') is not False or
                value.get('optimization_performed') is not False or
                value.get('fixed_calibration_only') is not True
                for value in (receiver_only, weighted))):
        raise ValueError('two sealed same-law early-only forecasts required')
    return True


def build(root):
    import numpy as np
    from .esa_conditional_coverage_report import describe_coverage
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    comparison = checked_comparison(root)
    current = ClosedStudy(root, 'data/'+ID)
    weighted_study = ClosedStudy(root, WEIGHTED)
    historical = ClosedStudy(root, HISTORICAL)
    try:
        if (current.completion['manifest_sha256'] !=
                comparison['manifest_sha256'] or
            current.completion['summary_sha256'] !=
                comparison['summary_sha256'] or
            historical.manifest['inputs']['scoring']['sha256'] !=
                SCORING_SHA256):
            raise ValueError('exact sealed cross-point comparison required')
        forecasts = {
            'receiver_only_point': current.artifact(TASK, 'conditional-forecast.json'),
            'weighted_point': weighted_study.artifact(
                WEIGHTED_TASK, 'conditional-forecast.json')}
        matched_forecasts(*forecasts.values())
        rows = json.loads(gzip.decompress(historical.input('scoring', raw=True)))
        if len(rows) != 1200:
            raise ValueError('exact 800/400 receiver split required')
        receiver = np.asarray([[math.radians(row['latitude_deg']),
            math.radians(row['longitude_deg']), row['height_m']]
            for row in rows[800:]], dtype=float)
        coverage = {name: describe_coverage(
            forecast['conditional_receiver_mean'], receiver,
            forecast['conditional_receiver_covariance'])
            for name, forecast in forecasts.items()}
        return dict(version='esa-cross-point-coverage-v1',
            study='data/'+ID,
            manifest_sha256=comparison['manifest_sha256'],
            summary_sha256=comparison['summary_sha256'],
            scoring_sha256=SCORING_SHA256,
            reporter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            same_complete_error_law=True,
            training_epochs=800, prediction_epochs=400,
            coverage=coverage,
            protected_confirmation_groups_opened=0,
            calibration_parameter_uncertainty_included=False,
            calibrated_coverage=False, scientific_decision='abstain')
    finally:
        historical.close()
        weighted_study.close()
        current.close()


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh coverage report path required')
    result = build(args.root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps({name: {axis: round(row['axes'][axis]['nominal_95_fraction']*400)
        for axis in ('north', 'east', 'up')}
        for name, row in result['coverage'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
