# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def audit(times,values,**kwargs):
    from lll.ilvis0_residual_covariance import describe
    return describe(times,values,**kwargs)


def alternating():
    x=np.array([-1.,1.]*4)
    return np.arange(8)*.5,np.column_stack((x,2*x,np.full(8,5.)))


def test_covariance_centers_and_keeps_cross_axis_sign_and_zero_variance():
    t,x=alternating();out=audit(t,x,max_lag=2)
    np.testing.assert_allclose(out['covariance'],[[1,2,0],[2,4,0],[0,0,0]])
    assert out['correlation'][0][1]==1.
    assert out['correlation'][2]==[None,None,None]
    assert out['axes'][2]['mean']==5.
    north=out['lags'][1]
    assert north['pairs']==7 and north['median_lag_s']==.5
    assert north['correlation'][0][0]==pytest.approx(-.875)
    assert out['lags'][2]['correlation'][0][0]==pytest.approx(.75)


@pytest.mark.parametrize('n',[255,256])
def test_spectrum_has_physical_frequency_and_parseval_normalization(n):
    t=np.arange(n)*.5
    x=np.sin(2*np.pi*16*np.arange(n)/n)
    y=np.sin(2*np.pi*2*np.arange(n)/n)
    out=audit(t,np.column_stack((x,-2*x,y)),max_lag=2)
    spectrum=out['spectrum']
    freq=np.array(spectrum['frequencies_hz']);power=np.array(spectrum['density'])
    assert freq[np.argmax(power[:,0])]==pytest.approx(16/(n*.5))
    w=np.hanning(n);centered=x-x.mean()
    expected=np.dot(w*centered,w*centered)/np.dot(w,w)
    assert np.sum(power[:,0])*spectrum['resolution_hz']==pytest.approx(expected)
    assert out['correlation'][0][1]==pytest.approx(-1.)
    assert out['axes'][0]['period_ge_60s_power_fraction']<1e-7
    assert out['axes'][2]['period_ge_60s_power_fraction']>.8


def test_irregular_cadence_retains_actual_lags_and_does_not_compute_fft():
    t,x=alternating();t[4:]+=5
    out=audit(t,x,max_lag=2)
    assert out['spectrum'] is None
    assert out['spectral_status']=='irregular_cadence_not_resampled'
    assert out['lags'][1]['min_lag_s']==.5
    assert out['lags'][1]['max_lag_s']==5.5
    assert out['epochs']==8


def test_constant_series_has_no_invented_correlation_or_spectral_fraction():
    out=audit(np.arange(8),np.ones((8,3)))
    assert out['correlation']==[[None]*3]*3
    assert all(r['period_ge_60s_power_fraction'] is None for r in out['axes'])


@pytest.mark.parametrize('error',['reversal','duplicate','nonfinite','unaligned','short','negative_lag'])
def test_invalid_measurements_or_lag_policy_are_rejected(error):
    t,x=alternating();kwargs={}
    if error=='reversal':t[2]=-1.
    if error=='duplicate':t[2]=t[1]
    if error=='nonfinite':x[0,0]=np.nan
    if error=='unaligned':x=x[:-1]
    if error=='short':t=t[:2];x=x[:2]
    if error=='negative_lag':kwargs['max_lag']=-1
    with pytest.raises(ValueError):audit(t,x,**kwargs)
