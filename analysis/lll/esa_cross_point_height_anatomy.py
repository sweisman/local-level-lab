# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only timing and commonality of ESA height prediction errors."""

import gzip
import hashlib
import json
from pathlib import Path

from .esa_conditional_cross_point_coverage import (
    HISTORICAL, ID, SCORING_SHA256, TASK, WEIGHTED, WEIGHTED_TASK,
)


def describe(errors_m, sigma_m):
    import numpy as np

    error = np.asarray(errors_m, dtype=float)
    sigma = np.asarray(sigma_m, dtype=float)
    if (error.ndim != 1 or error.size == 0 or sigma.shape != error.shape
            or not np.all(np.isfinite(error)) or not np.all(np.isfinite(sigma))
            or np.any(sigma <= 0)):
        raise ValueError('aligned finite height error and positive sigma required')
    z = np.abs(error / sigma)
    misses = z > 1.96
    first = int(np.flatnonzero(misses)[0]) if np.any(misses) else None
    longest = run = 0
    for missed in misses:
        run = run + 1 if missed else 0
        longest = max(longest, run)
    return dict(epochs=int(error.size),
        nominal_95_inside=int(error.size - np.count_nonzero(misses)),
        first_nominal_95_miss_index=first,
        longest_nominal_95_miss_run=longest,
        last_signed_error_m=float(error[-1]),
        empirical_95_absolute_z=float(np.quantile(z, .95)),
        empirical_95_scale_factor=float(np.quantile(z, .95) / 1.96),
        signed_error_mean_m=float(np.mean(error)))


def build(root):
    import numpy as np
    from .esa_conditional_cross_point_coverage import build as checked_coverage
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    prior = checked_coverage(root)
    if (prior['prediction_epochs'] != 400 or prior['calibrated_coverage'] is not False
            or prior['scientific_decision'] != 'abstain'):
        raise ValueError('failed, uncalibrated saved coverage required')
    current = ClosedStudy(root, 'data/' + ID)
    weighted = ClosedStudy(root, WEIGHTED)
    historical = ClosedStudy(root, HISTORICAL)
    try:
        if (current.completion['manifest_sha256'] != prior['manifest_sha256']
                or current.completion['summary_sha256'] != prior['summary_sha256']
                or historical.manifest['inputs']['scoring']['sha256']
                   != SCORING_SHA256):
            raise ValueError('sealed forecast or receiver scoring changed')
        rows = json.loads(gzip.decompress(historical.input('scoring', raw=True)))
        if len(rows) != 1200:
            raise ValueError('complete 800/400 receiver split required')
        height = np.asarray([row['height_m'] for row in rows[800:]], float)
        forecasts = dict(
            receiver_only_point=current.artifact(TASK, 'conditional-forecast.json'),
            weighted_point=weighted.artifact(
                WEIGHTED_TASK, 'conditional-forecast.json'))
        output, errors = {}, {}
        for name, forecast in forecasts.items():
            mean = np.asarray(forecast['conditional_receiver_mean'], float)
            covariance = np.asarray(
                forecast['conditional_receiver_covariance'], float)
            if (mean.shape != (400, 3) or covariance.shape != (400, 3, 3)
                    or not np.all(np.isfinite(mean))
                    or not np.all(np.isfinite(covariance))):
                raise ValueError('complete finite saved forecast required')
            error = mean[:, 2] - height
            sigma = np.sqrt(covariance[:, 2, 2])
            output[name] = describe(error, sigma)
            if (output[name]['nominal_95_inside'] != round(
                    400 * prior['coverage'][name]['axes']['up']['nominal_95_fraction'])):
                raise ValueError('saved height coverage differs from prior report')
            errors[name] = error
        first, second = errors['receiver_only_point'], errors['weighted_point']
        return dict(version='esa-saved-height-error-anatomy-v1',
            verified=True, study='data/' + ID,
            manifest_sha256=prior['manifest_sha256'],
            summary_sha256=prior['summary_sha256'],
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            height=output,
            cross_point_signed_error_correlation=float(np.corrcoef(first, second)[0, 1]),
            cross_point_height_difference_rms_m=float(
                np.sqrt(np.mean((first-second)**2))),
            cross_point_same_error_sign_fraction=float(
                np.mean(np.sign(first) == np.sign(second))),
            new_fits=0, original_reads=0, reserved_groups_opened=0,
            calibrated_coverage=False, scientific_decision='abstain')
    finally:
        historical.close()
        weighted.close()
        current.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh diagnostic output required')
    result = build(args.root)
    atomic(target, encoded(result))
    print(json.dumps(dict(
        height_inside={k: v['nominal_95_inside'] for k, v in result['height'].items()},
        error_correlation=result['cross_point_signed_error_correlation']),
        sort_keys=True))


if __name__ == '__main__':
    main()
