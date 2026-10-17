# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest
from test_ilvis0_trust_trial_worker import fixture


def worker():
    import ilvis0_timing_trial_worker
    return ilvis0_timing_trial_worker


def population():
    parent,summary=fixture();sid='fd7b81e48a4122b149c4925b'
    parent['plan']['target_segment_ids'][-1]=sid
    for t in parent['plan']['tasks']:
        if t['segment_id']=='c':
            old=t['identity'];t['segment_id']=sid;t['identity']=old.replace('c::',sid+'::',1)
            summary['results'][t['identity']]=summary['results'].pop(old)
    return parent,summary


def test_four_starts_fixed_488_call_ceiling_and_primary_seed_for_repeat():
    parent,summary=population();original=copy.deepcopy(parent)
    plan=worker().make_plan(parent,summary)
    assert len(plan['tasks'])==4 and plan['maximum_starts']==4
    assert sum(t['maximum_evaluations']+2 for t in plan['tasks'])==plan['maximum_native_sweeps']==488
    assert {t['segment_id'] for t in plan['tasks'] if t['role']!='control'}=={worker().TARGET}
    repeat=next(t for t in plan['tasks'] if t['role']=='repeat')
    assert repeat['reference']['normalized_parameters']==[.1]
    assert parent==original


def test_changed_evaluation_ceiling_or_missing_target_is_rejected():
    parent,summary=population();parent['plan']['tasks'][-2]['maximum_evaluations']+=1
    with pytest.raises(ValueError):worker().make_plan(parent,summary)
    parent,summary=population();parent['plan']['tasks']=[t for t in parent['plan']['tasks'] if t['role']!='repeat']
    with pytest.raises(ValueError):worker().make_plan(parent,summary)
