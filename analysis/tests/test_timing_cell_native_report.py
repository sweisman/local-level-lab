# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import numpy as np
import pytest


def fixture():
    from lll.timing_cell_native_probe import probe
    from test_timing_cell_native_probe import fixture as inputs
    point,options=inputs()
    d=probe(lambda p,**kw:(np.ones(6),np.zeros((6,27)),0),point,
        reserve=lambda **k:None,check_continue=lambda:None,physical_step=lambda d:d.reshape(2,3),**options)
    d.update(source_fit_sha256='a'*64,original_saved_converged=False,input_replay_exact=True)
    record=dict(identity='saved-point',saved_converged=False,proposals=options['proposals'],
        fit=dict(active_parameters=options['active'],normalized_parameters=point.tolist(),residual_sum_squares=6.,
            local_linearization=options['expected_linearization']),artifact_sha256={'fit.json':'a'*64})
    return record,d


def test_native_cell_report_recomputes_metrics_without_relabeling_failed_fits():
    from lll.timing_cell_native_report import summarize
    record,d=fixture();row,proposals=summarize(record,d)
    assert row['original_fit_converged'] is False and len(proposals)==6 and row['evaluations']==8
    assert all(p['cost_stable'] and p['position_stable'] for p in proposals)
    assert 'converged' not in row and not row['labels_changed']


@pytest.mark.parametrize('change',['source','label','coverage','cost','physical','threshold','jacobian'])
def test_native_cell_report_rejects_forged_or_incomplete_results(change):
    from lll.timing_cell_native_report import summarize
    record,d=fixture();d=copy.deepcopy(d)
    if change=='source':d['source_fit_sha256']='b'*64
    elif change=='label':d['original_saved_converged']=True
    elif change=='coverage':d['proposals'].pop()
    elif change=='cost':d['proposals'][0]['actual_cost']+=1
    elif change=='physical':d['proposals'][0]['position_rms_neu_m'][0]=1.
    elif change=='threshold':d['thresholds']['relative_cost']=1.
    else:d['proposals'][0]['jacobian'][0].pop()
    with pytest.raises(ValueError):summarize(record,d)
