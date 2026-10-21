# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
import ilvis0_three_source_complete_worker as worker


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
                meta=dict(identity=identity,source_identity=f'old-{model}-{int(profile)}-{sector}',
                    model=model,profile=profile,sector=sector,frame_sha256='a'*64,fresh=True)
                inventory.append(meta);tasks.append(dict(identity=identity,payload=meta))
                rows.append(dict(identity=identity,passed=True,excluded=False,
                    task=dict(model=model,profile=profile,sector=sector),truth_in_sector=sector==4,
                    known_truth_retained=True,future_lower_m=[-1.5]*3,future_upper_m=[1.5]*3))
    for name,value in (('baseline',dict(cases=baseline)),('inherited',dict(cases=inherited)),
                       ('inventory',dict(regions=inventory))):
        (tmp_path/(name+'.json')).write_text(json.dumps(value))
    return dict(tasks=tasks,inputs={name:dict(path=name+'.json') for name in ('baseline','inherited','inventory')}),rows


def test_all_six_complete_fresh_covers_are_required(tmp_path,monkeypatch):
    manifest,rows=fixture(tmp_path,monkeypatch);result=worker.comparison(manifest,rows)
    assert result['qualified'] and result['all_scheduled_passed'] and result['all_cases_twofold']
    assert len(result['cases'])==6 and all(c['fresh_complete'] for c in result['cases'])
    assert all(c['mode']=='complete-intersection' for c in result['cases'])
    assert not result['observational_coverage_qualified']


@pytest.mark.parametrize('change',('missing','failed','no-truth','too-wide'))
def test_inherited_success_cannot_hide_missing_new_checks(tmp_path,monkeypatch,change):
    manifest,rows=fixture(tmp_path,monkeypatch)
    if change=='missing':rows.pop(0)
    if change=='failed':rows[0]=dict(identity=rows[0]['identity'],passed=False)
    if change=='no-truth':rows[4]['truth_in_sector']=False
    if change=='too-wide':
        path=tmp_path/'baseline.json';value=json.loads(path.read_text());value['cases'][0]['union_width_m']=[.1]*3
        path.write_text(json.dumps(value))
    result=worker.comparison(manifest,rows)
    assert not result['qualified']


@pytest.mark.parametrize('change',('duplicate','wrong-sector','wrong-frame','fallback-mode'))
def test_identity_frame_and_complete_recipe_are_enforced(tmp_path,monkeypatch,change):
    manifest,rows=fixture(tmp_path,monkeypatch)
    if change=='duplicate':rows.append(rows[0])
    if change=='wrong-sector':rows[0]['task']['sector']=7
    if change=='wrong-frame':manifest['tasks'][0]['payload']['frame_sha256']='b'*64
    if change=='fallback-mode':
        path=tmp_path/'inventory.json';value=json.loads(path.read_text())
        for row in value['regions'][:8]:row['fresh']=False
        path.write_text(json.dumps(value))
        for row in manifest['tasks'][:8]:row['payload']['fresh']=False
    with pytest.raises(ValueError):worker.comparison(manifest,rows)
