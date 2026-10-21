# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import math
import pytest


def source(model='sphere_rotating'):
    return dict(model=model,profile=True,packets=2,durations=[.005,.005],starts=[0.,.005],base_time=.01,
        raw_theta=[[.001,-.002,0.],[-.003,.004,-0.]],raw_dv=[[0.,.01,-.04905],[.02,-.01,-.049]],
        limits=[.01]*25+[0.,1.],center=[0.]*27,seed_coordinates=[-.8,3.1416,12000.],
        seed_velocity=[100.,150.,-.1],seed_rotation=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]],radius=6371000.)


@pytest.mark.parametrize('model,index',(('sphere_rotating',0),('sphere_still',1),('flat_still',2)))
@pytest.mark.parametrize('profile',(False,True))
def test_generated_adapter_preserves_measurements_limits_frames_and_declares_processing(model,index,profile):
    from lll.ilvis0_legacy_recording import convert
    old=source(model);case=convert(old,profile=profile,source_sha256='a'*64,expected_packets=2)
    config=case['configuration']
    assert case['theta']==old['raw_theta'] and case['dv']==old['raw_dv'] and case['dt']==old['durations']
    assert config['limits']==old['limits'] and case['center']==old['center']
    assert config['initial_c']==old['seed_coordinates'] and config['initial_v']==old['seed_velocity']
    assert config['initial_r']==old['seed_rotation'] and config['radius']==old['radius']
    assert config['model']==index and config['profile'] is profile and config['gravity']==9.81
    assert case['provenance']['original_profile'] is True
    assert case['provenance']['clock_offset_fixed'] is True
    assert case['provenance']['source_sha256']=='a'*64
    assert math.copysign(1.,case['theta'][1][2])==-1.
    assert 'truth' not in case


def test_converted_case_owns_its_arrays_and_does_not_normalize_the_mount():
    from lll.ilvis0_legacy_recording import convert
    old=source();old['seed_rotation'][0][1]=2**-50;before=deepcopy(old)
    case=convert(old,profile=True,source_sha256='a'*64,expected_packets=2)
    assert old==before
    old['raw_theta'][0][0]=99.;old['limits'][0]=99.;old['seed_rotation'][0][1]=99.
    assert case['theta'][0][0]==.001 and case['configuration']['limits'][0]==.01
    assert case['configuration']['initial_r'][0][1]==2**-50


@pytest.mark.parametrize('change',('model','profile','hash','count','length','nan','negative-dt',
    'reversed-start','incorrect-end','negative-limit','missing-column','bad-rotation'))
def test_malformed_or_reinterpreted_generated_input_is_rejected(change):
    from lll.ilvis0_legacy_recording import convert
    old=source();profile=True;digest='a'*64
    if change=='model':old['model']='unknown'
    if change=='profile':profile=1
    if change=='hash':digest='not-a-hash'
    if change=='count':old['packets']=3
    if change=='length':old['raw_theta'].pop()
    if change=='nan':old['raw_dv'][0][2]=float('nan')
    if change=='negative-dt':old['durations'][0]=-.005
    if change=='reversed-start':old['starts'][1]=-.005
    if change=='incorrect-end':old['base_time']=.011
    if change=='negative-limit':old['limits'][0]=-.01
    if change=='missing-column':old['limits'].pop()
    if change=='bad-rotation':old['seed_rotation'].pop()
    with pytest.raises(ValueError):convert(old,profile=profile,source_sha256=digest,expected_packets=2)
