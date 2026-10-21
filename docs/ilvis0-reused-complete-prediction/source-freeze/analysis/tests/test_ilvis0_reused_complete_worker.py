# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
import ilvis0_reused_complete_worker as worker


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path)
    baseline=[];inherited=[];inventory=[];tasks=[];rows=[]
    for model in range(3):
        for profile in (False,True):
            baseline.append(dict(model=model,profile=profile,complete=True,union_width_m=[4.]*3))
            inherited.append(dict(model=model,profile=profile,complete=True,union_lower_m=[-.5]*3,
                union_upper_m=[.5]*3,union_width_m=[1.]*3))
            for sector in range(8):
                identity=f'reuse-{model}-{int(profile)}-{sector}'
                fresh=(model,profile)!=(1,True)
                meta=dict(identity=identity,source_identity=f'old-{model}-{int(profile)}-{sector}',
                    model=model,profile=profile,sector=sector,frame_sha256='a'*64,fresh=fresh)
                inventory.append(meta)
                if fresh:
                    tasks.append(dict(identity=identity,payload=meta))
                    rows.append(dict(identity=identity,passed=True,excluded=False,
                        task=dict(model=model,profile=profile,sector=sector),
                        truth_in_sector=sector==4,known_truth_retained=True,
                        future_lower_m=[-1.5]*3,future_upper_m=[1.5]*3))
    for name,value in (('baseline',dict(cases=baseline)),('inherited',dict(cases=inherited)),
                       ('inventory',dict(regions=inventory))):
        (tmp_path/(name+'.json')).write_text(json.dumps(value))
    return dict(tasks=tasks,inputs={name:dict(path=name+'.json') for name in ('baseline','inherited','inventory')}),rows


def test_complete_inherited_fallback_is_distinct_from_fresh_coverage(tmp_path,monkeypatch):
    manifest,rows=fixture(tmp_path,monkeypatch);result=worker.comparison(manifest,rows)
    assert result['qualified'] and result['all_cases_twofold'] and result['all_scheduled_passed']
    assert sum(c['fresh_complete'] for c in result['cases'])==5
    fallback=next(c for c in result['cases'] if c['model']==1 and c['profile'])
    assert fallback['mode']=='inherited-only' and fallback['fresh_lower'] is None
    assert fallback['completed_regions']==0 and fallback['combined_complete']
    assert not result['observational_coverage_qualified']


@pytest.mark.parametrize('change',('missing','failed','no-truth'))
def test_partial_or_failed_new_cover_cannot_qualify_through_inherited_fallback(tmp_path,monkeypatch,change):
    manifest,rows=fixture(tmp_path,monkeypatch)
    if change=='missing':rows.pop(0)
    if change=='failed':rows[0]=dict(identity=rows[0]['identity'],passed=False)
    if change=='no-truth':rows[4]['truth_in_sector']=False
    result=worker.comparison(manifest,rows)
    assert not result['qualified']
    assert not result['cases'][0]['fresh_complete']
    assert result['cases'][0]['mode']=='inherited-only'
    assert result['cases'][0]['fresh_lower'] is None


@pytest.mark.parametrize('change',('duplicate','unscheduled','wrong-sector','wrong-frame'))
def test_frozen_inventory_and_result_identities_are_enforced(tmp_path,monkeypatch,change):
    manifest,rows=fixture(tmp_path,monkeypatch)
    if change=='duplicate':rows.append(rows[0])
    if change=='unscheduled':rows[0]['identity']='other'
    if change=='wrong-sector':rows[0]['task']['sector']=7
    if change=='wrong-frame':manifest['tasks'][0]['payload']['frame_sha256']='b'*64
    with pytest.raises(ValueError):worker.comparison(manifest,rows)


@pytest.mark.parametrize('row,accepted',(
    ({'passed':True},True),
    ({'passed':False,'error_type':'Unsupported','reason':'time allowance exhausted'},True),
    ({'passed':False,'error_type':'ValueError','reason':'time allowance exhausted'},False),
    ({'passed':False,'error_type':'Unsupported','reason':'known truth lost'},False),
    ({'passed':False},False),
))
def test_only_passing_or_time_limited_source_tasks_can_supply_reports(row,accepted):
    assert worker.provider_eligible(row) is accepted
