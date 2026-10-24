# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


@pytest.mark.parametrize('gyro,accel',[(.003,.02),(0.,.02),(.003,0.),(0.,0.)])
def test_level_whitening_matches_analytic_covariance_on_irregular_epochs(gyro,accel):
    import numpy as np
    from scipy.linalg import solve_triangular
    from lll.inertial_error_budget import level_position_covariance,level_innovations
    times=np.array([0.,.3,1.2,2.7,4.]);d=np.array([[.1,0.,0.],[.01,.2,0.],[.02,-.03,.3]])
    op=level_innovations(times,gyro_white=gyro,accel_white=accel,gravity=9.7,receiver_loading=d,maximum_bytes=1024*1024)
    covariance=np.zeros((3*len(times),3*len(times)))
    for i,t in enumerate(times):
        for j,u in enumerate(times):
            c=level_position_covariance(t,u,gyro_white=gyro,accel_white=accel,gravity=9.7)
            covariance[3*i:3*i+3,3*j:3*j+3]=np.diag([c['north_east_m2'],c['north_east_m2'],c['up_m2']])
            if i==j:covariance[3*i:3*i+3,3*j:3*j+3]+=d@d.T
    values=np.cos(np.arange(3*len(times)*27).reshape(3*len(times),27));lower=np.linalg.cholesky(covariance)
    np.testing.assert_allclose(op.whiten(values),solve_triangular(lower,values,lower=True),rtol=2e-11,atol=2e-11)
    assert op.log_determinant==pytest.approx(2*np.log(np.diag(lower)).sum(),abs=2e-11)


def test_level_long_operator_storage_is_linear_without_a_dense_covariance():
    import numpy as np
    from lll.inertial_error_budget import level_innovations
    count=64080;times=np.arange(1,count+1,dtype=float)*.5
    op=level_innovations(times,gyro_white=1e-5,accel_white=2e-4,gravity=9.80665,
        receiver_loading=np.diag([.1,.1,.2]),maximum_bytes=128*1024*1024)
    assert op.storage_bytes==count*(8*8+2*8*3+3*3)*8
    assert op.storage_bytes<128*1024*1024 and op.epoch_count==count
    result=op.whiten(np.zeros(3*count))
    assert result.shape==(3*count,) and np.array_equal(result,np.zeros_like(result))
    assert op.error_law_calibrated is False and op.parameter_uncertainty_included is False
