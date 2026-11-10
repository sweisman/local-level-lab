# SPDX-License-Identifier: AGPL-3.0-or-later
"""Endpoint-shared noise for trapezoidally integrated raw rate samples.

Point covariances have squared-rate units, not continuous white-rate PSD units.
No bandwidth, hardware specification, noise estimate or scientific measurement
is supplied or inferred. The incremental-data noise law remains separate.
"""
from functools import lru_cache


class LinearPointNoise:
    hidden_dimension = 12

    def __init__(self, *, gyro_point_covariance, accel_point_covariance,
                 gyro_bias_covariance, accel_bias_covariance,
                 gyro_bias_tau_s, accel_bias_tau_s):
        from .measurement_noise import _root, ou_moments
        self.roots = tuple(_root(a) for a in (gyro_point_covariance,
            accel_point_covariance, gyro_bias_covariance, accel_bias_covariance))
        self.taus = (gyro_bias_tau_s, accel_bias_tau_s)
        for tau in self.taus:
            ou_moments([.005], tau_s=tau)
        for root in self.roots:
            root.flags.writeable = False

    @lru_cache(maxsize=32)
    def at(self, dt):
        """Loading for increment6/endpoint12, endpoint decay and mean6×12.

        Hidden order is gyro bias3, acceleration bias3, gyro white point3,
        acceleration white point3. Both endpoint innovations contribute to the
        current interval and remain in its endpoint state for the next interval.
        """
        import numpy as np
        from .measurement_noise import ou_moments
        loading = np.zeros((18, 12)); rho = np.zeros(12); mean = np.zeros((6, 12))
        for i, tau in enumerate(self.taus):
            moments = {k: v[0] for k, v in ou_moments([dt], tau_s=tau).items()}
            sl = slice(3*i, 3*i+3); endpoint = slice(6+3*i, 9+3*i)
            white = slice(6+3*i, 9+3*i); white_endpoint = slice(12+3*i, 15+3*i)
            bias_root = self.roots[i+2]*np.sqrt(moments['state_variance'])
            loading[sl, sl] = bias_root*(dt/2)
            loading[endpoint, sl] = bias_root
            loading[sl, white] = self.roots[i]*(dt/2)
            loading[white_endpoint, white] = self.roots[i]
            rho[sl] = moments['rho']
            mean[sl, sl] = np.eye(3)*(dt/2)*(1+moments['rho'])
            mean[sl, white] = np.eye(3)*(dt/2)
        if not np.all(np.isfinite(loading)) or not np.all(np.isfinite(mean)):
            raise ValueError('unrepresentable linear-point error law')
        for value in (loading, rho, mean):
            value.flags.writeable = False
        return loading, rho, mean

    def initial_loading(self):
        import numpy as np
        loading = np.zeros((21, 12))
        for i in range(2):
            loading[9+3*i:12+3*i, 3*i:3*i+3] = self.roots[i+2]
            loading[15+3*i:18+3*i, 6+3*i:9+3*i] = self.roots[i]
        return loading
