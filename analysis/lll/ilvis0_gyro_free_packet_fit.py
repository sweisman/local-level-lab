# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare calibrated packet magnitudes with time-averaged required forces."""

import numpy as np
from scipy.linalg import solve_triangular

from .ilvis0_packet_force_calibration import PacketMeans


def continuous_gap_upper(durations_s, change_rate_mps3, packet_magnitude_lower_mps2):
    """Bound the convexity gap using a supplied body-frame Lipschitz limit."""
    duration, rate, lower = np.broadcast_arrays(durations_s, change_rate_mps3, packet_magnitude_lower_mps2)
    duration, rate, lower = (np.asarray(value, float) for value in (duration, rate, lower))
    if (any(not np.isfinite(v).all() for v in (duration, rate, lower)) or np.any(duration <= 0.)
            or np.any(rate < 0.) or np.any(lower < 0.)):
        raise ValueError('positive duration and finite nonnegative rate and magnitude bounds required')
    upper = lambda value: np.nextafter(value, np.inf)
    with np.errstate(over='ignore'):
        radius = upper(upper(duration*rate)/np.nextafter(np.sqrt(12.), 0.))
        ratio = upper(np.divide(radius, lower, out=np.full_like(radius, np.inf), where=lower > 0.))
        refined = upper(upper(radius/2.)*ratio)
    if not np.isfinite(radius).all():
        raise ValueError('body-frame packet motion bound exceeded numerical range')
    return np.where(rate == 0., 0., np.minimum(radius, refined))


class PacketForceProblem:
    """Keep one calibration and one declared covariance on the same windows."""

    def __init__(self, packets, required_force, weights, limits, covariance):
        if not isinstance(packets, PacketMeans):
            raise ValueError('whole-packet accelerometer windows are required')
        count = len(packets.starts)
        force, weights, limits, covariance = (np.asarray(value, float)
            for value in (required_force, weights, limits, covariance))
        if (weights.ndim != 1 or not len(weights) or force.shape != (count, len(weights), 3)
                or not np.isfinite(force).all() or not np.isfinite(weights).all()
                or np.any(weights <= 0.) or not np.isclose(weights.sum(), 1., rtol=1e-14, atol=0.)):
            raise ValueError('finite aligned force nodes and positive normalized quadrature weights required')
        if (limits.shape != (7,) or not np.isfinite(limits).all() or np.any(limits <= 0.)
                or np.any(limits[:3] >= 1.)):
            raise ValueError('seven positive bounds with gains below one required')
        if (covariance.shape != (count, count) or not np.isfinite(covariance).all()
                or not np.allclose(covariance, covariance.T, rtol=1e-12, atol=0.)):
            raise ValueError('finite symmetric force covariance required')
        try:
            self.cholesky = np.linalg.cholesky(covariance)
        except np.linalg.LinAlgError as error:
            raise ValueError('positive definite force covariance required') from error
        self.packets = packets
        self.force = force.copy()
        self.weights = weights/weights.sum()
        self.limits = limits.copy()

    def _evaluate(self, point):
        point = np.asarray(point, float)
        if point.shape != (7,) or not np.isfinite(point).all() or np.any(abs(point) > 1.):
            raise ValueError('seven finite normalized coordinates within the bounds required')
        physical = point*self.limits
        measured, jacobian = self.packets.value_jacobian(physical[:6])
        target = self.force.copy()
        target[..., 2] -= physical[6]
        magnitudes = np.linalg.norm(target, axis=-1)
        if not np.isfinite(magnitudes).all() or np.any(magnitudes <= np.finfo(float).tiny):
            raise ValueError('nonzero required force at every quadrature node is required')
        residual = measured - magnitudes @ self.weights
        gravity_derivative = (target[..., 2]/magnitudes) @ self.weights
        return residual, np.column_stack((jacobian, gravity_derivative))*self.limits

    def raw_residual(self, point):
        return self._evaluate(point)[0]

    def residual(self, point):
        return solve_triangular(self.cholesky, self.raw_residual(point), lower=True)

    def jacobian(self, point):
        return solve_triangular(self.cholesky, self._evaluate(point)[1], lower=True)
