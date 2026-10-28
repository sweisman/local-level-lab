# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def fixture(kind='fit'):
    from lll.timing_stopping_study import case_table,run_case
    identity='fit-interior-start-0' if kind=='fit' else 'probe-ramp_zero'
    row=next(r for r in case_table() if r['identity']==identity);values=[]
    result=run_case(row,reserve_evaluation=lambda:None,reserve_linear=lambda:None,
        save_evaluation=values.append,check_continue=lambda:None)
    return row,result,values


@pytest.mark.parametrize('kind',['fit','probe'])
def test_timing_report_independently_checks_expected_fit_and_rejection(kind):
    from lll.timing_stopping_report import summarize
    row,result,values=fixture(kind);report=summarize(row,result,values)
    assert report['qualification_passed'] and report['kind']==kind
    assert report['accepted'] is (kind=='fit')
    assert report['evaluations']==len(values)


@pytest.mark.parametrize('change',['cost','convergence','trace','count','reference'])
def test_timing_report_rejects_forged_success_or_incomplete_trace(change):
    from lll.timing_stopping_report import summarize
    row,r,values=fixture();r=copy.deepcopy(r);values=copy.deepcopy(values)
    if change=='cost':r['fit']['residual_sum_squares']+=1
    elif change=='convergence':r['fit']['converged']=False
    elif change=='trace':values[0]['number']=0
    elif change=='count':r['evaluations']+=1
    else:row=copy.deepcopy(row);row['reference']['cost']=0.
    with pytest.raises(ValueError):summarize(row,r,values)
