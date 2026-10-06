# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent projection/derivative checks; no simulated flight or nonlinear fit."""
import numpy as np
import pytest

from lll.inference import CandidateProblem, science_information
from lll.calib import RAD2DPH
from test_release060 import crab_fixture
from test_research_candidates import settings


@pytest.mark.parametrize('scale', [1e-200, 1e-16, 1., 1e16, 1e200])
def test_nuisance_units_cannot_create_identifiable_science(scale):
    J = np.zeros((6, 6))
    J[:3, :3] = np.eye(3)
    J[0, 3] = 1.
    J[1, 4] = scale
    # A zero nuisance column must not count as an extra direction.
    info = science_information(J, np.array([2., 3., 4., 1., 1., 1.]))
    assert info['report']['estimable_rank'] == 1
    assert info['report']['nuisance_projection']['rank'] == 2
    np.testing.assert_allclose(info['effective'][:2], 0., atol=1e-12)
    np.testing.assert_allclose(info['fisher'], np.diag([0., 0., 4.]), atol=1e-12)


def test_cutoff_reports_information_it_discards_without_relaxing_gate():
    # An independent weak science direction survives nuisance projection, but the
    # preregistered science cutoff must still exclude it.
    J = np.zeros((5, 4))
    J[0, 0], J[1, 1], J[2, 2], J[3, 1] = 1., 1., 1., .2
    J[1, 3] = 1.
    report = science_information(J, np.ones(5))['report']
    pair = report['model_contrast_information']['sphere_still_vs_flat_still']
    assert report['estimable_rank'] == 2
    assert pair['pre_cutoff_information'] > pair['information']
    assert pair['pre_cutoff_retained_fraction'] > pair['retained_fraction']


@pytest.mark.parametrize('anchor', [[1., 1., 0.], [0., 1., 0.], [0., 0., 1.]])
def test_wind_tangent_matches_finite_differences_at_model_anchors(anchor):
    bins, fwd = crab_fixture()
    problem = CandidateProblem(bins, fwd, lambda _: 0., np.full(3, 2/RAD2DPH),
        settings(crab_model='wind', bias_model='dynamic', forward_uncertainty=True),
        forward_sigma_rad=.02)
    z = np.zeros(problem.npar)
    z[:3] = anchor
    _, jacobian = problem.prediction(z, True)
    for index in range(problem.p, problem.npar):
        plus, minus = z.copy(), z.copy()
        plus[index] += 1e-6
        minus[index] -= 1e-6
        np.testing.assert_allclose(jacobian[:, index],
            (problem.prediction(plus)-problem.prediction(minus))/(2e-6), atol=1e-12, rtol=2e-5)
