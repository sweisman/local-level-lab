# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forecast persistent relative GPS position offsets from observed earlier offsets."""

import math

from .receiver_contrast_covariance import RIDGE_FRACTION, gaussian_loss


CANDIDATES = (('independent', None), ('walk', None)) + tuple(
    ('reverting', time) for time in (2., 5., 10., 20., 40.)
)


def predictability(law, memory, elapsed):
    """Return variance growth and memory of the last observed offset."""
    import numpy as np

    elapsed = np.asarray(elapsed, float)
    if not np.isfinite(elapsed).all() or np.any(elapsed <= 0.):
        raise ValueError('positive finite elapsed windows required')
    if law == 'independent':
        return np.ones_like(elapsed), np.zeros_like(elapsed)
    if law == 'walk':
        return elapsed, np.ones_like(elapsed)
    if law != 'reverting' or memory is None or not math.isfinite(memory) or memory <= 0.:
        raise ValueError('the mean-reverting model needs a positive memory')
    return -np.expm1(-2.*elapsed/memory), np.exp(-elapsed/memory)


def fit_candidate(indices, values, law, memory):
    import numpy as np

    indices, values = np.asarray(indices, float), np.asarray(values, float)
    if (indices.ndim != 1 or len(indices) < 8 or values.shape != (len(indices), 6)
            or not np.isfinite(values).all()):
        raise ValueError('eight or more ordered six-channel donor means required')
    variance, retained = predictability(law, memory, np.diff(indices))
    mean = values.mean(axis=0)
    differences = values[1:]-mean-retained[:, None]*(values[:-1]-mean)
    white = differences/np.sqrt(variance[:, None])
    covariance = white.T@white/len(white)
    ridge = np.trace(covariance)*RIDGE_FRACTION/6
    if not ridge > 0.:
        raise ValueError('positive finite donor variance required')
    covariance += ridge*np.eye(6)
    loss = gaussian_loss(white, covariance)+3.*float(np.log(variance).sum())
    return dict(law=law, memory=memory, mean=mean.tolist(), covariance=covariance.tolist(),
                donor_transitions=len(white), negative_log_score=loss)


def forecast(model, previous, elapsed):
    import numpy as np

    variance, retained = predictability(model['law'], model['memory'], elapsed)
    prior = np.asarray(previous, float)
    mean = np.asarray(model['mean'], float)
    return mean+retained*(prior-mean), variance*np.asarray(model['covariance'], float)
