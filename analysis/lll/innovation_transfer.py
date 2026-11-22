# SPDX-License-Identifier: AGPL-3.0-or-later
"""Directional and chronological checks on saved forecast error innovations."""


def _series(values):
    import numpy as np

    result = np.asarray(values, float)
    if (result.ndim != 2 or result.shape[1] != 3 or len(result) < 4
            or not np.isfinite(result).all()):
        raise ValueError('finite complete three-channel error series required')
    return result


def estimates(values):
    """Estimate the working zero-mean score scales from one earlier window."""
    import numpy as np

    series = _series(values)
    moments = series.T@series/len(series)
    np.linalg.cholesky(moments)
    return dict(common=np.eye(3)*np.trace(moments)/3,
                per_channel=np.diag(np.diag(moments)), full=moments)


def score(values, covariance):
    import numpy as np
    from scipy.linalg import solve_triangular

    series = _series(values)
    factors = np.linalg.cholesky(np.asarray(covariance, float))
    innovations = solve_triangular(factors, series.T, lower=True)
    return float(np.mean(innovations**2))


def diagnose(values, *, blocks, peaks):
    """Use fixed contiguous blocks and fixed largest-epoch energy shares."""
    import numpy as np

    series = _series(values)
    count = len(series)
    if (type(blocks) is not int or not 2 <= blocks <= count or count % blocks
            or type(peaks) is not int or not 1 <= peaks <= count):
        raise ValueError('equal chronological blocks and a fixed peak count required')
    squared = series**2
    energy = squared.sum(axis=0)
    denom = np.where(energy>0, energy, 1.)
    mean = series.mean(axis=0)
    before = series[:-1]-series[:-1].mean(axis=0)
    after = series[1:]-series[1:].mean(axis=0)
    correlation_denom = np.linalg.norm(before, axis=0)*np.linalg.norm(after, axis=0)
    return dict(mean=mean.tolist(), channel_energy=energy.tolist(),
                mean_fraction_of_energy=(count*mean**2/denom).tolist(),
                block_energy_shares=(squared.reshape(blocks,count//blocks,3).sum(axis=1)/denom).tolist(),
                largest_epoch_energy_share=(np.sort(squared,axis=0)[-peaks:].sum(axis=0)/denom).tolist(),
                lag_one_centered=[float(x/y) if y > 0 else None
                                  for x,y in zip(np.sum(before*after,axis=0),correlation_denom,strict=True)])
