# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-value checks only; these fixtures do not qualify native arithmetic."""
from copy import deepcopy
import math
import pytest


def pair():
    old=dict(time_s=290.,normalized_center=[0.]*27,center=[.1,.2,30.],
        previous_coefficients=[[1.]*6 for _ in range(3)],
        acceleration_coefficients=[[2.]*9 for _ in range(3)],
        transform_coefficients=[[3.]*9 for _ in range(3)])
    point=dict(time_s=290.,point=[0.]*27,prediction=old['center'][:],status=0,warning=0,
        jacobian=[[float(i) for i in range(27)] for _ in range(3)])
    return old,deepcopy(old),point


def test_saved_pair_reconstructs_all_columns_without_native_calls():
    from lll.ilvis0_native_prefix_audit import check_saved_pair
    old,new,point=pair();out=check_saved_pair(old,new,point,expected_time=290.)
    assert len(out['matrix'])==3 and all(len(row)==51 for row in out['matrix'])
    assert out['matrix'][0]==list(map(float,range(27)))+[1.]*6+[2.]*9+[3.]*9
    assert out['native_center_error_m']==[0.,0.,0.]
    assert out['report_equal'] and out['numerical_work']==0


@pytest.mark.parametrize('change',['ulp','sign','jacobian','point','time','status','nan','oracle'])
def test_saved_pair_rejects_changed_values_and_invalid_oracle(change):
    from lll.ilvis0_native_prefix_audit import check_saved_pair
    old,new,point=pair()
    if change=='ulp':new['center'][0]=math.nextafter(new['center'][0],math.inf)
    if change=='sign':new['normalized_center'][0]=-0.
    if change=='jacobian':point['jacobian'][0].pop()
    if change=='point':point['point'][0]=.1
    if change=='time':point['time_s']=438.
    if change=='status':point['status']=1
    if change=='nan':point['jacobian'][0][0]=math.nan
    if change=='oracle':point['prediction'][2]+=.01
    with pytest.raises(ValueError):check_saved_pair(old,new,point,expected_time=290.)


def test_audit_cannot_infer_unretained_query_from_an_equal_earlier_one():
    from lll.ilvis0_native_prefix_audit import check_saved_reports
    old,new,point=pair();late=deepcopy(old);late['time_s']=438.
    late_point=deepcopy(point);late_point['time_s']=438.
    out=check_saved_reports([old,late],{0:new},[point,late_point])
    assert out['report_comparisons']==1 and out['missing_queries']==[1]
    assert out['all_queries_verified'] is False
    new_late=deepcopy(late);new_late['center'][0]+=.01
    with pytest.raises(ValueError):check_saved_reports([old,late],{0:new,1:new_late},[point,late_point])


def case():
    from lll.ilvis0_native_prefix_long import batch_limits,recipe
    from lll.studies.artifacts import digest,encoded
    old,new,point=pair();late=deepcopy(old);late['time_s']=438.
    late_point=deepcopy(point);late_point['time_s']=438.
    r=recipe();n=r['packets'];reserved=batch_limits(n)
    used=dict(reserved,packet_steps=88000,prefix_packet_steps=87000,tail_packet_steps=1000)
    reference=dict(report=late,certificate=dict(saved_report_sha256=digest(encoded(late))),
        early_reference=dict(report=old))
    task=dict(identity='case',payload=dict(recipe=r,reused_early=True),
        limits=dict(native_calls=2,packet_visits=2*n,bound_calls=1,bound_steps=18*n))
    envelope=dict(result=dict(passed=False,error_type='ValueError',
        reason='complete long report differs from sealed cold reference'),charged=deepcopy(task['limits']))
    artifacts={'compatibility.json':reference['certificate'],'cold-00.json':old,'cold-01-reused.json':late,
        'cold-work.json':dict(elapsed_s=0.,peak_rss_bytes=1000),
        'batch-progress.json':dict(elapsed_s=5000.,peak_rss_bytes=1000,actual_prepaid_work=used,reservations=reserved),
        'batched-00.json':new,'native-00.json':point,'native-01.json':late_point}
    return task,envelope,reference,artifacts


def test_only_complete_format_failures_can_have_missing_output_recovery():
    from lll.ilvis0_native_prefix_audit import check_case
    out=check_case(*case())
    assert out['missing_queries']==[1] and out['needs_cached_recovery']
    assert out['oracle_comparisons']==2 and out['original_result']['passed'] is False
    assert out['numerical_work']==0


@pytest.mark.parametrize('change',['reason','timeout','negative','memory','charge','work','missing','cold','oracle'])
def test_recovery_rejects_incomplete_or_incompatible_evidence(change):
    from lll.ilvis0_native_prefix_audit import check_case
    task,envelope,reference,artifacts=deepcopy(case())
    if change=='reason':envelope['result']['reason']='budget exhausted'
    if change=='timeout':artifacts['batch-progress.json']['elapsed_s']=15000.
    if change=='negative':artifacts['batch-progress.json']['elapsed_s']=-1.
    if change=='memory':artifacts['batch-progress.json']['peak_rss_bytes']=2**40
    if change=='charge':envelope['charged']['bound_calls']=0
    if change=='work':artifacts['batch-progress.json']['actual_prepaid_work']['packet_steps']=1
    if change=='missing':artifacts.pop('batched-00.json')
    if change=='cold':artifacts['cold-01-reused.json']=artifacts['cold-00.json']
    if change=='oracle':artifacts['native-01.json']['point'][0]=.5
    with pytest.raises(ValueError):check_case(task,envelope,reference,artifacts)


def test_recovery_compatibility_permits_only_the_documented_report_fix(tmp_path):
    from lll.ilvis0_native_prefix_audit import compatible_recovery_sources
    from lll.studies.artifacts import digest
    adapter='analysis/lll/ilvis0_native_prefix_long.py'
    storage='analysis/lll/studies/artifacts.py';physics='analysis/lll/physics.py'
    old=b'def recipe():\n return 1\ndef compare():\n return "old check"\n'
    new=b'def recipe():\n return 1\ndef compare():\n return "serialized check"\n'
    old_storage=b'def encoded(value):\n return value\n'
    new_storage=old_storage+b'def reports_equal(a,b):\n return encoded(a)==encoded(b)\n'
    previous={adapter:digest(old),storage:digest(old_storage),physics:digest(b'physics')}
    for name,raw in ((adapter,new),(storage,new_storage),(physics,b'physics')):
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    out=compatible_recovery_sources(previous,tmp_path,frozen_adapter=old,frozen_storage=old_storage)
    assert out['unchanged_dependencies']==[physics]
    (tmp_path/physics).write_bytes(b'changed physics')
    with pytest.raises(ValueError,match='dependency'):compatible_recovery_sources(previous,tmp_path,frozen_adapter=old,frozen_storage=old_storage)
    (tmp_path/physics).write_bytes(b'physics')
    (tmp_path/adapter).write_bytes(new.replace(b'return 1',b'return 2'))
    with pytest.raises(ValueError,match='helper'):compatible_recovery_sources(previous,tmp_path,frozen_adapter=old,frozen_storage=old_storage)
    (tmp_path/adapter).write_bytes(new)
    (tmp_path/storage).write_bytes(new_storage.replace(b'return value',b'return str(value)'))
    with pytest.raises(ValueError,match='encoder'):compatible_recovery_sources(previous,tmp_path,frozen_adapter=old,frozen_storage=old_storage)
