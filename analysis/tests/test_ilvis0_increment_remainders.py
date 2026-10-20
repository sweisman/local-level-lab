# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll import ilvis0_increment_remainders as bounds


def corrected(raw=(.1,-.2,.3),dt=.005,wide=.15):
    return bounds.calibrated_box(raw,dt,bias_center=[0.,0.,0.],gain_center=[0.,0.,0.],
        bias_lower=[-.02]*3,bias_upper=[.02]*3,gain_lower=[-wide]*3,gain_upper=[wide]*3)


def test_reciprocal_calibration_bound_contains_all_corners_and_signs():
    raw=np.array([.1,-.2,.3]);dt=.005;result=corrected()
    for number in range(64):
        signs=np.array([1. if number&(1<<i) else -1. for i in range(6)])
        b=.02*signs[:3];g=.15*signs[3:];actual=(raw-b*dt)/(1+g)
        linear=raw-b*dt-raw*g
        assert np.linalg.norm(actual-raw)<=result['change_radius']+1e-14
        assert np.linalg.norm(actual-linear)<=result['remainder_radius']+1e-14


def test_one_axis_rational_remainder_attains_analytic_bound():
    raw=np.array([.1,0.,0.]);dt=.5
    result=bounds.calibrated_box(raw,dt,bias_center=np.zeros(3),gain_center=np.zeros(3),
        bias_lower=[-.02,0.,0.],bias_upper=[.02,0.,0.],gain_lower=[-.15,0.,0.],gain_upper=[.15,0.,0.])
    actual=(.1+.02*dt)/.85;linear=.1+.02*dt+.1*.15
    np.testing.assert_allclose(result['remainder_radius'],actual-linear,rtol=1e-13)


def test_fixed_gain_makes_bias_correction_affine():
    result=bounds.calibrated_box([.1,-.2,.3],.005,bias_center=np.zeros(3),gain_center=np.zeros(3),
        bias_lower=[-.2]*3,bias_upper=[.2]*3,gain_lower=np.zeros(3),gain_upper=np.zeros(3))
    assert result['remainder_radius']==0.


@pytest.mark.parametrize('kind,c0,c1,c2',[('rotation',1.,1.,.5),('velocity',1.,.5,1/6),('position',.5,1/6,1/24)])
def test_packet_constants_and_joint_product_term(kind,c0,c1,c2):
    theta=dict(center=np.array([0.,0.,0.]),change_radius=.2,remainder_radius=.01)
    dv=dict(center=np.array([3.,4.,0.]),change_radius=.3,remainder_radius=.02)
    result=bounds.packet_bound(theta,dv,kind=kind)
    expected=c2*.2**2*5.+c1*.2*.3+c1*.01*5.+c0*.02
    np.testing.assert_allclose(result['remainder_radius'],expected,rtol=1e-14)


def test_no_uncertainty_preserves_zero_remainders_through_history():
    state=bounds.PreintegrationBounds()
    theta=dict(center=np.zeros(3),change_radius=0.,remainder_radius=0.)
    dv=dict(center=np.array([0.,0.,-.05]),change_radius=0.,remainder_radius=0.)
    for _ in range(7):state=state.advance(theta,dv,.005)
    assert state.rotation_change==state.rotation_remainder==state.velocity_remainder==state.position_remainder==0.
    assert state.samples==7 and state.position_center_norm>0.


def test_remainder_identity_never_claims_complete_native_coverage():
    state=bounds.PreintegrationBounds()
    assert state.report()['native_full_map_covered'] is False
    assert state.report()['floating_point_enclosure_verified'] is False


@pytest.mark.parametrize('kind',['denominator','center','time'])
def test_unsupported_calibration_domain_is_rejected(kind):
    args=dict(raw=[1.,2.,3.],dt=.005,bias_center=np.zeros(3),gain_center=np.zeros(3),
        bias_lower=[-.1]*3,bias_upper=[.1]*3,gain_lower=[-.2]*3,gain_upper=[.2]*3)
    if kind=='denominator':args['gain_lower']=[-1.,0.,0.]
    elif kind=='center':args['bias_center']=[1.,0.,0.]
    else:args['dt']=0.
    with pytest.raises(ValueError):bounds.calibrated_box(**args)
