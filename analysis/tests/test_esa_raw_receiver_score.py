# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_carrier_satellite_influence import leave_one_out
from lll.esa_raw_receiver_score import centered_geometry, fit_displacements


def test_recovers_position_geometry_and_refits_satellite_subset():
    xyz = np.random.default_rng(72).normal(size=(9, 3))
    geometry = xyz/np.linalg.norm(xyz, axis=1)[:, None]
    design = np.c_[geometry, np.ones(len(geometry))]
    correction, withheld, _ = leave_one_out(design, np.linspace(-1, 1, len(design))**2)
    saved = dict(satellites=list(range(1, 10)), correction_ecef_m=correction[:, :3],
                withheld_range_error_m=withheld)
    recovered = centered_geometry(saved)
    np.testing.assert_allclose(recovered, geometry-geometry.mean(axis=0), atol=1e-13)
    keep = [0, 2, 3, 6, 8]
    delta = np.array([.31, -.04, .09])
    error = geometry[keep] @ delta + 300.
    result, _ = fit_displacements(recovered[keep], np.c_[error, 2*error, error])
    np.testing.assert_allclose(result, [delta, 2*delta, delta], atol=1e-12)
