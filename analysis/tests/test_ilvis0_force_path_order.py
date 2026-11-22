# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.ilvis0_force_path_order import coordinate_boxes, fit_path, point_jet
from lll.ilvis0_force_support_average import bound_average
from lll.ilvis0_force_path_order import mean_bounds


def test_quartic_path_recovers_known_first_two_derivatives_and_encloses_them():
    time = np.arange(-5., 6.)
    shape = time**4 - .6*time**3 + 2.*time**2 + .25*time
    coordinates = np.column_stack((np.full(len(time), .4), 1.1+2e-5*time, 1200.+shape))
    coefficients = fit_path(time, coordinates, degree=4)
    left, right = -.7, 1.3
    bounds = coordinate_boxes(coefficients, left, right)
    for t in np.linspace(left, right, 41):
        jet = point_jet(coefficients, t)
        np.testing.assert_allclose(jet[:, 2],
            [1200.+t**4-.6*t**3+2.*t**2+.25*t, 4.*t**3-1.8*t**2+4.*t+.25,
             12.*t**2-3.6*t+4.], atol=2e-11, rtol=0)
        assert np.all(bounds[:, 0] <= jet.ravel()) and np.all(jet.ravel() <= bounds[:, 1])


def test_general_force_enclosure_matches_quadratic_control():
    jet = np.array([[.4, -.8, 1400.], [3e-5, 1.2e-5, -.15], [2e-9, 1e-9, 1e-4]])
    coefficients = jet/np.array([1., 1., 2.])[:, None]
    settings = dict(model='sphere_still', background_rate_rads=0., gravity_mps2=9.80665,
                    disc_radius_m=6371000.)
    old = bound_average(jet, (-5., 5.), subdivisions=8, offset_bounds_s=(-.15,.15), **settings)
    new = mean_bounds(coefficients, (-5.,5.), subdivisions=8, offset=.15, **settings)
    np.testing.assert_allclose(old, new, atol=1.2e-5, rtol=0)
