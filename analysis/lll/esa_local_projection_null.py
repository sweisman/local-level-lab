# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved ESA tangent projection check for fit-induced training correlation."""

import hashlib
import json
import math
from pathlib import Path


SEED = 20261117
MAX_DRAWS = 2048
PUBLIC = 'docs/prediction-observed-development/training-innovation-result.json'


def projected_draws(jacobian, *, draws, seed):
    import numpy as np

    matrix = np.asarray(jacobian, dtype=float)
    if (matrix.ndim != 2 or matrix.shape[0] <= matrix.shape[1]
            or not np.all(np.isfinite(matrix))
            or type(draws) is not int or not 1 <= draws <= MAX_DRAWS
            or type(seed) is not int or seed < 0):
        raise ValueError('finite, overdetermined tangent and bounded draw count required')
    left, singular, _ = np.linalg.svd(matrix, full_matrices=False)
    rank = int(np.count_nonzero(singular > singular[0] * 1e-10))
    if singular[0] <= 0 or rank != matrix.shape[1]:
        raise ValueError('full-rank saved tangent required')
    basis = left[:, :rank]
    independent = np.random.default_rng(seed).standard_normal(
        (matrix.shape[0], draws))
    return independent - basis @ (basis.T @ independent), rank


def _correlations(residuals, lag):
    import numpy as np

    left = residuals[:-lag] - np.mean(residuals[:-lag], axis=0)
    right = residuals[lag:] - np.mean(residuals[lag:], axis=0)
    numerator = np.sum(left * right, axis=0)
    denominator = np.sqrt(np.sum(left * left, axis=0) *
                          np.sum(right * right, axis=0))
    if np.any(denominator <= 0):
        raise ValueError('degenerate projected error history')
    return numerator / denominator


def build(root, *, draws=MAX_DRAWS):
    import numpy as np
    from .esa_training_innovation_study import ID as INNOVATION_ID
    from .esa_training_split_study import ID as FIT_ID, LAWS
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    public_bytes = (root / PUBLIC).read_bytes()
    published = json.loads(public_bytes)
    innovation = ClosedStudy(root, 'data/' + INNOVATION_ID)
    fit_study = ClosedStudy(root, 'data/' + FIT_ID)
    try:
        if (published.get('version') != 'esa-training-innovation-diagnostic-v1'
                or published.get('training_epochs') != 600
                or published.get('study_manifest_sha256') !=
                    innovation.completion['manifest_sha256']
                or published.get('study_summary_sha256') !=
                    innovation.completion['summary_sha256']
                or published.get('fit_manifest_sha256') !=
                    fit_study.completion['manifest_sha256']
                or innovation.completion['state'] != 'complete'
                or fit_study.completion['state'] != 'complete'
                or set(innovation.tasks) != set(LAWS)
                or set(fit_study.tasks) != set(LAWS)):
            raise ValueError('sealed matching ESA training studies required')
        result = {}
        for law in LAWS:
            record = fit_study.artifact(law, 'fit.json')
            linear = record.get('local_linearization', {})
            jacobian = np.asarray(linear.get('jacobian'), dtype=float)
            residual = np.asarray(linear.get('residual'), dtype=float)
            if (record.get('converged') is not True
                    or record.get('stopping_rule_verified') is not True
                    or record.get('active_bounds') != []
                    or linear.get('convention') !=
                       'whitened residual derivative by normalized parameter'
                    or jacobian.shape != (1800, 26)
                    or residual.shape != (1800,)
                    or len(linear.get('active_parameters', [])) != 26
                    or not np.all(np.isfinite(residual))
                    or not np.all(np.isfinite(jacobian))
                    or not math.isclose(float(residual @ residual),
                                        record['residual_sum_squares'],
                                        rel_tol=1e-10, abs_tol=1e-10)):
                raise ValueError('complete unconstrained ESA fitted tangent required')
            projected, rank = projected_draws(
                jacobian, draws=draws, seed=SEED)
            basis, _, _ = np.linalg.svd(jacobian, full_matrices=False)
            projection_fraction = float(np.linalg.norm(basis.T @ residual) /
                                        np.linalg.norm(residual))
            if projection_fraction >= 1e-3:
                raise ValueError('saved fit is not near a local stationary point')
            actual = residual[2::3]
            simulated = projected[2::3]
            saved = published['laws'][law]['channels'][2]
            if (saved['index'] != 2 or not math.isclose(
                    float(np.sqrt(np.mean(actual * actual))), saved['rms'],
                    rel_tol=1e-8, abs_tol=1e-8)):
                raise ValueError('published fitted height error differs')
            lags = {}
            for lag in (1, 20):
                observed = float(_correlations(actual[:, None], lag)[0])
                if not math.isclose(observed, saved['lags'][str(lag)],
                                    rel_tol=1e-7, abs_tol=1e-7):
                    raise ValueError('published correlation differs')
                null = np.abs(_correlations(simulated, lag))
                exceed = int(np.count_nonzero(null >= abs(observed)))
                lags[str(lag)] = dict(
                    observed=observed,
                    null_abs_median=float(np.median(null)),
                    null_abs_p95=float(np.quantile(null, .95)),
                    null_abs_p99=float(np.quantile(null, .99)),
                    null_abs_maximum=float(np.max(null)),
                    draws=draws, exceedances=exceed,
                    plus_one_tail_fraction=(exceed + 1) / (draws + 1))
            result[law] = dict(
                rank=rank, active_bounds=0,
                fitted_residual_projection_fraction=projection_fraction,
                observed_whitened_height_rms=saved['rms'],
                lag_correlations=lags,
                fit_artifact_sha256=hashlib.sha256(fit_study.artifact(
                    law, 'fit.json', raw=True)).hexdigest())
        return dict(version='esa-local-projection-null-v1', verified=True,
            source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            plan_sha256=hashlib.sha256((root / 'docs/prediction-observed-development/'
                'LOCAL_PROJECTION_NULL_PLAN.md').read_bytes()).hexdigest(),
            public_report_sha256=hashlib.sha256(public_bytes).hexdigest(),
            fit_manifest_sha256=fit_study.completion['manifest_sha256'],
            innovation_manifest_sha256=innovation.completion['manifest_sha256'],
            seed=SEED, draws_per_law=draws, training_epochs=600,
            laws=result, new_fits=0, original_reads=0, later_receiver_reads=0,
            protected_reads=0, local_linear_null_only=True,
            error_law_qualified=False, scientific_decision='abstain')
    finally:
        fit_study.close()
        innovation.close()


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh local-projection output required')
    report = build(args.root)
    atomic(target, encoded(report))
    print(json.dumps({law: {lag: row['exceedances'] for lag, row in
        item['lag_correlations'].items()} for law, item in
        report['laws'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
