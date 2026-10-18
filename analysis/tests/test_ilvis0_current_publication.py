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


def test_later_saved_review_updates_only_its_declared_unresolved_stretch():
    from test_ilvis0_boundary_publication import example
    review, _ = example()
    rows = {'s': dict(shape_preference='unresolved'),
            'earlier': dict(shape_preference='globe', result_origin='earlier')}
    publication().apply_boundary_review(rows, review, 'later')
    assert rows['s']['shape_preference'] == 'globe'
    assert rows['s']['result_origin'] == 'later'
    assert rows['earlier'] == dict(shape_preference='globe', result_origin='earlier')


def test_later_review_cannot_overwrite_an_already_resolved_comparison():
    from test_ilvis0_boundary_publication import example
    review, _ = example()
    with pytest.raises(ValueError):
        publication().apply_boundary_review({'s':dict(shape_preference='globe')}, review, 'later')


def test_failing_repeat_keeps_a_later_publication_unresolved():
    from test_ilvis0_boundary_publication import example
    review, _ = example()
    review['pairs'][0].update(passed=False, relative_cost_difference=.01)
    rows = {'s':dict(shape_preference='unresolved')}
    publication().apply_boundary_review(rows, review, 'later')
    assert rows['s']['shape_preference'] == 'unresolved'


def test_current_publication_includes_complete_final_stretch_review_last():
    report=publication()
    assert report.REVIEWS[-1]=='docs/ilvis0-last-review-20261018'
    assert len(set(report.REVIEWS))==len(report.REVIEWS)


def test_final_review_checks_exact_public_source_snapshot_instead_of_live_runtime():
    report=publication();name='data/ilvis0-boundary-diagnostic-20261016/manifest.json'
    sources={name:'sealed-hash','analysis/lll/ilvis0_shape.py':'source-hash'}
    expected='docs/ilvis0-last-zero-boundary-20261018/source-freeze/'+name
    assert report.published_sources(report.FINAL,sources)=={
        expected:'sealed-hash','analysis/lll/ilvis0_shape.py':'source-hash'}
    assert report.published_sources(report.SCALED,sources)==sources
