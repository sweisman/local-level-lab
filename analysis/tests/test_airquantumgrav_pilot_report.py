# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import io

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_pilot_report') is not None,'saved pilot preparation verifier missing'
    return importlib.import_module('lll.airquantumgrav_pilot_report')


def material():
    t=1000.+np.arange(101)*.003;dt=np.diff(t);w=np.tile([.1,.2,.3],(101,1));f=np.tile([1.,2.,3.],(101,1))
    arrays=dict(raw_time_s=t,acceleration_mps2=f,angular_rate_rads=w,temperature_c=np.full(101,20.),
        line_number=np.arange(2,103,dtype=np.int64),theta=(w[:-1]+w[1:])/2*dt[:,None],
        dv=(f[:-1]+f[1:])/2*dt[:,None],dt=dt)
    layout=dict(times_s=[.06,.09,.12,.15,.18,.21],time_origin_gps_sow_s=1000.,
        maximum_latency_s=.01,maximum_interval_s=.005,sampling_hypothesis='linear_points',
        constructed_not_logged_increments=True,training_epochs=4,prediction_epochs=2)
    result=dict(raw_points=101,constructed_intervals=100,query_epochs=6,training_epochs=4,prediction_epochs=2)
    return arrays,layout,result


def packed(arrays):
    buffer=io.BytesIO();np.savez_compressed(buffer,**arrays);return buffer.getvalue()


def test_saved_raw_interval_reconciles_actual_times_and_unmodified_rate_units():
    arrays,layout,result=material()
    report=library().validate_interval(packed(arrays),layout,result)
    assert report['raw_points']==101 and report['constructed_intervals']==100
    assert report['minimum_dt_s']>0 and report['maximum_dt_s']<.005
    assert report['constructed_not_logged_increments']


@pytest.mark.parametrize('fault',['angle','velocity','time','line','shape','support','origin','method'])
def test_saved_raw_interval_rejects_changed_units_missing_samples_and_false_support(fault):
    arrays,layout,result=material()
    if fault=='angle':arrays['theta']*=2
    elif fault=='velocity':arrays['dv']*=-1
    elif fault=='time':arrays['dt'][0]=0
    elif fault=='line':arrays['line_number'][2]+=1
    elif fault=='shape':arrays['angular_rate_rads']=arrays['angular_rate_rads'][:-1]
    elif fault=='support':layout['times_s'][-1]=.31
    elif fault=='origin':layout['time_origin_gps_sow_s']=0
    else:layout['sampling_hypothesis']='left_hold'
    with pytest.raises(ValueError):library().validate_interval(packed(arrays),layout,result)
