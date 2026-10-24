# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run under the numerical guard after the active pilot releases capacity."""
import copy

import pytest


def test_constant_height_has_no_reference_variation():
    from lll.airquantumgrav_diagnosis import gravity_reference
    result=gravity_reference([0.,60.,120.,180.],[1500.]*4,2)
    assert result['range_mps2']==result['constant_acceleration_position_scale_m']==0.
    assert result['reference_gravity_mps2']==[9.81]*4
    assert not result['gravity_measured'] and not result['scale_is_forecast'] and not result['scale_is_error_bound']


def test_increasing_height_has_independently_expected_gravity_change():
    from lll.airquantumgrav_diagnosis import gravity_reference
    result=gravity_reference([0.,100.,200.,300.],[0.,500.,1000.,2000.],2)
    # Independent first-order free-air scale over 2 km; not the helper's exact formula.
    assert result['reference_gravity_mps2'][-1]-9.81==pytest.approx(-.00616,abs=8e-6)
    assert result['minimum_mps2']<result['training_mean_mps2']<result['maximum_mps2']
    assert result['prediction_span_s']==100.
    assert not result['causation_established']


def test_fixed_blocks_never_cross_training_boundary_or_change_errors():
    from lll.airquantumgrav_diagnosis import fixed_blocks
    times=[0.,30.,59.,60.,90.,120.,150.];errors=[[1.,2.,3.] for _ in times];before=copy.deepcopy(errors)
    result=fixed_blocks(times,errors,4)
    assert sum(v['epochs'] for v in result['blocks'])==len(times)
    assert [(v['section'],v['first_epoch'],v['last_epoch']) for v in result['blocks']]==[
        ('training',0,2),('training',3,3),('prediction',4,5),('prediction',6,6)]
    assert all(v['horizontal_rms_m']==pytest.approx(5**.5) for v in result['blocks'])
    assert errors==before and not result['forecasts_changed'] and not result['blocks_are_independent_trials']


def test_normalization_and_boundaries_do_not_claim_calibration_identification():
    from lll.airquantumgrav_diagnosis import calibration
    result=calibration(dict(gravity_delta=.5,gyro_gain_z=-1.,earth_removal=-1.),dict(gravity_delta=.1,gyro_gain_z=.01),9.8)
    assert result['fitted_constant_gravity_mps2']==pytest.approx(9.85)
    assert result['physical_linear_parameters']['gyro_gain_z']==-.01
    assert result['near_boundary']==['gyro_gain_z','earth_removal']
    assert not result['calibration_uniquely_identified'] and not result['force_reference_is_independent_gravity']


def test_reference_failure_does_not_clip_or_repair_inputs():
    from lll.airquantumgrav_diagnosis import gravity_reference,fixed_blocks,calibration
    with pytest.raises(ValueError):gravity_reference([0.,1.],[0.,-6371000.],1)
    with pytest.raises(ValueError):gravity_reference([0.,0.],[0.,1.],1)
    with pytest.raises(ValueError):fixed_blocks([0.,1.],[[0.,0.,0.],[0.,0.,float('nan')]],1)
    with pytest.raises(ValueError):calibration(dict(gravity_delta=1.01),dict(gravity_delta=.1),9.8)


def test_saved_diagnosis_preserves_missing_predictions_and_has_no_native_work(tmp_path):
    """Exercise the whole saved-data calculation, journal and figures without a motion kernel."""
    import gzip
    import io
    import itertools
    import json
    from types import SimpleNamespace
    import numpy as np
    from lll.airquantumgrav_diagnosis import evaluate,environment,recipe,tasks,SCOPE
    from lll.airquantumgrav_geographic_report import construction_counts
    from lll.studies.artifacts import digest,encoded

    r=recipe();task=tasks()[0];identity=task['identity']
    times=np.arange(1.,1201.);raw_times=np.arange(2401,dtype=float)/2
    raw_dt=np.diff(raw_times);raw_dv=np.zeros((2400,3));raw_dv[:,2]=-9.8*raw_dt
    buffer=io.BytesIO()
    np.savez(buffer,raw_time_s=raw_times,temperature_c=np.full(len(raw_times),21.),dv=raw_dv,dt=raw_dt)
    combinations=list(itertools.product(('sphere_rotating','sphere_still','flat_still'),(False,True),
        ('reported-short-v1','reported-persistent-v1')))
    pilot_manifest={'tasks':[{'payload':dict(model=m,profile=p,policy_id=w)} for m,p,w in combinations]}
    pilot_raw=encoded(pilot_manifest);metrics=dict(horizontal_rms_m=5.,vertical_rms_m=12.)
    primary=dict(identity='saved-only',normalized_parameters=dict(gravity_delta=-.5),training=metrics,prediction=metrics)
    groups=[dict(model=m,profile=p,policy_id=w,primary=primary if i==0 else None,
        selected_training_start=0) for i,(m,p,w) in enumerate(combinations)]
    report=dict(verified=True,total=24,expected_primaries=12,manifest_sha256=digest(pilot_raw),
        original_reads=0,protected_reads=0,native_calls_during_audit=0,source=dict(raw_points=len(raw_times)),
        primaries=groups,calibration_limits=dict(gravity_delta=.1),start_sensitivity=[dict(preserved=True)])
    receiver=[dict(time_s=float(t),height_m=1500.,north_mps=50.,east_mps=0.,latitude_deg=45.) for t in times]
    curves={'saved-only':dict(times_s=times.tolist(),errors_neu_m=[[3.,4.,12.] for _ in times],source_sha256='a'*64)}
    materials=dict(recipe=encoded(r),**{'qualification-environment':encoded(environment()),
        'pilot-report':encoded(report),'pilot-manifest':pilot_raw,
        'query-layout':encoded(dict(training_epochs=800,prediction_epochs=400,time_origin_gps_sow_s=0.,times_s=times.tolist())),
        'interval':buffer.getvalue(),'scoring':gzip.compress(encoded(receiver),mtime=0),
        'curves':gzip.compress(encoded(curves),mtime=0)})
    inputs={}
    for i,(key,value) in enumerate(materials.items()):
        path=tmp_path/f'input-{i}';path.write_bytes(value);inputs[key]=path
    manifest=dict(scope=SCOPE,limits=dict(maximum_wall_s=600.))
    (tmp_path/'manifest.json').write_bytes(encoded(manifest))
    directory=tmp_path/'artifacts'/identity;directory.mkdir(parents=True)
    def save(name,value):
        path=directory/name;path.write_bytes(encoded(value));return name
    def save_bytes(name,value):
        (directory/name).write_bytes(value);return name
    context=SimpleNamespace(root=tmp_path,directory=directory,manifest=manifest,
        input_path=lambda key:inputs[key],save=save,save_bytes=save_bytes,note_file=lambda path:None)
    result=evaluate(task,context)
    assert result['passed'] and result['available_settings']==1 and result['settings']==12
    assert all(result[key]==0 for key in ('native_calls','observed_starts','new_propagations','original_reads','protected_reads'))
    assert result['processed_primary_error_epochs']==1200 and not result['forecasts_changed']
    assert not result['causation_established'] and result['scientific_decision']=='abstain'
    cases=json.loads((directory/'cases.json').read_bytes())
    assert len(cases)==12 and sum(v['available'] for v in cases)==1
    assert cases[0]['training']==cases[0]['prediction']==metrics
    assert all(not v['available'] and v['selected_training_start']==0 for v in cases[1:])
    assert sum(v['epochs'] for v in cases[0]['blocks'])==1200
    assert all(v['horizontal_rms_m']==5. and v['vertical_rms_m']==12. for v in cases[0]['blocks'])
    assert json.loads((directory/'start-sensitivity.json').read_bytes())==report['start_sensitivity']
    for name in ('context.png','saved-errors.png'):
        assert (directory/name).read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    counts=construction_counts((directory/'diagnosis-work.sqlite').read_bytes(),
        digest((tmp_path/'manifest.json').read_bytes()),identity,result['charged_work'])
    assert counts==result['charged_work'] and counts['saved_error_epochs']==28800
