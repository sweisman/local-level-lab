# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_solver_controls as controls
from lll import ilvis0_solver_screen as screen


@pytest.mark.parametrize('name',screen.NAMES)
@pytest.mark.parametrize('index',range(3))
def test_unit_scale_solver_recovers_known_optima_and_counts_every_call(name,index):
    from lll.ilvis0_solver_unit_scale import fit_candidate
    if name in controls.ANALYTIC:
        problem,optimum,expected,unique=controls.analytic_problem(name)
    else:
        problem,optimum=screen.mixed_problem(name); expected=1.; unique=False
    fit=fit_candidate(problem,'control',start=controls.starts(len(optimum),3)[index])
    point=np.array(fit['normalized_parameters'])
    assert fit['converged']
    assert abs(fit['residual_sum_squares']-expected)<=1e-7
    assert np.linalg.norm(problem.residual_tangent(point,'control')[0]-problem.residual_tangent(optimum,'reference')[0])<=1e-4
    if unique: assert max(abs(point-optimum))<=1e-5
    assert fit['evaluations']<=198
    assert len(fit['scaled_projected_gradient'])==len(optimum)
    assert len(fit['right_singular_vectors'])==len(optimum)
    assert fit['full_stage_x_scale']==1.
    if name in controls.ANALYTIC: assert problem.calls==fit['evaluations']+2


def test_staged_initialization_releases_all_parameters_and_budget_reserves_diagnostics():
    from lll.ilvis0_solver_unit_scale import fit_candidate
    class Problem:
        bounds=controls.ControlBounds(3)
        calls=0
        def residual_tangent(self,u,model):
            self.calls+=1
            return np.r_[u-[.2,-.3,.4],1.],np.vstack([np.eye(3),np.zeros((1,3))]),0
    p=Problem(); p.bounds.active=('attitude_x','accel_gain_y','gyro_bias_z')
    fit=fit_candidate(p,'control')
    assert fit['initialization_evaluations']>0
    assert fit['initialization_x_scale']=='jac'
    assert fit['converged'] and fit['residual_sum_squares']==pytest.approx(1.)
    assert np.allclose(fit['normalized_parameters'],[.2,-.3,.4])
    assert p.calls==fit['evaluations']<=198
    limited=Problem()
    short=fit_candidate(limited,'control',maximum_evaluations=4)
    assert not short['converged'] and limited.calls==short['evaluations']<=2
