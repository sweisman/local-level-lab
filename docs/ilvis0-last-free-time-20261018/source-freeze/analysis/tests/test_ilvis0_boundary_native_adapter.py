# SPDX-License-Identifier: AGPL-3.0-or-later
"""Positive native callback checks at isolated, exactly bracketed packet edges."""
import numpy as np
import pytest
from test_ilvis0_boundary_adapter import motion_kernels


@pytest.mark.parametrize('latitude',[.3,.8])
def test_native_two_sided_gate_accepts_independent_exact_motion(motion_kernels,latitude,record_property):
    from lll import ilvis0_clock_brackets as clock,ilvis0_boundary_stop as stopping
    from lll import ilvis0_shape as shape,ilvis0_estimator as estimator,ilvis0_solver_position as position
    times=np.array([1.,2.+1e-8,3.+2e-8,4.+3e-8]);count=1000;scale=.15
    geometry=clock.bracket(times,count,scale,0.)
    assert geometry['side_geometry_supported']
    truth=geometry['point'];dt=np.full(count,.005);theta=np.zeros((count,3));dv=np.zeros_like(theta);dv[:,2]=-9.81*dt
    radius=6371000.;speed=250.
    gps=np.column_stack((latitude+speed*(times+scale*truth)/radius,np.full(4,.1),np.full(4,1000.)))
    initial=dict(latitude_rad=latitude,longitude_rad=.1,height_m=1000.,velocity_ned_mps=np.array([speed,0.,0.]),attitude_body_to_ned=np.eye(3))
    p=shape.TangentProblem(theta,dv,dt,times,gps,np.diag(np.tile([radius**-2,radius**-2,1.],4)),initial,
        estimator.Bounds({'time_offset':scale}),fit_earth_removal=False,kernel=motion_kernels[0],tangent_kernel=motion_kernels[1],
        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',maximum_interval_s=.0075,
        gravity_mps2=9.81,disc_radius_m=radius)
    calls=[]
    def evaluate(u,*,fresh=False):
        assert fresh;calls.append(1);return p.residual_tangent(u,'flat_still')
    result=stopping.check([truth],evaluate,lambda d:position.physical_residual_step(p,d),time_index=0,knots=geometry['knots'])
    record_property('native_evaluations',len(calls))
    assert result['passed'],result
    assert len(calls)==result['evaluations']<=10
