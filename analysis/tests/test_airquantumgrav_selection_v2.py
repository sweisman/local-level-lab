# SPDX-License-Identifier: AGPL-3.0-or-later
"""Receiver-only full-motion selection and exact legacy compatibility."""
import copy
import json
import math
from pathlib import Path

import pytest

from lll import airquantumgrav_selection as selection
from test_airquantumgrav_selection import rows


def data(n=2501,speed=60.):
    result=rows(n=n,speed=speed)
    for row in result:row['position_cross_covariance_m2']=[0.,0.,0.]
    return result


def select(values,*,support=(999.,3000.)):
    assert hasattr(selection,'select_full_motion'), 'explicit full-motion selector is missing'
    return selection.select_full_motion(values,imu_support=support,source_integrity_verified=True)


@pytest.fixture(scope='module')
def legacy():
    from lll.studies.artifacts import ArchiveStore,digest
    from lll.studies.closed import load_python_reference
    store=ArchiveStore(Path(__file__).resolve().parents[2])
    try:
        manifest=json.loads(store.read('docs/esa-development-selection/manifest.json'))
        name='analysis/lll/airquantumgrav_selection.py';sha=manifest['sources'][name]
        raw=store.read('docs/esa-development-selection/source-freeze/'+name)
        assert digest(raw)==sha
        return load_python_reference(raw,name='lll._selection_v1_compatibility',sha256=sha)
    finally:store.close()


@pytest.mark.parametrize('kind',['plain','turn','climb','gap','quality','wrap','support'])
def test_version_one_is_identical_to_its_frozen_implementation(legacy,kind):
    values=data(n=2501 if kind=='plain' else 201);support=(999.,3000.)
    if kind in ('turn','wrap'):
        for i,row in enumerate(values):
            angle=math.radians((i*.1 if kind=='turn' else 359.9+i*.002))
            row.update(north_mps=60.*math.cos(angle),east_mps=60.*math.sin(angle))
    elif kind=='climb':
        for row in values[90:111]:row['up_mps']=2.
    elif kind=='gap':
        for row in values[100:]:row['time_s']+=1.
    elif kind=='quality':values[100]['satellites']=7
    elif kind=='support':support=(1010.,1050.)
    arguments=dict(imu_support=support,source_integrity_verified=True)
    assert selection.select(copy.deepcopy(values),**arguments)==legacy.select(copy.deepcopy(values),**arguments)


def test_full_motion_retains_turns_and_climbs_without_claiming_quiet_flight():
    values=data()
    for i,row in enumerate(values):
        angle=math.radians(i*.1);row.update(north_mps=60.*math.cos(angle),east_mps=60.*math.sin(angle),up_mps=2.)
    result=select(values)
    assert result['version']=='esa-receiver-full-motion-v2' and len(result['eligible'])==1
    assert result['eligible'][0]['duration_s']==1250.
    assert result['eligible'][0]['maximum_absolute_up_mps']==2.
    assert result['eligible'][0]['maximum_sampled_course_rate_deg_s']==pytest.approx(.2,abs=1e-12)
    assert result['instantaneous_motion_certified'] is False
    assert result['policy']['motion_treatment']=='modeled_from_native_imu'
    assert not any(result['epoch_reasons'])
    assert not selection.select(values,imu_support=(999.,3000.),source_integrity_verified=True)['eligible']


def test_full_motion_exact_duration_distance_and_quality_thresholds_pass():
    values=data(n=2401,speed=50.)
    for row in values:row.update(pdop=4.,satellites=8,position_variance_m2=[25.,25.,100.])
    run=select(values)['eligible'][0]
    assert run['duration_s']==1200. and run['distance_m']==60000.
    assert run['first_index']==0 and run['last_index']==2400


@pytest.mark.parametrize('kind,reason',[('covariance','receiver_covariance'),('pole','receiver_chart_support'),
    ('pdop','receiver_quality'),('satellites','receiver_quality'),('speed','speed'),('support','imu_support')])
def test_full_motion_failures_are_preserved_without_maneuver_margin(kind,reason):
    values=data(n=101);support=(999.,3000.)
    if kind=='covariance':values[50]['position_cross_covariance_m2']=[100.,0.,0.]
    elif kind=='pole':values[50]['latitude_deg']=90.
    elif kind=='pdop':values[50]['pdop']=4.01
    elif kind=='satellites':values[50]['satellites']=7
    elif kind=='speed':values[50]['north_mps']=49.99
    else:support=(1000.,1024.99)
    result=select(values,support=support)
    assert reason in result['epoch_reasons'][50]
    if kind!='support':assert not result['epoch_reasons'][49] and not result['epoch_reasons'][51]
    assert not result['eligible']


@pytest.mark.parametrize('kind',['time_gap','sequence_gap'])
def test_full_motion_splits_discontinuities_without_joining_short_runs(kind):
    values=data()
    for row in values[1250:]:row['time_s' if kind=='time_gap' else 'sequence']+=1.
    result=select(values)
    assert len(result['blocks'])==2 and len(result['rejected_runs'])==2 and not result['eligible']


def test_full_motion_uses_actual_timestamps_and_wrapped_heading_differences():
    values=data(n=101)
    for i,row in enumerate(values):
        row['time_s']+=.02*math.sin(i*.2);angle=math.radians(359.9+i*.002)
        row.update(north_mps=60.*math.cos(angle),east_mps=60.*math.sin(angle))
    result=select(values);run=result['rejected_runs'][0]
    assert math.isclose(run['distance_m'],60*run['duration_s'],rel_tol=1e-14)
    assert run['maximum_sampled_course_rate_deg_s']<.005


def test_full_motion_ignores_outcomes_and_does_not_mutate_receiver_rows():
    values=data(n=101);before=copy.deepcopy(values);a=select(values)
    assert values==before
    for row in values:row.update(gyro_mean=1000.,preferred_model='disc')
    assert select(values)==a


@pytest.mark.parametrize('kind',['cross_shape','missing_cross','duplicate','week','integrity'])
def test_full_motion_rejects_bad_schema_or_unverified_sources(kind):
    values=data(n=20)
    if kind=='cross_shape':values[0]['position_cross_covariance_m2']=[0.]
    elif kind=='missing_cross':del values[0]['position_cross_covariance_m2']
    elif kind=='duplicate':values[1]['time_s']=values[0]['time_s']
    elif kind=='week':values[1]['gps_week']+=1
    assert hasattr(selection,'select_full_motion'), 'explicit full-motion selector is missing'
    with pytest.raises(ValueError):selection.select_full_motion(values,imu_support=(999.,3000.),source_integrity_verified=kind!='integrity')
