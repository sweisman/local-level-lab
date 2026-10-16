# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact independent motion targets qualify stopping under wider arithmetic."""
import numpy as np
import pytest

from lll import ilvis0_precision as precision, ilvis0_shape as shape
from lll import ilvis0_exploratory as explore, ilvis0_estimator as estimator
from lll import ilvis0_solver_position as solver


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    directory=tmp_path_factory.mktemp('precision-solver-controls')
    return explore.load_kernel(directory)[0],precision.load_tangent(directory)[0]


def straight_problem(kernels,truth):
    # Exact zero-net-force, constant north velocity on the declared disc metric.
    # Receiver positions come from the analytic trajectory, not either kernel.
    count=802;theta=np.zeros((count,3));dv=np.zeros_like(theta);dt=np.full(count,.005)
    dv[:,2]=-9.81*dt
    times=np.arange(.5,4.01,.5);radius=6371000.
    initial=dict(latitude_rad=.8,longitude_rad=.1,height_m=1000.,
                 velocity_ned_mps=np.array([250.,0.,0.]),attitude_body_to_ned=np.eye(3))
    # Bounds orders velocity before position; the analytic target is independent
    # of the prediction implementation but uses those explicit parameter units.
    gps=np.column_stack((.8+(5*truth[1]+(250+.5*truth[0])*times)/radius,
                         np.full(len(times),.1),np.full(len(times),1000.)))
    covariance=np.diag(np.tile([radius**-2,radius**-2,1.],len(times)))
    return shape.TangentProblem(theta,dv,dt,times,gps,covariance,initial,
        estimator.Bounds(dict(position_x=5.,velocity_x=.5)),fit_earth_removal=False,
        kernel=kernels[0],tangent_kernel=kernels[1],clock_hypothesis='nominal_200Hz',
        processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=radius)


@pytest.mark.parametrize('truth',[(.15,-.2),(.98,-.98),(1.,-1.)])
@pytest.mark.parametrize('start',[(0.,0.),(-.7,.6)])
def test_known_interior_near_boundary_and_exact_boundary_optima(kernels,truth,start):
    problem=straight_problem(kernels,truth)
    result=solver.fit_candidate(problem,'flat_still',start=np.array(start),maximum_evaluations=40)
    assert result['converged']
    np.testing.assert_allclose(result['normalized_parameters'],truth,atol=2e-6,rtol=0)
    assert result['residual_sum_squares']<1e-10
    assert result['evaluations']<=40
    assert result['scientific_decision']=='abstain'
    assert not result['scientific_eligible']
