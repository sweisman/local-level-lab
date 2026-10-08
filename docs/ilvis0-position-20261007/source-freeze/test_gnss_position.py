# SPDX-License-Identifier: AGPL-3.0-or-later
import math
import struct

import numpy as np
import pytest

from lll import gnss_position as gps, trimble_observations as orbit
from test_trimble_observations import ephemeris


def test_ionosphere_layout_units_and_no_default_substitution():
    values=[1e-8,2e-8,-3e-8,4e-8,72000.,1.,2.,3.,1e-9,1e-14,319488.,15.,15.,319488.]
    payload=b'\x03\x00'+struct.pack('>14d',*values)+b'\xf7\xf7\x00'+b'\0'*6
    result=gps.decode_ionosphere(payload)
    assert result['alpha']==values[:4] and result['beta']==values[4:8]
    assert result['leap_seconds']==15
    with pytest.raises(ValueError):
        gps.decode_ionosphere(payload[:-1])
    with pytest.raises(ValueError,match='coefficients required'):
        gps.klobuchar(0.,0.,0.,0.,.5,None)
    midnight=dict(alpha=[0.]*4,beta=[72000.,0.,0.,0.])
    assert gps.klobuchar(0.,0.,0.,0.,math.pi/2,midnight)==pytest.approx(gps.C*(1+16*(.03)**3)*5e-9)


@pytest.mark.parametrize('latitude,height',[(0.,0.),(.8,12000.),(-1.2,1000.),(math.pi/2,50.)])
def test_geodetic_roundtrip_and_local_axes(latitude,height):
    position=gps.ecef(latitude,-1.3,height)
    lat,lon,h=gps.geodetic(position)
    assert (lat,h)==pytest.approx((latitude,height),abs=1e-7)
    if abs(latitude)<math.pi/2:
        assert lon==pytest.approx(-1.3)
    rotation=gps.local_rotation(latitude,-1.3)
    assert rotation@rotation.T==pytest.approx(np.eye(3),abs=1e-14)


def test_troposphere_does_not_vanish_at_airborne_height():
    sea=gps.troposphere(.5,0.,math.pi/2,humidity=0.)
    airborne=gps.troposphere(.5,12000.,math.pi/2,humidity=0.)
    assert 2.2<sea<2.4 and .3<airborne<.6
    assert gps.troposphere(.5,12000.,math.pi/6,humidity=0.)==pytest.approx(airborne*2)
    with pytest.raises(ValueError):
        gps.troposphere(.5,30000.,math.pi/2)


def test_clock_relativity_and_signal_transmit_time():
    eph=orbit.decode_gps_ephemeris(ephemeris())
    seconds=216130.
    dt=seconds-eph['toc_s']
    polynomial=eph['af0']+dt*(eph['af1']+dt*eph['af2'])
    assert gps.clock(eph,1527,seconds,relativity=False)==pytest.approx(polynomial)
    assert gps.clock(eph,1527,seconds)!=polynomial
    position,bias,transmit=gps.satellite_state(eph,1527,seconds,20e6)
    assert abs(transmit-(seconds-20e6/gps.C-polynomial))<1e-8
    assert np.linalg.norm(position)>2e7 and math.isfinite(bias)
    with pytest.raises(ValueError,match='stale'):
        gps.satellite_state(eph,1528,seconds,20e6)


def static_ranges(position,bias):
    rotation=gps.local_rotation(*gps.geodetic(position)[:2])
    selected=[]
    for index,(az,el) in enumerate([(0,30),(90,30),(180,30),(270,30),(45,70),(225,60)]):
        az,el=math.radians(az),math.radians(el)
        direction=rotation.T@np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
        satellite=position+22e6*direction
        sagnac=gps.OMEGA/gps.C*(satellite[0]*position[1]-satellite[1]*position[0])
        selected.append(dict(sv_id=index+1,satellite_ecef_m=satellite.tolist(),
            satellite_clock_s=0.,observed_corrected_code_m=22e6+sagnac+bias))
    return selected


def test_range_solution_recovers_position_and_common_clock_without_receiver_constraint(monkeypatch):
    position=gps.ecef(.8,-1.1,9000.); bias=72000.
    selected=static_ranges(position,bias)
    monkeypatch.setattr(gps,'observations',lambda *args:(selected,[]))
    monkeypatch.setattr(gps,'troposphere',lambda *args:0.)
    result=gps.solve(dict(gps_week_seconds=100.),[],None,'dual_frequency',position+[1000.,-800.,500.])
    assert result['status']=='converged'
    assert result['ecef_m']==pytest.approx(position,abs=1e-5)
    assert result['receiver_clock_m']==pytest.approx(bias,abs=1e-5)
    assert result['range_rms_m']<1e-6 and not result['covariance_calibrated']
    # Leave a bad range in the result; there is no residual-driven deletion.
    selected[0]['observed_corrected_code_m']+=20.
    noisy=gps.solve(dict(gps_week_seconds=100.),[],None,'dual_frequency',position)
    assert noisy['status']=='converged' and noisy['observations']==6
    assert noisy['range_rms_m']>0.


def test_rank_abstention_is_recorded(monkeypatch):
    position=gps.ecef(.8,-1.1,9000.)
    selected=[static_ranges(position,0.)[0]]*6
    monkeypatch.setattr(gps,'observations',lambda *args:(selected,[]))
    monkeypatch.setattr(gps,'troposphere',lambda *args:0.)
    result=gps.solve(dict(gps_week_seconds=100.),[],None,'dual_frequency',position)
    assert result['status']=='abstain' and 'rank' in result['reason']


def test_dual_frequency_combination_and_tgd_use_distinct_corrections():
    eph=orbit.decode_gps_ephemeris(ephemeris()) | dict(payload_sha256='ephemeris',tgd_s=1e-8)
    record=dict(format='RT27',gps_week=1527,gps_week_seconds=216130.,satellites=[dict(
        system=0,antenna=0,sv_id=7,flags=[0],signals=[
            dict(band=0,track_type=0,range_loaded=True,pseudorange_m=20e6),
            dict(band=1,track_type=2,range_loaded=True,pseudorange_m=20e6+gps.GAMMA*10-10)])])
    single,_=gps.observations(record,[eph],'l1_broadcast')
    dual,_=gps.observations(record,[eph],'dual_frequency')
    assert single[0]['observed_corrected_code_m']==pytest.approx(20e6-gps.C*1e-8)
    assert dual[0]['observed_corrected_code_m']==pytest.approx(20e6-10)
    assert dual[0]['code_bias_correction_m']==0.
    record['satellites'][0]['signals']=record['satellites'][0]['signals'][:1]
    assert not gps.observations(record,[eph],'dual_frequency')[0]
