# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def module():
    from lll import ilvis0_projected_fullcal as fullcal
    return fullcal


def test_complete_task_identity_and_case_pairs():
    rows=module().tasks()
    assert len(rows)==len({r['identity'] for r in rows})==24
    assert {r['case_id'] for r in rows}=={'bias1_unsubtracted','bias1_profiled_removal'}
    assert all(r['clock']=='nominal' for r in rows)
    assert len({(r['model'],r['case_id'],tuple(r['axes'])) for r in rows})==12


@pytest.mark.parametrize('profile',[False,True])
def test_all_calibration_columns_truth_and_starts_remain_feasible(profile):
    from lll import ilvis0_geographic_controls as geographic
    q=module();task=next(r for r in q.tasks() if r['profile']==profile and r['start']=='zero')
    f=geographic.fixture(task['model'],'nominal');p=q.problem(task,f,None,None)
    assert len(p.bounds.active)==26+int(profile)
    truth=q.truth_point(task,f,p);p.bounds.decode(truth)
    assert p.bounds.decode(truth)['gyro_bias_z']==pytest.approx(f['truth']['gyro_bias_z'])
    if profile:assert truth[-1]==-1. and p.bounds.decode(truth)['earth_removal']==0.
    zero=q.start(task,p);p.bounds.decode(zero)
    other=q.start(dict(task,start='opposed'),p);p.bounds.decode(other)
    assert all(abs(v)<=1 for v in other)
    if profile:assert zero[-1]==-1. and other[-1]==-.8


def test_different_processing_cases_cannot_form_a_repeat_pair():
    assert not module().compare_pair(dict(case_id='a'),dict(case_id='b'))['passed']
