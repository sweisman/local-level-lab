# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
from decimal import Decimal,localcontext
import numpy as np
import pytest


def options(**changes):
    from lll.ilvis0_error_model import Spec
    value=dict(receiver=Spec(np.eye(3)),origin_s=0.,accel_psd=np.zeros((3,3)),
        gyro_psd=np.zeros((3,3)),coupling=np.eye(3),clock_interval_s=[0.,0.])
    value.update(changes);return value


def test_exact_signed_acceleration_and_gyro_summary_variances():
    from lll.ilvis0_joint_variance_bounds import projected_variance_bounds
    weights=[[1.,0.,0.,-1.,0.,0.]]
    acceleration=projected_variance_bounds([1.,2.],weights,**options(accel_psd=np.eye(3)))
    gyro=projected_variance_bounds([1.,2.],weights,**options(gyro_psd=np.eye(3)))
    assert F(acceleration['exact_variance_upper_m2'][0])==F(10,3)
    assert F(gyro['exact_variance_upper_m2'][0])==F(47,15)
    assert F(float(acceleration['variance_upper_m2'][0]))>=F(10,3)


def test_common_clock_adds_noise_prefix_and_keeps_drift_origin():
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_joint_variance_bounds import projected_variance_bounds
    weights=[[1.,0.,0.,-1.,0.,0.]]
    value=projected_variance_bounds([1.,2.],weights,
        **options(accel_psd=np.eye(3),clock_interval_s=[-1.,1.]))
    assert F(value['exact_variance_upper_m2'][0])==F(13,3)
    drift=projected_variance_bounds([1.,2.],weights,
        **options(receiver=Spec(np.eye(3),offset=np.eye(3)*17,drift=np.eye(3)),clock_interval_s=[-1.,1.]))
    assert F(drift['exact_variance_upper_m2'][0])==3  # shared offset cancels; drift does not


def test_correlated_receiver_summary_retains_signed_cancellation():
    from lll.ilvis0_error_model import Spec
    from lll.ilvis0_joint_variance_bounds import projected_variance_bounds,marginal_variance_bounds
    settings=options(receiver=Spec(np.eye(3),components=((10.,np.eye(3)),)),clock_interval_s=[-1.,1.])
    value=projected_variance_bounds([1.,2.],[[1.,0.,0.,-1.,0.,0.]],**settings)
    upper=F(value['exact_variance_upper_m2'][0])
    with localcontext() as context:
        context.prec=80;expected=Decimal(4)-2*(Decimal(-1)/10).exp()
        actual=Decimal(upper.numerator)/Decimal(upper.denominator)
        assert actual>=expected and actual-expected<Decimal('1e-12')
    assert value['covariance_id']==marginal_variance_bounds([1.,2.],**settings)['covariance_id']
    assert len(value['projection_id'])==64 and not value['law_adequacy_established']


def test_projection_variance_bounds_cover_independent_dense_reference_and_clock():
    from test_ilvis0_joint_error_operator import receiver,settings
    from lll.ilvis0_inertial_error import joint_covariance
    from lll.ilvis0_joint_variance_bounds import projected_variance_bounds
    times=np.array([2.,10.,30.,180.,290.]);weights=np.random.default_rng(7).normal(size=(4,15))
    args=dict(receiver=receiver(),**settings(),clock_interval_s=[-.75,.75])
    result=projected_variance_bounds(times,weights,**args)
    for shift in (-.75,0.,.3,.75):
        covariance=joint_covariance(times+shift,args['receiver'],**settings())
        expected=np.diag(weights@covariance@weights.T)
        assert np.all(result['variance_upper_m2']>=expected-1e-8)
    assert result['clock_interval_covered'] and not result['variance_upper_m2'].flags.writeable


@pytest.mark.parametrize('weights',[[],[1.,2.,3.],[[np.nan,0.,0.]],[[1.,2.]]])
def test_projection_variance_rejects_incomplete_or_nonfinite_rows(weights):
    from lll.ilvis0_joint_variance_bounds import projected_variance_bounds
    with pytest.raises(ValueError):projected_variance_bounds([2.],weights,**options())
