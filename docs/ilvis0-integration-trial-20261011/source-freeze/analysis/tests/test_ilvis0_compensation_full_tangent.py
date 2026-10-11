# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full-column regression checks; no optimizer or observed-data starts."""
import numpy as np
import pytest

from lll import ilvis0_latitude_controls as controls
from lll import ilvis0_compensation as correction
from lll import ilvis0_estimator as estimator, ilvis0_shape as shape


@pytest.fixture(scope='module')
def kernel(tmp_path_factory):
    return correction.load_kernel(tmp_path_factory.mktemp('full-compensation-tangent'))[0]


@pytest.mark.parametrize('model,latitude',(('sphere_rotating',-45.),('sphere_still',45.),('flat_still',-45.)))
def test_all_archival_tangent_columns_match_separate_value_differences(model,latitude,kernel):
    f=controls.fixture(model,latitude,'near_roll')
    sigma=np.tile(.01/f['metric'],len(f['gps_times']))
    p=correction.CompensatedProblem(f['theta'],f['dv'],f['dt'],f['gps_times'],f['gps'],np.diag(sigma**2),
        f['initial'],estimator.Bounds(shape.instrument_limits(1.)),fit_earth_removal=True,
        kernel=None,tangent_kernel=kernel,mode='combined',convention='ordinary_rate_integrals',
        clock_hypothesis='header_elapsed',processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
    assert len(p.bounds.active)==27
    point=.03*np.sin(np.arange(27)+.4)
    _,jac,_=p.prediction_tangent(point,model)
    # Absolute geographic coordinates accumulate floating-point rounding. A
    # measured step sweep showed cancellation at 1e-4. Fourth-order symmetric
    # extrapolation permits a larger step without relaxing the accuracy check.
    step_size=1e-2
    for axis in range(27):
        step=np.eye(27)[axis]*step_size
        coarse=(p.predict(point+step,model)-p.predict(point-step,model)).ravel()/(2*step_size)
        fine=(p.predict(point+step/2,model)-p.predict(point-step/2,model)).ravel()/step_size
        finite=(4*fine-coarse)/3
        np.testing.assert_allclose(finite.reshape(-1,3)*f['metric'],jac[:,axis].reshape(-1,3)*f['metric'],
            rtol=2e-6,atol=2e-5,err_msg=p.bounds.active[axis])
