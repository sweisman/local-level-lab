# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generation and scoring of positive shared-plus-receiver covariances."""

from dataclasses import dataclass
import math


SCALES = (1/16, 1/8, 1/4, 1/2, 1., 2., 4., 8.)


@dataclass(frozen=True)
class Marginal:
    eigenvalues: object
    projected_error: object
    logdet_template: float

    def score(self, scale):
        import numpy as np

        if scale <= 0. or not math.isfinite(scale):
            raise ValueError('positive finite common covariance multiplier required')
        values = scale+self.eigenvalues
        dimension = len(values)
        logdet = self.logdet_template+float(np.log(values).sum())
        quadratic = float(np.sum(self.projected_error**2/values))
        return dict(logdet=logdet, quadratic=quadratic,
                    negative_log_score=.5*(logdet+quadratic+dimension*math.log(2.*math.pi)))


def additive_spectrum(residual, receiver, logdet):
    """Diagonalize the receiver root after whitening the shared template."""
    import numpy as np
    from scipy.linalg import svd

    residual, receiver = np.asarray(residual, float), np.asarray(receiver, float)
    dimension = len(residual)
    if (residual.shape != (dimension,) or receiver.ndim != 2 or receiver.shape[0] != dimension
            or not np.isfinite(residual).all() or not np.isfinite(receiver).all() or not math.isfinite(logdet)):
        raise ValueError('finite matched residual and receiver root required')
    axes, singular, _ = svd(receiver, full_matrices=True)
    eigenvalues = np.zeros(dimension)
    eigenvalues[:len(singular)] = singular**2
    return Marginal(eigenvalues, axes.T@residual, logdet)


def select_scale(donors, *, reserve):
    if len(donors) != 18:
        raise ValueError('exactly 18 donor marginals required')
    candidates = []
    for scale in SCALES:
        reserve()
        loss = math.fsum(item.score(scale)['negative_log_score'] for item in donors)
        candidates.append(dict(scale=scale, negative_log_score=loss))
    best = min(candidates, key=lambda item: (item['negative_log_score'], item['scale']))
    return dict(**best, candidates=candidates)
