# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import hashlib
import json

import pytest


def module():
    from lll import ilvis0_artifact_inventory
    return ilvis0_artifact_inventory


def example():
    fit=dict(converged=True,active_parameters=['a','time_offset'],normalized_parameters=[.2,.1],residual_sum_squares=91.)
    saved=dict(active_parameters=['a','time_offset'],normalized_parameters=[.2,.1],
        residual=[1.,2.,3.,4.,5.,6.],jacobian=[[.1,.2]]*6)
    fixes=[dict(time_s=100.25,latitude_rad=.5,longitude_rad=.2,height_m=1000.),
           dict(time_s=101.25,latitude_rad=.51,longitude_rad=.21,height_m=1001.)]
    return fit,saved,dict(times_s=[.25,1.25]),fixes


def test_payload_validation_preserves_all_arrays_and_receiver_context():
    values=example();before=copy.deepcopy(values)
    report=module().validate_payload(*values)
    assert values==before
    assert report['receiver_epochs']==2 and report['parameters']==2 and report['residual_count']==6
    assert report['time_origin_s']==100. and report['parameter_match']
    fit,saved,epochs,fixes=values
    saved.update(times_s=epochs['times_s'],gps=[[r['latitude_rad'],r['longitude_rad'],r['height_m']] for r in fixes])
    assert module().validate_payload(fit,saved,None,fixes)['embedded_receiver_context']


@pytest.mark.parametrize('bad',['point','order','residual','jacobian','nonfinite','cost','epochs','time','gps','fit'])
def test_incompatible_arrays_are_not_silently_reused(bad):
    fit,saved,epochs,fixes=example()
    if bad=='point':saved['normalized_parameters'][0]+=.1
    if bad=='order':saved['active_parameters'].reverse()
    if bad=='residual':saved['residual'].pop()
    if bad=='jacobian':saved['jacobian'][0]=[.1]
    if bad=='nonfinite':saved['jacobian'][0][0]=float('nan')
    if bad=='cost':fit['residual_sum_squares']=1.
    if bad=='epochs':epochs['times_s'].pop()
    if bad=='time':epochs['times_s'][1]+=.001
    if bad=='gps':saved['gps']=[[.5,.2,1000.]]*2
    if bad=='fit':fit['converged']=False
    with pytest.raises(ValueError):module().validate_payload(fit,saved,epochs,fixes)


def test_absent_reference_is_explicit_and_does_not_search_for_a_better_fit(tmp_path):
    assert module().find_artifact(tmp_path,tmp_path,{}, {},'linearization') is None


def test_recorded_digest_resolves_a_published_copy_and_rejects_corruption(tmp_path):
    directory=tmp_path/'docs'/'study';directory.mkdir(parents=True)
    artifact=directory/'evidence-copy.gz';artifact.write_bytes(b'original bytes')
    digest=hashlib.sha256(artifact.read_bytes()).hexdigest()
    fit=dict(linearization_file='original.gz',linearization_sha256=digest)
    manifest=dict(inputs={'docs/study/evidence-copy.gz':digest})
    assert module().find_artifact(tmp_path,directory,fit,manifest,'linearization')==artifact
    artifact.write_bytes(b'changed')
    with pytest.raises(ValueError):module().find_artifact(tmp_path,directory,fit,manifest,'linearization')


def test_primary_selection_uses_declared_case_model_and_not_the_smallest_cost():
    cases=('bias1_unsubtracted','bias1_profiled_removal');models=('sphere_rotating','sphere_still','flat_still')
    row=dict(cases=[dict(case_id=c,fits=[dict(model=m,converged=True,residual_sum_squares=i+1.) for i,m in enumerate(models)]) for c in cases])
    assert module().primary_fit(row,cases[0],'flat_still')['residual_sum_squares']==3.
    row['cases'][0]['fits'].append(dict(model='flat_still',converged=True,residual_sum_squares=0.))
    with pytest.raises(ValueError):module().primary_fit(row,cases[0],'flat_still')
