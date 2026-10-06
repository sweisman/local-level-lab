# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from lll.forward_reference import estimate_forward_axis, joint_covariance, matched_rows


def controlled_motion(seed=41, micro_corrections=False, course_noise=.1, heading_corrections=False):
    """Independent physical frames; no synthesize, science fit, or campaign seed."""
    dt = .1
    t = np.arange(0., 600., dt)
    bank = np.radians(12)*(np.exp(-((t-130)/25)**2)-np.exp(-((t-300)/35)**2)+np.exp(-((t-470)/28)**2))
    if micro_corrections:
        bank += np.radians(.3)*np.sin(2*np.pi*t/19)+np.radians(.2)*np.sin(2*np.pi*t/11.7)
    heading = np.cumsum(9.80665*np.tan(bank)/260)*dt
    mount = Rotation.from_euler('ZYX',[27.,4.,2.],degrees=True).as_matrix()
    fuselage_heading=heading.copy()
    if heading_corrections:
        # Independent body-yaw/sideslip stress: this is not a measured camera trace.
        fuselage_heading += np.radians(.4)*np.sin(2*np.pi*t/23)
        fuselage_heading += np.radians(2)*np.exp(-((t-220)/8)**2)
    frames = Rotation.from_euler('ZYX',np.column_stack([fuselage_heading,t*0,bank])).as_matrix()@mount
    gyro = Rotation.from_matrix(np.swapaxes(frames[:-1],1,2)@frames[1:]).as_rotvec()/dt
    gyro = np.vstack([gyro,gyro[-1]])
    rng = np.random.default_rng(seed)
    gyro += np.radians(.007)*np.sqrt(1/dt)*rng.normal(size=gyro.shape)
    # Slowly correlated transverse disturbance, independently prescribed.
    gyro += np.radians(.002)*np.sin(2*np.pi*t/75)[:,None]*(mount.T@[0.,1.,0.])
    gps_t = np.arange(1.,599.)
    bearing = np.degrees(np.interp(gps_t,t,heading))+rng.normal(0,course_noise,len(gps_t))
    return t,gyro,gps_t,np.full(len(gps_t),260.),bearing,mount.T@[0.,0.,-1.],mount.T@[1.,0.,0.]


@pytest.mark.parametrize('micro_corrections',[False,True])
def test_direction_and_covariance_under_independent_gps_imu_noise(micro_corrections):
    *args,known = controlled_motion(micro_corrections=micro_corrections)
    axis,q = estimate_forward_axis(*args)
    assert axis is not None
    assert np.dot(axis,known)>.999
    assert 0<q['angle_sigma_rad']<np.radians(5.)
    assert q['hac_lags']==60
    assert q['covariance_support_windows']>=4
    assert np.linalg.eigvalsh(q['regression_cov']).min()>-1e-12
    assert 'joint GPS/IMU' in q['uncertainty_method']
    assert q['coverage_status'].startswith('development')


def test_small_fixed_noise_panel_has_no_gross_uncertainty_underestimate():
    # Eight local software fixtures, not a flight campaign or a coverage claim.
    covered=0
    for seed in range(41,49):
        *args,known = controlled_motion(seed,micro_corrections=True)
        axis,q = estimate_forward_axis(*args)
        assert axis is not None
        up=args[-1]
        error=abs(np.arctan2(np.dot(up,np.cross(known,axis)),np.dot(known,axis)))
        covered += error<=3*q['angle_sigma_rad']
    assert covered>=7


def test_reference_tolerates_small_body_yaw_and_occasional_larger_view_shift():
    *args,known=controlled_motion(micro_corrections=True,heading_corrections=True)
    axis,q=estimate_forward_axis(*args)
    assert axis is not None
    assert np.dot(axis,known)>.999
    assert q['angle_sigma_rad']>0


def test_uncertainty_does_not_count_covariance_across_a_gap():
    x=np.ones(8)
    g=np.column_stack([x,np.r_[np.ones(4),-np.ones(4)],np.zeros(8)])
    coefficient=np.array([1.,0.,0.])
    together=joint_covariance(x,g,np.r_[np.zeros(4),np.ones(4)],coefficient,3)
    separate=sum(joint_covariance(x[s],g[s],np.zeros(4),coefficient,3)/4
                 for s in (slice(0,4),slice(4,8)))
    np.testing.assert_allclose(together,separate)
    assert together[1,1]>joint_covariance(x,g,np.zeros(8),coefficient,3)[1,1]


def test_reference_abstains_with_insufficient_covariance_duration():
    *args,_=controlled_motion()
    args[0],args[1]=args[0][:2000],args[1][:2000]
    args[2],args[3],args[4]=args[2][:190],args[3][:190],args[4][:190]
    axis,q=estimate_forward_axis(*args)
    assert axis is None
    assert 'covariance support' in q['reason']


def test_sparse_public_track_is_not_silently_a_frequent_gps_reference():
    *args,_=controlled_motion()
    args[2],args[3],args[4]=args[2][::30],args[3][::30],args[4][::30]
    rows,reason=matched_rows(*args)
    assert rows is None and 'frequent GPS' in reason


def test_no_roll_cannot_be_rescued_by_noisy_gps():
    *args,_=controlled_motion()
    args[1]=np.zeros_like(args[1])
    axis,q=estimate_forward_axis(*args)
    assert axis is None


def test_analyzer_refuses_matched_method_without_explicit_research_and_uncertainty():
    from lll.analyze import analyze
    with pytest.raises(ValueError,match='research candidate'):
        analyze('unused.zip',fit_options={'forward_reference':'matched'})


def test_science_engine_receives_measured_uncertainty_and_versioned_method(monkeypatch):
    from lll import inference
    from lll.fit import fit
    from test_release060 import crab_fixture
    bins,fwd=crab_fixture()
    class Captured(Exception): pass
    def capture(*args,**kwargs):
        assert kwargs['forward_sigma_rad']==.01
        assert kwargs['settings']['forward_reference']=='matched'
        assert kwargs['settings']['forward_reference_policy']['version']=='matched-forward-1'
        raise Captured
    monkeypatch.setattr(inference,'candidate_fit',capture)
    with pytest.raises(Captured):
        fit(bins,fwd,lambda t:np.zeros((len(t),3)),np.full(3,1e-5),n_boot=0,
            research_candidate=True,forward_uncertainty=True,forward_reference='matched',
            forward_sigma_rad=.01,forward_tangent=np.zeros_like(fwd))


def test_reference_uncertainty_is_rotation_invariant():
    *args,_=controlled_motion(micro_corrections=True)
    axis,q=estimate_forward_axis(*args)
    rotation=Rotation.from_euler('ZYX',[67.,18.,-34.],degrees=True).as_matrix()
    transformed=list(args)
    transformed[1]=args[1]@rotation.T
    transformed[-1]=rotation@args[-1]
    other,quality=estimate_forward_axis(*transformed)
    np.testing.assert_allclose(other,rotation@axis,atol=1e-12)
    assert quality['angle_sigma_rad']==pytest.approx(q['angle_sigma_rad'],rel=1e-10)
