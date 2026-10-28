# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import pytest


def fixture():
    names=['time_offset']+['p'+str(i) for i in range(26)];r=[1.,2.,3.];j=[[0.]*27 for _ in r]
    cell=dict(index=0,linear={'linear_success':True},point=[0.]*27,residual=r,jacobian=j,actual_cost=14.,
        relative_cost_change=0.,fresh_stationarity=0.,position_delta_neu_m=[[0.,0.,0.]],
        position_rms_neu_m=[0.,0.,0.],position_max_abs_neu_m=[0.,0.,0.],
        cost_stable=True,stationary=True,position_stable=True,passed=True)
    probe=dict(passed=True,cells=[cell],linear_solves=1)
    return dict(version='ilvis0-timing-cell-verification-v1',active_parameters=names,
        normalized_parameters=[0.]*27,residual_sum_squares=14.,
        local_linearization=dict(residual=r,jacobian=j),near_zero_probe=None,
        stability_probe=probe,ordinary_stability_probe=probe,timing_geometry=[{'cells':[{}]}],
        maximum_evaluations=200,evaluations=4,linear_solves=2,optimizer_linear_solves=1,
        final_verification_reserve=36,converged=True,stability_verified=True)


def test_native_timing_verification_audit_recomputes_full_cell_metrics():
    from lll.timing_optimizer_native_report import audit_verification
    report=audit_verification(fixture())
    assert report['passed'] and report['cells']==1 and report['columns']==27


@pytest.mark.parametrize('change',['cost','position','count','columns','missing'])
def test_native_timing_verification_audit_rejects_forged_or_omitted_checks(change):
    from lll.timing_optimizer_native_report import audit_verification
    f=copy.deepcopy(fixture())
    if change=='cost':f['stability_probe']['cells'][0]['actual_cost']+=1.
    elif change=='position':f['stability_probe']['cells'][0]['position_rms_neu_m'][0]=1.
    elif change=='count':f['linear_solves']+=1
    elif change=='columns':f['stability_probe']['cells'][0]['jacobian'][0].pop()
    else:f['stability_probe']['cells']=[]
    with pytest.raises(ValueError):audit_verification(f)


def test_native_timing_audit_keeps_genuine_stationarity_failure_unresolved():
    from lll.timing_optimizer_native_report import audit_verification
    f=fixture();f.update(converged=False,stability_verified=False,linear_solves=1,
        stability_probe={'passed':False,'reason':'not_stationary','cells':[],'linear_solves':0})
    assert audit_verification(f)['passed'] is False


def test_native_timing_failure_description_exposes_distant_anchor_without_refitting():
    from lll.timing_optimizer_native_report import describe_failures
    f=fixture();f['stability_probe']['cells'][0].update(passed=False,cost_stable=False)
    f['timing_geometry'][0]['cells'][0]=dict(lower=0.,upper=1.,anchor=.5)
    rows=describe_failures(f,time_scale=.01)
    assert len(rows)==1 and rows[0]['anchor_distance_s']==pytest.approx(.005)
    assert rows[0]['cost_stable'] is False and rows[0]['position_stable'] is True
