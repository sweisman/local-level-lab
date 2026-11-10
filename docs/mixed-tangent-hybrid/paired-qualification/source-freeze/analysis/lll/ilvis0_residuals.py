# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive epoch residual diagnostics; no optimization or adequacy decisions."""
import numpy as np

from .ilvis0_saved_audit import rank_correlation

VERSION = 'ilvis0-epoch-residual-diagnostics-v1'


def samples(values):
    values = np.asarray(values, float)
    if values.ndim != 1 or len(values) == 0 or not np.all(np.isfinite(values)):
        raise ValueError('finite nonempty residual vector required')
    return values


def distribution(values):
    x = samples(values)
    return dict(mean=float(x.mean()), rms=float(np.sqrt(np.mean(x*x))),
                centered_rms=float(x.std()), absolute_median=float(np.median(abs(x))),
                absolute_p95=float(np.quantile(abs(x), .95)),
                absolute_p99=float(np.quantile(abs(x), .99)),
                absolute_max=float(np.max(abs(x))),
                fraction_absolute_gt_3=float(np.mean(abs(x) > 3)))


def autocorrelation(values, lag):
    x = samples(values)
    if not isinstance(lag, int) or lag <= 0:
        raise ValueError('positive integer epoch lag required')
    if lag >= len(x):
        return None
    x = x-x.mean(); norm = float(x@x)
    return float(x[:-lag]@x[lag:]/norm) if norm else None


def summarize(times, physical, primary, conservative, covariates):
    t = samples(times)
    if len(t) < 3 or np.any(np.diff(t) <= 0):
        raise ValueError('at least three increasing receiver epochs required')
    arrays = [np.asarray(x, float) for x in (physical, primary, conservative)]
    if any(x.shape != (len(t), 3) or not np.all(np.isfinite(x)) for x in arrays):
        raise ValueError('finite aligned residual axes required')
    cov = {k: samples(v) for k, v in covariates.items()}
    if any(len(v) != len(t) for v in cov.values()):
        raise ValueError('unaligned receiver covariate')
    axes = []
    for i, name in enumerate(('north', 'east', 'up')):
        a, z, c = [v[:, i] for v in arrays]
        lags = []
        for lag in (1, 5, 10, 30, 60):
            if lag < len(t):
                delta = t[lag:]-t[:-lag]
                lags.append(dict(lag_epochs=lag, median_lag_s=float(np.median(delta)),
                                 min_lag_s=float(delta.min()), max_lag_s=float(delta.max()),
                                 primary=autocorrelation(z, lag),
                                 conservative=autocorrelation(c, lag),
                                 physical=autocorrelation(a, lag)))
        axes.append(dict(axis=name, physical=distribution(a), primary=distribution(z),
                         conservative=distribution(c), autocorrelation=lags,
                         associations={k: rank_correlation(a.tolist(), v.tolist()) for k, v in cov.items()}))
    step = np.diff(t)
    return dict(epochs=len(t), sample_intervals_s=dict(min=float(step.min()),
                median=float(np.median(step)), max=float(step.max())), axes=axes,
                held_out_validation=False, absolute_fit_status='not_calibrated',
                native_predictions=0, scientific_decision='abstain')
