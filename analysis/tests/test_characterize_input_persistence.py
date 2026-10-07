# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll.format import Session
import characterize_input_persistence as persistence


def test_raw_second_means_reject_interior_gaps_and_never_fill_missing_seconds():
    t=np.arange(0.,5.,.05);keep=~(((t>=1.3)&(t<1.55))|((t>=3)&(t<4)))
    ns=np.rint(t[keep]*1e9).astype(np.int64);stream=dict(t_ns=ns,x=np.ones(len(ns)))
    mean,count=persistence.second_means(stream,['x'],0,5_000_000_000,imu=True)
    assert mean[[0,2,4],0]==pytest.approx([1.,1.,1.])
    assert np.isnan(mean[[1,3],0]).all() and count[3]==0


def test_timestamp_offsets_are_averaged_on_same_clock_without_row_pairing():
    t=np.arange(0.,3.,.05);stream=dict(t_ns=np.rint((t+.002)*1e9).astype(np.int64),x=2*t)
    mean,count=persistence.second_means(stream,['x'],0,3_000_000_000,imu=True)
    assert count.tolist()==[20,20,20]
    assert mean[:,0]==pytest.approx([.95,2.95,4.95])


def test_known_cross_correlation_and_lag_pairs_do_not_bridge_missing_second():
    x=np.arange(15.,dtype=float);values=np.column_stack([x,2*x]);values[7]=np.nan
    result=persistence.describe(values,['a','b']);constant=result['treatments']['constant_mean_removed']
    lags={lag['lag_seconds']:lag for lag in constant['lags']}
    assert result['contiguous_run_seconds']==[7,7]
    assert lags[1]['within_run_pairs']==12 and lags[5]['within_run_pairs']==4 and lags[15]['within_run_pairs']==0
    assert np.asarray(lags[0]['cross_correlation'])==pytest.approx(np.ones((2,2)))
    centered=values[np.isfinite(values).all(axis=1)];centered-=centered.mean(axis=0)
    assert constant['second_mean_covariance']==pytest.approx(centered.T@centered/len(centered))
    assert np.max(result['treatments']['linear_trend_removed']['second_mean_standard_deviation'])<1e-12


def test_averaging_variance_matches_direct_nonoverlapping_means():
    values=np.sin(np.arange(900.)*.15)[:,None]
    report=persistence.describe(values,['a'])['treatments']['constant_mean_removed']
    blocks=next(b for b in report['averaging'] if b['window_seconds']==300)
    assert blocks['complete_nonoverlapping_blocks']==3
    assert blocks['standard_deviation_of_block_means'][0]==pytest.approx(values.reshape(3,300).mean(axis=1).std(ddof=1))


def test_zero_variance_and_insufficient_data_are_not_fake_zero_uncertainty():
    report=persistence.describe(np.ones((400,2)),['a','b'])
    lag=report['treatments']['constant_mean_removed']['lags'][0]
    assert lag['autocorrelation']==[None,None]
    assert persistence.describe(np.array([[1.],[np.nan]]),['a'])['status']=='insufficient'


def test_flight_markers_cannot_be_used_as_still_controls():
    session=Session(dict(phases=[dict(name='flight',start_ns=0,end_ns=1_000_000_000)]),{})
    with pytest.raises(ValueError,match='still phases'):persistence.characterize(session)


def test_absent_gps_is_reported_and_no_recording_is_certified():
    t=np.arange(0.,6.,.05);ns=np.rint(t*1e9).astype(np.int64)
    gyro=dict(t_ns=ns,x=np.sin(t)*1e-5,y=np.cos(t)*1e-5,z=np.sin(t/2)*1e-5)
    force=dict(t_ns=ns,x=np.sin(t)*.001,y=np.cos(t)*.001,z=np.full(len(t),9.8))
    session=Session(dict(phases=[dict(name='bench',start_ns=0,end_ns=6_000_000_000)]),dict(gyro=gyro,accel=force))
    result=persistence.characterize(session)
    assert result['phases'][0]['gps'] is None
    assert result['phases'][0]['imu']['observed_complete_seconds']==6
    assert result['decisions_enabled'] is False


def test_gps_gaps_and_longitude_wrap_preserve_later_observations():
    t=np.arange(0.,6.,.05);ns=np.rint(t*1e9).astype(np.int64)
    stream=dict(t_ns=ns,x=np.sin(t)*.001,y=np.cos(t)*.001,z=np.ones(len(t)))
    gns=np.arange(6,dtype=np.int64)*1_000_000_000+500_000_000
    gps=dict(t_ns=gns,speed_mps=np.full(6,.1),bearing_deg=np.arange(6)*10.,alt_m=np.arange(6.),lat=np.ones(6)*20.,
        lon=np.array([179.9999,-179.9999,np.nan,179.9998,-179.9998,179.9999]),
        h_acc_m=np.ones(6),v_acc_m=np.ones(6),speed_acc_mps=np.ones(6),bearing_acc_deg=np.ones(6))
    gps['h_acc_m'][:4]=np.inf
    session=Session(dict(phases=[dict(name='bench',start_ns=0,end_ns=6_000_000_000)]),dict(gyro=stream,accel=stream,gnss=gps))
    phase=persistence.characterize(session)['phases'][0]
    assert phase['gps']['observed_complete_seconds']==5
    assert phase['gps_imu_joint']['observed_complete_seconds']==5
    assert phase['gps']['contiguous_run_seconds']==[2,3]
    assert phase['gps']['treatments']['constant_mean_removed']['second_mean_standard_deviation'][-1]<1e-5
    assert phase['gps_accuracy_fields']['h_acc_m']==dict(finite_samples=2,median=1.)


def test_saturated_second_is_not_noise_characterization_data():
    t=np.arange(0.,3.,.05);sat=np.zeros(len(t),bool);sat[25]=True
    stream=dict(t_ns=np.rint(t*1e9).astype(np.int64),x=np.ones(len(t)),sat=sat)
    mean,_=persistence.second_means(stream,['x'],0,3_000_000_000,imu=True)
    assert np.isfinite(mean[[0,2]]).all() and np.isnan(mean[1]).all()
