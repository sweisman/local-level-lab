# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import pytest
import ilvis0_coupled_subdivision_worker as worker


def fixture(tmp_path,monkeypatch):
    monkeypatch.setattr(worker,'DATA',tmp_path);parents=[];baseline=[];before=[];rows=[]
    for model in range(3):
        for profile in (False,True):
            baseline.append(dict(model=model,profile=profile,union_width_m=[2.]*3))
            before.append(dict(model=model,profile=profile,union_width_m=[1.5]*3))
            for sector in range(8):
                parent=f'p-{model}-{int(profile)}-{sector}'
                parents.append(dict(identity=parent,model=model,profile=profile,sector=sector,children=4))
                for child in range(4):
                    rows.append(dict(identity=parent+f'-xy-{child}',passed=True,excluded=False,
                        truth_in_child=sector==0,known_truth_retained=True,
                        future_lower_m=[0.]*3,future_upper_m=[.25*(child+1)]*3))
    payloads={'cover':dict(parents=parents,identities=192),'baseline':dict(cases=baseline),'previous-comparison':dict(cases=before)}
    for key,value in payloads.items():(tmp_path/(key+'.json')).write_text(json.dumps(value))
    manifest=dict(inputs={key:dict(path=key+'.json') for key in payloads})
    return manifest,rows


def test_all_cells_contribute_to_the_outward_union_and_shared_boundary_checks(tmp_path,monkeypatch):
    manifest,rows=fixture(tmp_path,monkeypatch);result=worker.comparisons(manifest,rows)
    assert result['all_cases_twofold'] and len(result['cases'])==6
    for case in result['cases']:
        assert case['union_width_m']==[1.]*3 and case['expected_cells']==32
        assert case['truth_containing_cells']==4


@pytest.mark.parametrize('change',['missing','failed','no-truth'])
def test_incomplete_or_failed_covers_cannot_pass_on_favorable_surviving_cells(tmp_path,monkeypatch,change):
    manifest,rows=fixture(tmp_path,monkeypatch)
    if change=='missing':rows.pop(3)
    elif change=='failed':rows[3]['passed']=False
    else:
        for row in rows:row['truth_in_child']=False
    result=worker.comparisons(manifest,rows)
    assert not result['all_cases_twofold']
    assert not result['cases'][0]['complete'] and not result['cases'][0]['twofold']
