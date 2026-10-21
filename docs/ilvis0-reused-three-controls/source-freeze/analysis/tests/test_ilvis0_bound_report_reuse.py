# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only validation: no numerical libraries, integration or LPs."""
from copy import deepcopy
import hashlib
import json
import pytest


def report():
    return dict(version='joint-bound-report-v1',time_s=7.2,center=[1.,2.,3.],
        physical_parameter_count=27,enclosure_parameter_count=51,
        normalized_center=[0.]*27,lower=[-.5]*27,upper=[.5]*27,
        bound_lower=[-.5]*27,bound_upper=[.5]*27,
        source_id='source',reference_binding='reference',shared_binding='shared',
        acceleration_binding='acceleration',transform_binding='transform',
        previous_coefficients=[[0.]*6 for _ in range(3)],
        acceleration_coefficients=[[0.]*9 for _ in range(3)],
        transform_coefficients=[[0.]*9 for _ in range(3)],
        previous_caps=[1.]*6,acceleration_caps=[1.]*9,
        retained_acceleration_remainder=.1,transform_reference=dict(binding='transform',caps=[1.]*9),
        conditioning=dict(binding='training'),source_initial_padding=['0','0','0'],
        unshared_remainder=[2.,3.,4.],position_unshared_remainder=[1.,1.,1.],
        floating_point_enclosure_verified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def provider(tmp_path,name,payload=None,environment='0'*64):
    from lll.ilvis0_bound_report_reuse import Provider
    blob=json.dumps(payload if payload is not None else report(),sort_keys=True,allow_nan=False).encode()
    path=tmp_path/(name+'.json');path.write_bytes(blob)
    return Provider.from_file(name,path,sha256=hashlib.sha256(blob).hexdigest(),environment_sha256=environment)


def test_reuse_minimum_keeps_maps_and_provider_identity(tmp_path):
    from lll.ilvis0_bound_report_reuse import merge_reports
    a=provider(tmp_path,'old');changed=report();changed['unshared_remainder']=[1.,5.,2.]
    b=provider(tmp_path,'new',changed)
    result=merge_reports([a,b])
    assert result['unshared_remainder']==[1.,3.,2.]
    assert result['center']==report()['center']
    assert result['previous_coefficients']==report()['previous_coefficients']
    assert result['certificate_reuse']['coordinate_providers']==['new','old','new']
    assert 'position_unshared_remainder' not in result
    assert result['scientific_decision']=='abstain' and not result['observational_coverage_qualified']
    assert result==merge_reports([b,a])


@pytest.mark.parametrize('field',('source_id','reference_binding','shared_binding','acceleration_binding',
    'transform_binding','time_s','center','lower','upper','normalized_center','bound_lower','bound_upper',
    'previous_coefficients','acceleration_coefficients','transform_coefficients','previous_caps',
    'acceleration_caps','conditioning','source_initial_padding','retained_acceleration_remainder','transform_reference'))
def test_mismatched_physical_or_shared_definition_is_rejected(tmp_path,field):
    from lll.ilvis0_bound_report_reuse import merge_reports
    a=provider(tmp_path,'one');changed=report();value=changed[field]
    if isinstance(value,str):changed[field]=value+'-changed'
    elif isinstance(value,dict):changed[field]=dict(value,changed=True)
    elif isinstance(value,list):
        if isinstance(value[0],list):value[0][0]=.01
        elif isinstance(value[0],str):value[0]='1'
        else:value[0]+=.01
    else:changed[field]+=.01
    with pytest.raises(ValueError):merge_reports([a,provider(tmp_path,'two',changed)])


def test_hash_environment_and_duplicate_providers_are_rejected(tmp_path):
    from lll.ilvis0_bound_report_reuse import Provider,merge_reports
    a=provider(tmp_path,'one');path=tmp_path/'one.json'
    with pytest.raises(ValueError):Provider.from_file('wrong',path,sha256='f'*64,environment_sha256='0'*64)
    with pytest.raises(ValueError):merge_reports([a,a])
    with pytest.raises(ValueError):merge_reports([a,provider(tmp_path,'two',environment='1'*64)])


@pytest.mark.parametrize('change',('missing','shape','negative','boolean','infinite'))
def test_incomplete_or_invalid_reports_are_rejected(tmp_path,change):
    from lll.ilvis0_bound_report_reuse import merge_reports
    changed=report()
    if change=='missing':del changed['normalized_center']
    if change=='shape':changed['transform_coefficients'][0].pop()
    if change=='negative':changed['unshared_remainder'][0]=-1.
    if change=='boolean':changed['unshared_remainder'][0]=True
    if change=='infinite':changed['unshared_remainder'][0]='Infinity'
    with pytest.raises(ValueError):merge_reports([provider(tmp_path,'bad',changed)])


def test_provider_owns_bytes_and_duplicate_json_fields_are_rejected(tmp_path):
    from lll.ilvis0_bound_report_reuse import Provider,merge_reports
    a=provider(tmp_path,'one');before=merge_reports([a]);(tmp_path/'one.json').write_text('{}')
    assert merge_reports([a])==before
    blob=b'{"unshared_remainder":[1,2,3],"unshared_remainder":[0,0,0]}'
    path=tmp_path/'duplicate.json';path.write_bytes(blob)
    with pytest.raises(ValueError):
        Provider.from_file('duplicate',path,sha256=hashlib.sha256(blob).hexdigest(),environment_sha256='0'*64)
