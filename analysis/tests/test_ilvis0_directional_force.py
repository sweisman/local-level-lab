# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from lll.ilvis0_directional_force import calibrated_force,action


def test_increment_conversion_and_calibration_keep_signed_axes():
    lo,hi=calibrated_force([F(1,10),F(-1,5),F(-49,500)],F(1,100),
        [[0,0]]*3,[[0,0]]*3)
    assert lo==hi==[F(10),F(-20),F(-49,5)]


def test_calibration_extrema_cover_all_bias_and_gain_corners():
    raw=[.1,-.2,-.098];dt=.01;bias=[[-.02,.03]]*3;gain=[[-.01,.015]]*3
    lo,hi=calibrated_force(raw,dt,bias,gain)
    for j in range(3):
        exact=[(F(raw[j])-F(dt)*F(b))/(1+F(g))/F(dt) for b in bias[j] for g in gain[j]]
        assert lo[j]==min(exact) and hi[j]==max(exact)


def test_pure_yaw_preserves_vertical_force_and_sign_exactly():
    result=action([0,0,-100],[0,0,100],[-.02,-.03,F(-49,5)],[.02,.03,F(-49,5)])
    assert F(result['lower'][2])==F(result['upper'][2])==F(-49,5)


def test_zero_force_is_exactly_zero_for_arbitrary_rotation():
    result=action([-100]*3,[100]*3,[0]*3,[0]*3)
    assert result['lower']==result['upper']==['0']*3


def test_known_installation_is_applied_without_normalizing_it():
    matrix=[[0,0,2],[1,0,0],[0,-1,0]]
    result=action([0]*3,[0]*3,[1,2,3],[1,2,3],installation=matrix)
    assert list(map(F,result['lower']))==list(map(F,result['upper']))==[6,1,-2]


@pytest.mark.parametrize('seed',[0,1,2])
def test_independent_rotations_cover_force_boxes_and_installation(seed):
    rng=np.random.default_rng(661+seed)
    lower=np.array([-.02,-.03,-1.8]);upper=np.array([.04,.01,2.2])
    flo=np.array([-.05,-.04,-9.85]);fhi=np.array([.08,.07,-9.75])
    matrix=Rotation.from_rotvec([.17,-.21,.83]).as_matrix()
    result=action(lower.tolist(),upper.tolist(),flo.tolist(),fhi.tolist(),installation=matrix.tolist())
    w=rng.uniform(lower,upper,size=(128,3));force=rng.uniform(flo,fhi,size=(128,3))
    actual=Rotation.from_rotvec(w).apply(force)@matrix.T
    assert np.all(actual>=np.array([float(F(v)) for v in result['lower']])-1e-13)
    assert np.all(actual<=np.array([float(F(v)) for v in result['upper']])+1e-13)


@pytest.mark.parametrize('change',['time','gain','bias_shape','nonfinite'])
def test_bad_calibration_input_rejected(change):
    raw=[0.,0.,-.1];dt=.01;bias=[[0,0]]*3;gain=[[0,0]]*3
    if change=='time':dt=0
    if change=='gain':gain=[[-1.1,-.9]]*3
    if change=='bias_shape':bias=[[0,0]]*2
    if change=='nonfinite':raw[0]=float('inf')
    with pytest.raises(ValueError):calibrated_force(raw,dt,bias,gain)


@pytest.mark.parametrize('change',['force_order','rotation_order','matrix','nonfinite'])
def test_bad_action_input_rejected(change):
    lo=[0]*3;hi=[0]*3;flo=[0]*3;fhi=[0]*3;matrix=np.eye(3).tolist()
    if change=='force_order':flo[0]=1
    if change=='rotation_order':lo[0]=1
    if change=='matrix':matrix=[[1,0]]*3
    if change=='nonfinite':matrix[0][0]=float('nan')
    with pytest.raises(ValueError):action(lo,hi,flo,fhi,installation=matrix)
