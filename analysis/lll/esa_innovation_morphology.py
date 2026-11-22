# SPDX-License-Identifier: AGPL-3.0-or-later
"""Describe saved ESA training-innovation persistence without refitting."""

import hashlib
import json
import math
from pathlib import Path

from .prediction_fitted_innovation_audit import correlation


PLAN = 'docs/prediction-observed-development/INNOVATION_MORPHOLOGY_PLAN.md'
PUBLIC = 'docs/prediction-observed-development/training-innovation-result.json'


def two_lag_curve(first, twentieth):
    if (not all(type(x) in (int, float) and math.isfinite(x)
                for x in (first, twentieth))
            or not 0 < twentieth < first < 1):
        return dict(status='not_described')
    scale = -19. / math.log(twentieth / first)
    amplitude = first * math.exp(1. / scale)
    if not math.isfinite(amplitude) or amplitude > 1:
        return dict(status='not_described')
    return dict(status='descriptive_two_lag_curve', amplitude=amplitude,
                scale_reports=scale,
                lag5_prediction=amplitude * math.exp(-5. / scale))


def _long_period_fraction(values, period):
    import numpy as np

    data = np.asarray(values, dtype=float)
    spectrum = np.fft.rfft(data - np.mean(data))
    frequency = np.fft.rfftfreq(len(data))
    power = np.abs(spectrum) ** 2
    weights = np.full(len(power), 2.)
    weights[0] = 1.
    if len(data) % 2 == 0:
        weights[-1] = 1.
    power *= weights
    denominator = float(np.sum(power[1:]))
    if denominator <= 0:
        raise ValueError('nonconstant finite error history required')
    return float(np.sum(power[(frequency > 0) &
                              (frequency <= 1. / period)]) / denominator)


def _axis_summary(values):
    return dict(
        shifted_correlations=[correlation(values, lag)
                              for lag in range(1, 121)],
        spectral_fraction_period_over_60_reports=
            _long_period_fraction(values, 60),
        spectral_fraction_period_over_120_reports=
            _long_period_fraction(values, 120))


def build(root):
    import numpy as np
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    published_bytes = (root / PUBLIC).read_bytes()
    published = json.loads(published_bytes)
    fit_study = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        if (fit_study.completion['state'] != 'complete'
                or published.get('training_epochs') != 600
                or published.get('fit_manifest_sha256') !=
                    fit_study.completion['manifest_sha256']
                or set(fit_study.tasks) != set(LAWS)):
            raise ValueError('matching sealed 600-report development fits required')
        laws = {}
        for law in LAWS:
            fit = fit_study.artifact(law, 'fit.json')
            linear = fit.get('local_linearization', {})
            residual = linear.get('residual')
            training = fit_study.artifact(law, 'training-observations.json')
            times = np.asarray(training.get('times_s'), dtype=float)
            if (fit.get('converged') is not True
                    or fit.get('stopping_rule_verified') is not True
                    or linear.get('convention') !=
                        'whitened residual derivative by normalized parameter'
                    or not isinstance(residual, list)
                    or len(residual) != 1800 or len(times) != 600
                    or training.get('training_epochs') != 600
                    or not np.all(np.isfinite(times))
                    or np.any(np.diff(times) <= 0)
                    or any(type(x) not in (int, float) or not math.isfinite(x)
                           for x in residual)
                    or not math.isclose(sum(x*x for x in residual),
                                        fit['residual_sum_squares'],
                                        rel_tol=1e-10, abs_tol=1e-10)):
                raise ValueError('unchanged finite fitted training residual required')
            channels = {}
            matrix = np.asarray(residual).reshape(600, 3)
            for axis, name in enumerate(('north', 'east', 'height')):
                series = matrix[:, axis].tolist()
                saved = published['laws'][law]['channels'][axis]
                summary = _axis_summary(series)
                for lag in (1, 5, 20):
                    if not math.isclose(
                            summary['shifted_correlations'][lag-1],
                            saved['lags'][str(lag)],
                            rel_tol=1e-7, abs_tol=1e-7):
                        raise ValueError('published training correlation differs')
                channels[name] = summary
            cross = np.corrcoef(matrix, rowvar=False)
            if not np.all(np.isfinite(cross)):
                raise ValueError('finite cross-axis correlation required')
            height = channels['height']['shifted_correlations']
            model = two_lag_curve(height[0], height[19])
            if model['status'] == 'descriptive_two_lag_curve':
                model['lag5_observed'] = height[4]
                model['lag5_prediction_error'] = (
                    height[4] - model['lag5_prediction'])
            laws[law] = dict(
                axes=channels,
                cross_axis_correlation=cross.tolist(),
                report_spacing_s=dict(
                    minimum=float(np.min(np.diff(times))),
                    maximum=float(np.max(np.diff(times))),
                    median=float(np.median(np.diff(times)))),
                height_two_lag_model=model,
                fit_artifact_sha256=hashlib.sha256(fit_study.artifact(
                    law, 'fit.json', raw=True)).hexdigest())
        return dict(version='esa-saved-innovation-morphology-v1',
            verified=True, training_epochs=600, laws=laws,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            plan_sha256=hashlib.sha256((root / PLAN).read_bytes()).hexdigest(),
            fit_manifest_sha256=fit_study.completion['manifest_sha256'],
            public_report_sha256=hashlib.sha256(published_bytes).hexdigest(),
            new_fits=0, original_reads=0, later_receiver_reads=0,
            protected_reads=0, error_source_identified=False,
            aircraft_error_law_qualified=False,
            scientific_decision='abstain')
    finally:
        fit_study.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh saved morphology output required')
    report = build(args.root)
    atomic(target, encoded(report))
    print(json.dumps({law: item['height_two_lag_model'] for law, item in
        report['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
