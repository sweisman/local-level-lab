# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
import ilvis0_timing_worker as worker


def fixture():
    ids=[worker.CONTROL,worker.PREFIX+'primary',worker.PREFIX+'repeat']
    parent={'plan':{'tasks':[dict(identity=i) for i in ids]}}
    results={i:dict(converged=i==worker.CONTROL) for i in ids}
    audit={'results':[dict(identity=i,audit={'methods':[dict(method='original_bvls',step=[.1])]}) for i in ids[1:]]}
    return parent,{'results':results},audit


def test_fixed_three_endpoints_and_exact_34_call_scope():
    tasks=worker.select_tasks(*fixture())
    assert [t['maximum_native_evaluations'] for t in tasks]==[10,12,12]
    assert sum(t['maximum_native_evaluations'] for t in tasks)==34
    assert [t['correction'] for t in tasks]==[None,[.1],[.1]]


def test_control_and_failed_labels_are_required():
    parent,summary,audit=fixture();summary['results'][worker.CONTROL]['converged']=False
    with pytest.raises(ValueError):worker.select_tasks(parent,summary,audit)
