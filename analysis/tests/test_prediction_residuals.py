# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent series controls for descriptive saved-prediction statistics."""
import math

import numpy as np
import pytest


def test_constant_error_has_no_invented_correlation_or_spectral_variance():
    from lll.prediction_residuals import section
    values=np.tile([1.,2.,3.],(128,1));result=section(np.arange(128.),values)
    assert result['epochs']==128 and result['units']=='m'
    for i,axis in enumerate(result['axes']):
        assert axis['distribution']['rms']==i+1
        assert axis['distribution']['centered_rms']==0.
        assert all(v['value'] is None for v in axis['autocorrelation'])
        assert axis['spectrum']['total_variance']==0.
    assert all(v is None for row in result['correlation'] for v in row)


def test_ramp_covariance_and_actual_time_differences_have_known_values():
    from lll.prediction_residuals import section
    t=np.arange(128.);values=np.column_stack([t,2*t,np.zeros(len(t))])
    result=section(t,values);variance=(128**2-1)/12
    assert np.array(result['covariance'])==pytest.approx(np.array([[variance,2*variance,0.],[2*variance,4*variance,0.],[0.,0.,0.]]))
    assert result['correlation'][0][1]==pytest.approx(1.)
    assert result['correlation'][0][2] is None
    differences=result['first_differences']
    assert differences['epochs']==127 and differences['units']=='m/s'
    assert [v['distribution']['mean'] for v in differences['axes']]==[1.,2.,0.]
    assert all(v['distribution']['centered_rms']==0. for v in differences['axes'])


def test_alternating_series_has_known_negative_lag_and_nyquist_variance():
    from lll.prediction_residuals import section
    t=np.arange(128.);x=np.array([(-1.)**i for i in range(128)])
    result=section(t,np.column_stack([x,-2*x,np.zeros(len(x))]))
    axis=result['axes'][0]
    assert axis['autocorrelation'][0]['value']==pytest.approx(-127/128)
    assert axis['autocorrelation'][0]['median_lag_s']==1.
    assert axis['spectrum']['bands']['shorter_than_10_s']==pytest.approx(1.)
    assert axis['spectrum']['total_variance']==pytest.approx(1.)
    assert result['correlation'][0][1]==pytest.approx(-1.)


def test_sinusoid_has_analytically_known_low_frequency_energy():
    from lll.prediction_residuals import section
    t=np.arange(128.);x=2*np.sin(2*np.pi*t/64)
    result=section(t,np.column_stack([x,x,np.zeros(len(t))]))
    spectrum=result['axes'][0]['spectrum']
    assert spectrum['bands']['longer_than_60_s']==pytest.approx(2.)
    assert spectrum['total_variance']==pytest.approx(2.)


@pytest.mark.parametrize('n',(127,128))
def test_one_sided_spectrum_preserves_parseval_for_odd_and_even_lengths(n):
    from lll.prediction_residuals import section
    t=np.arange(float(n));x=np.array([(7*i)%17-8 for i in range(n)],float)
    mean=math.fsum(x)/n;variance=math.fsum((float(v)-mean)**2 for v in x)/n
    result=section(t,np.column_stack([x,x,np.zeros(n)]))
    spectrum=result['axes'][0]['spectrum']
    assert spectrum['total_variance']==pytest.approx(variance,rel=2e-14)
    assert sum(spectrum['bands'].values())+spectrum['zero_frequency_variance']==pytest.approx(variance,rel=2e-14)


def test_irregular_cadence_is_retained_but_not_interpolated_for_a_spectrum():
    from lll.prediction_residuals import section
    t=np.arange(128.);t[65]+=.1;values=np.column_stack([2*t,np.zeros(len(t)),np.zeros(len(t))])
    original=values.copy();result=section(t,values)
    assert result['epochs']==128
    assert all(not axis['spectrum']['supported'] for axis in result['axes'])
    assert result['axes'][0]['autocorrelation'][0]['min_lag_s']==pytest.approx(.9)
    assert result['axes'][0]['autocorrelation'][0]['max_lag_s']==pytest.approx(1.1)
    assert result['first_differences']['axes'][0]['distribution']['mean']==pytest.approx(2.)
    np.testing.assert_array_equal(values,original)


def test_later_errors_do_not_change_training_statistics_or_source_arrays():
    from lll.prediction_residuals import summarize
    t=np.arange(128.);values=np.column_stack([t/10,np.sin(t),np.zeros(len(t))]);original=values.copy()
    t.setflags(write=False);values.setflags(write=False)
    first=summarize(t,values,training_epochs=64)
    changed=values.copy();changed[64:]+=100.
    second=summarize(t,changed,training_epochs=64)
    assert first['training']==second['training'] and first['prediction']!=second['prediction']
    np.testing.assert_array_equal(values,original)
    assert not first['forecasts_changed'] and not first['error_law_calibrated']
    assert first['effective_sample_size'] is None and first['scientific_decision']=='abstain'
    assert all(v['last_epoch']<64 if v['section']=='training' else v['first_epoch']>=64 for v in first['blocks'])
    assert sum(v['epochs'] for v in first['blocks'])==128


@pytest.mark.parametrize('kind',('nonfinite_error','nonfinite_time','duplicate','reverse','shape','overflow','split'))
def test_invalid_series_fail_without_clipping_or_repair(kind):
    from lll.prediction_residuals import summarize
    t=np.arange(128.);values=np.column_stack([t,t,t]);cut=64
    if kind=='nonfinite_error':values[3,1]=float('nan')
    if kind=='nonfinite_time':t[3]=float('nan')
    if kind=='duplicate':t[3]=t[2]
    if kind=='reverse':t=t[::-1]
    if kind=='shape':values=values[:,:2]
    if kind=='overflow':values[:]=1e200
    if kind=='split':cut=True
    with pytest.raises(ValueError):summarize(t,values,training_epochs=cut)
