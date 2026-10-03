# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

import truthgen


def geometric_truth(world):
    """ω_in for synth, from the independent geometric generator rather than lll.models. The
    sampled track is interpolated, so the generator can differentiate the local frame along it."""
    def fn(t, lat, lon, h):
        t, lat, lon, h = (np.atleast_1d(np.asarray(x, float)) for x in (t, lat, lon, h))
        if len(t) == 1:   # a stationary point (ground calibration)
            def traj(tt):
                tt = np.atleast_1d(tt)
                return np.full(tt.shape, lat[0]), np.full(tt.shape, lon[0]), np.full(tt.shape, h[0])
        else:
            def traj(tt):
                return np.interp(tt, t, lat), np.interp(tt, t, lon), np.interp(tt, t, h)
        w, _ = truthgen.truth(world, traj, t)
        return w
    return fn
