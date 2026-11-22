# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.covariance_component_support import information


def test_zero_exposure_cannot_identify_its_variance():
    report=information(dict(native=np.eye(3), drift=[[1.],[0.],[0.]], maneuver=np.zeros((3,1))))
    assert report['rank']==2
    assert report['profile_information']['maneuver']==0.
    assert report['profile_information']['drift']>0.


def test_duplicated_component_is_confounded_even_with_nonzero_exposure():
    report=information(dict(native=np.eye(2), drift=[[1.],[0.]], maneuver=[[2.],[0.]]))
    assert report['rank']==2
    assert report['profile_information']['drift']==pytest.approx(0.,abs=1e-15)
    assert report['profile_information']['maneuver']==pytest.approx(0.,abs=1e-15)


def test_independent_variances_match_analytic_information():
    report=information(dict(first=[[1.],[0.]], second=[[0.],[2.]]))
    np.testing.assert_allclose(report['fisher_matrix'], .5*np.eye(2))
