# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

import pytest


def publication():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-current-findings-20261015/build_report.py'
    assert path.exists(), 'new publication builder is missing'
    spec=importlib.util.spec_from_file_location('new_publication',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def fixture():
    cases=[dict(case_id=c,fits=[dict(model=m,converged=True) for m in ('sphere_rotating','sphere_still','flat_still')])
           for c in ('bias1_unsubtracted','bias1_profiled_removal')]
    row=dict(segment_id='a',cases=cases,profile=dict(conditional_shape_preference='globe'))
    summary=dict(state='complete',comparisons=[row],qualification=dict(controls_passed=True,
        controls=[dict(passed=True),dict(passed=True)],repeatability=[dict(identity='a::case::model::repeat',passed=True)]))
    return {'a':'unresolved'},summary,dict(target_segment_ids=['a'])


def test_individual_success_survives_other_failed_fits():
    old,summary,plan=fixture();summary['qualification']['qualified']=False
    assert publication().qualified_updates(old,summary,plan)['a']['profile']['conditional_shape_preference']=='globe'


@pytest.mark.parametrize('failure',['control','repeat','primary','duplicate_model','resolved','population'])
def test_missing_required_check_cannot_promote(failure):
    old,s,p=fixture()
    if failure=='control': s['qualification']['controls_passed']=False
    if failure=='repeat': s['qualification']['repeatability'][0]['passed']=False
    if failure=='primary': s['comparisons'][0]['cases'][0]['fits'][0]['converged']=False
    if failure=='duplicate_model': s['comparisons'][0]['cases'][0]['fits'][0]['model']='flat_still'
    if failure=='resolved': old['a']='globe'
    if failure=='population': p['target_segment_ids'].append('b')
    with pytest.raises(ValueError): publication().qualified_updates(old,s,p)


@pytest.mark.parametrize('failure',['hidden_failure','missing_pair','extra_pair'])
def test_every_declared_repeat_pair_is_checked(failure):
    old,s,p=fixture()
    identities=['a::case::model::repeat','a::other::model::repeat']
    p['tasks']=[dict(identity=i,role='repeat') for i in identities]
    s['qualification']['pair_repeatability']=[dict(identity=i,passed=True) for i in identities]
    if failure=='hidden_failure': s['qualification']['pair_repeatability'][0]['passed']=False
    if failure=='missing_pair': s['qualification']['pair_repeatability'].pop()
    if failure=='extra_pair': s['qualification']['pair_repeatability'].append(dict(identity='a::extra',passed=True))
    with pytest.raises(ValueError): publication().qualified_updates(old,s,p)
