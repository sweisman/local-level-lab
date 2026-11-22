# SPDX-License-Identifier: AGPL-3.0-or-later
"""Time-weighted calibrated accelerometer magnitudes on whole packets."""

import numpy as np


class PacketMeans:
    """Share one physical gain and bias per axis over all packet windows."""

    def __init__(self, increments_mps, durations_s, windows):
        increments = np.asarray(increments_mps, float)
        durations = np.asarray(durations_s, float)
        windows = np.asarray(windows)
        if (increments.ndim != 2 or increments.shape[1] != 3 or not len(increments)
                or durations.shape != (len(increments),) or not np.isfinite(increments).all()
                or not np.isfinite(durations).all() or np.any(durations <= 0.)):
            raise ValueError('finite three-axis increments and positive packet durations required')
        if (windows.ndim != 2 or windows.shape[1] != 2 or not len(windows)
                or not np.issubdtype(windows.dtype, np.integer) or np.any(windows[:, 0] < 0)
                or np.any(windows[:, 1] > len(increments)) or np.any(windows[:, 0] >= windows[:, 1])):
            raise ValueError('each window must have valid integer start and stop packet indices')
        self.increments = increments.copy()
        self.durations = durations.copy()
        self.starts, self.stops = windows.T.copy()
        elapsed = np.r_[0., np.cumsum(durations, dtype=np.longdouble)]
        self.window_durations = elapsed[self.stops] - elapsed[self.starts]

    def value_jacobian(self, calibration):
        """Return N window means and their six physical-parameter derivatives."""
        point = np.asarray(calibration, float)
        if point.shape != (6,) or not np.isfinite(point).all() or np.any(point[:3] <= -1.):
            raise ValueError('finite gains greater than minus one and finite biases required')
        denominator = 1. + point[:3]
        corrected = (self.increments - self.durations[:, None]*point[3:]) / denominator
        magnitude = np.linalg.norm(corrected, axis=1)
        if not np.isfinite(magnitude).all() or np.any(magnitude <= np.finfo(float).tiny):
            raise ValueError('finite nonzero calibrated magnitudes required for derivatives')
        direction = corrected / magnitude[:, None]
        derivatives = np.column_stack((-direction*corrected/denominator,
                                       -direction*self.durations[:, None]/denominator))
        contributions = np.column_stack((magnitude, derivatives))
        # Wider prefix sums limit cancellation when a short window comes late in a recording.
        prefix = np.vstack((np.zeros((1, 7)), np.cumsum(contributions, axis=0, dtype=np.longdouble)))
        totals = (prefix[self.stops] - prefix[self.starts]) / self.window_durations[:, None]
        return np.asarray(totals[:, 0], float), np.asarray(totals[:, 1:], float)
