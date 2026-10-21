# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
import ilvis0_directional_prediction_worker as worker


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path);baseline=[];inherited=[];rows=[]
    for model in range(3):
        for profile in (False,True):
            baseline.append(dict(model=model,profile=profile,union_width_m=[4.]*3))
            inherited.append(dict(model=model,profile=profile,complete=True,union_lower_m=[-.5]*3,
                union_upper_m=[.5]*3,union_width_m=[1.]*3))
            for sector in range(8):
                rows.append(dict(passed=True,excluded=False,task=dict(model=model,profile=profile,sector=sector),
                    truth_in_sector=sector==4,known_truth_retained=True,future_lower_m=[-1.5]*3,future_upper_m=[1.5]*3))
    (tmp_path/'baseline.json').write_text(json.dumps(dict(cases=baseline)))
    (tmp_path/'inherited.json').write_text(json.dumps(dict(cases=inherited)))
    return dict(inputs=dict(baseline=dict(path='baseline.json'),inherited=dict(path='inherited.json'))),rows


def test_fresh_and_combined_ranges_are_both_visible(tmp_path,monkeypatch):
    manifest,rows=fixture(tmp_path,monkeypatch);result=worker.comparison(manifest,rows)
    assert result['all_cases_twofold'] and not result['all_fresh_cases_twofold']
    assert all(c['fresh_width_m']==[3.]*3 and c['union_width_m']==[1.]*3 for c in result['cases'])


@pytest.mark.parametrize('change',['missing','failed','no_truth','duplicate'])
def test_missing_or_failed_sector_cannot_be_hidden_by_favorable_neighbors(tmp_path,monkeypatch,change):
    manifest,rows=fixture(tmp_path,monkeypatch)
    if change=='missing':rows.pop(0)
    if change=='failed':rows[0]['passed']=False
    if change=='no_truth':rows[4]['truth_in_sector']=False
    if change=='duplicate':rows[0]['task']['sector']=1
    result=worker.comparison(manifest,rows)
    assert not result['all_cases_twofold'] and not result['cases'][0]['complete']
