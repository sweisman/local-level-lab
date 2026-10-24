# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib

import numpy as np
import pytest


def library():
    assert importlib.util.find_spec('lll.airquantumgrav_pilot_data') is not None,'pilot data preparation missing'
    return importlib.import_module('lll.airquantumgrav_pilot_data')


def selection():
    return dict(version='esa-receiver-full-motion-v2',eligible=[dict(first_index=4,last_index=4004,
        first_time_s=1002.,last_time_s=3002.,duration_s=2000.,distance_m=120000.,rejection_reasons=[])])


def receiver_rows():
    return [dict(sequence=i+5,time_s=1002.+i*.5,gps_week=2269,latitude_deg=65.,longitude_deg=-50.,height_m=1500.,
        position_variance_m2=[1.,1.,4.],position_cross_covariance_m2=[0.,0.,0.],
        north_mps=60.,east_mps=0.,up_mps=0.,satellites=12,pdop=2.) for i in range(2401)]


def test_first_interval_layout_is_chronological_fixed_and_training_only():
    mod=library();chosen=mod.choose(selection());rows=receiver_rows();layout=mod.receiver_layout(rows,chosen)
    assert chosen['first_index']==4 and chosen['last_index']==2404
    assert len(layout['training_rows'])==800 and len(layout['scoring_rows'])==1200
    assert layout['query_source_indices']==list(range(5,2404,2))
    assert layout['training_rows']==rows[1:1600:2]
    assert layout['scoring_rows']==rows[1:2400:2]
    assert layout['later_positions_used_for_training'] is False


@pytest.mark.parametrize('fault',['empty','version','short','gap','sequence','week','reordered','nonfinite'])
def test_pilot_receiver_layout_rejects_unsupported_selection_without_repair(fault):
    mod=library();selected=selection();rows=receiver_rows()
    if fault=='empty':selected['eligible']=[]
    elif fault=='version':selected['version']='old'
    elif fault=='short':selected['eligible'][0]['last_index']=10
    elif fault=='gap':rows[100]['time_s']+=.3
    elif fault=='sequence':rows[100]['sequence']+=1
    elif fault=='week':rows[100]['gps_week']+=1
    elif fault=='reordered':selected['eligible']*=2
    else:selected['eligible'][0]['duration_s']=float('nan')
    with pytest.raises(ValueError):mod.receiver_layout(rows,mod.choose(selected))


def imu_rows():
    return [dict(line_number=i+2,gps_time_s=1000.+i*.003,
        acceleration_mps2=[1.,2.,3.],angular_rate_rads=[.1,.2,.3],temperature_c=20.,
        gap_above_1p5_nominal_periods=False) for i in range(20)]


def test_imu_window_preserves_original_samples_and_brackets_timing_allowance():
    mod=library();window=mod.RawWindow(1000.02,1000.04,maximum_points=20)
    rows=imu_rows()
    for row in rows:window.accept(row)
    raw=window.finish()
    assert raw['raw_time_s'][0]<=1000.02 and raw['raw_time_s'][-1]>=1000.04
    assert np.array_equal(raw['acceleration_mps2'],np.tile([1.,2.,3.],(len(raw['raw_time_s']),1)))
    assert np.array_equal(raw['line_number'],np.arange(8,17))
    assert np.array_equal(raw['angular_rate_rads'],np.tile([.1,.2,.3],(9,1)))


@pytest.mark.parametrize('fault',['gap','capacity','left','right'])
def test_imu_window_fails_instead_of_repairing_or_trimming(fault):
    mod=library();window=mod.RawWindow(1000.02,1000.04,maximum_points=2 if fault=='capacity' else 20)
    rows=imu_rows()
    if fault=='gap':rows[2]['gap_above_1p5_nominal_periods']=True
    elif fault=='left':rows=rows[9:]
    elif fault=='right':rows=rows[:9]
    with pytest.raises(ValueError):
        for row in rows:window.accept(row)
        window.finish()


def test_existing_imu_decoder_stream_and_interval_constructor_preserve_units():
    import hashlib
    import io
    from lll.airquantumgrav import HEADER,records
    from lll.airquantumgrav_geographic_controls import construct
    from lll.studies.streams import consume
    raw=(HEADER+'\n'+''.join(f'{1000+i*.003:.9f} 1 2 3 .1 .2 .3 20\n' for i in range(20))).encode()
    window=library().RawWindow(1000.02,1000.04,maximum_points=20);charges=[]
    result=consume(io.BytesIO(raw),decoder=records,expected_sha256=hashlib.sha256(raw).hexdigest(),
        expected_bytes=len(raw),maximum_records=25,block_size=4,reserve=charges.append,
        check_continue=lambda:None,accept=window.accept)
    source=window.finish();work=[]
    increments=construct(dict(times=source['raw_time_s'],angular_rate_rads=source['angular_rate_rads'],
        specific_force_mps2=source['acceleration_mps2']),method='linear_points',rate_hz=300,
        reserve=lambda **v:work.append(v))
    assert result['records']==20 and result['decoder_calls']==21 and sum(charges)==24
    assert work==[dict(constructed_intervals=8)]
    assert np.array_equal(increments['dt'],np.diff(source['raw_time_s']))
    np.testing.assert_allclose(increments['theta'],increments['dt'][:,None]*np.array([.1,.2,.3]),rtol=1e-15)
    np.testing.assert_allclose(increments['dv'],increments['dt'][:,None]*np.array([1.,2.,3.]),rtol=1e-15)
