# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib
import importlib.util

import pytest


def planner():
    name='lll.ilvis0_hybrid_remaining_plan'
    assert importlib.util.find_spec(name), 'bounded six-target planner is missing'
    return importlib.import_module(name)


def test_saved_population_and_budget_are_exact():
    import json
    from pathlib import Path
    root=Path(__file__).resolve().parents[2]/'docs/ilvis0-remaining-precision-20261014'
    parent=json.loads((root/'manifest.json').read_text());summary=json.loads((root/'summary.json').read_text())
    plan,reused=planner().build(parent,summary)
    assert len(plan['target_segment_ids'])==6
    assert len(reused)==25 and all(f['converged'] for f in reused.values())
    assert plan['maximum_starts']==24 and plan['maximum_native_sweeps']==4528
    assert len({t['identity'] for t in plan['tasks']})==24
    for task in plan['tasks']:
        if task['role']=='repeat':
            primary=next(t for t in plan['tasks'] if t['identity']==task['identity'].rsplit('::',1)[0]+'::primary')
            assert task['reference']==primary['reference']


def repeat_fixture():
    tasks=[dict(identity='a::c::'+m+'::repeat',segment_id='a',role='repeat') for m in ('first','second')]
    raw=dict(qualified=False,controls_passed=True,repeatability=[dict(identity=t['identity'],passed=i==1) for i,t in enumerate(tasks)])
    return dict(tasks=tasks,target_segment_ids=['a']),raw


def test_one_failed_pair_cannot_be_overwritten_by_a_passing_pair():
    plan,raw=repeat_fixture();result=planner().aggregate_repeatability(plan,raw)
    assert not result['repeatability'][0]['passed'] and not result['qualified']
    assert len(result['pair_repeatability'])==2


def test_missing_or_duplicate_pair_cannot_qualify():
    for duplicate in (False,True):
        plan,raw=repeat_fixture()
        raw['repeatability']=raw['repeatability'][1:]
        if duplicate: raw['repeatability']*=2
        with pytest.raises(ValueError): planner().aggregate_repeatability(plan,raw)
