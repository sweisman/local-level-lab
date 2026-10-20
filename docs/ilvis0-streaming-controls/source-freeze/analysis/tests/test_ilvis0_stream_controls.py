# SPDX-License-Identifier: AGPL-3.0-or-later
from lll import ilvis0_stream_controls as controls


def test_finite_plan_has_unique_identities_and_all_models_modes():
    tasks=controls.tasks()
    assert len(tasks)==48 and len({t['identity'] for t in tasks})==48
    assert {t['model'] for t in tasks if t['kind']=='equivalence'}=={0,1,2}
    assert {t['tangent'] for t in tasks}=={False,True}
    assert {t['profile'] for t in tasks if t['kind']=='equivalence'}=={False,True}


def test_small_real_worker_control_returns_counted_comparison(tmp_path):
    charged=[]
    task=next(t for t in controls.tasks() if t['kind']=='equivalence')
    result=controls.evaluate(task,tmp_path,lambda **counts:charged.append(counts))
    assert result['passed'] and result['chunk_bit_identical']
    assert sum(c['packet_visits'] for c in charged)==3*task['packets']
    assert all(c['native_calls']==1 for c in charged)
