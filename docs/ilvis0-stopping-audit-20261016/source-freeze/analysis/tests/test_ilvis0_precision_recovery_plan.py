# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select failure classes, never favorable costs or model rankings."""
import copy
import pytest
from lll import ilvis0_precision_recovery_plan as planning


def fixture(gate='relative_cost', repeat_failed=False):
    probe=dict(actual_cost_change=2e-8, fresh_stationarity=1e-8,
               position_rms_neu_m=[1e-6]*3, position_max_abs_neu_m=[1e-5]*3,
               position_rms_tolerance_m=.001, position_max_tolerance_m=.01)
    fit=dict(converged=False, case_id=planning.CASES[0], model=planning.MODELS[0],
             exact_projected_gradient_relative=1e-8, stationarity_tolerance=1e-4,
             stability_probe=probe)
    if gate=='stationarity': fit['exact_projected_gradient_relative']=.01
    if gate=='position': probe['position_rms_neu_m'][2]=.002
    if gate=='missing': fit.pop('stability_probe')
    cases=[]
    for c in planning.CASES:
        fits=[]
        for m in planning.MODELS:
            f=copy.deepcopy(fit);f.update(case_id=c,model=m,converged=repeat_failed or (c,m)!=(planning.CASES[0],planning.MODELS[0]))
            fits.append(f)
        cases.append(dict(case_id=c,fits=fits))
    repeat=copy.deepcopy(fit);repeat['converged']=not repeat_failed
    identity='target::'+planning.CASES[0]+'::'+planning.MODELS[0]+'::repeat'
    recovery=dict(state='complete',comparisons=[dict(segment_id='target',cases=cases,
        profile=dict(conditional_shape_preference='unresolved'))],results={identity:repeat},
        qualification=dict(controls_passed=True,repeatability=[dict(identity=identity,passed=not repeat_failed)]))
    trial=dict(state='complete',qualification=dict(qualified=True),comparisons=[])
    manifest=dict(proposal=dict(tasks=[dict(segment_id='target',identity=identity,case_id=planning.CASES[0],model=planning.MODELS[0],role='repeatability')]))
    return recovery,trial,manifest


@pytest.mark.parametrize('repeat_failed',[False,True])
def test_only_cost_failures_selected_including_repeat_only(repeat_failed):
    plan=planning.build(*fixture(repeat_failed=repeat_failed))
    assert plan['target_segment_ids']==['target']
    assert plan['maximum_starts']==9
    assert plan['maximum_native_sweeps']==538
    assert len({t['identity'] for t in plan['tasks']})==9
    assert sum(t['role']=='repeat' for t in plan['tasks'])==1


@pytest.mark.parametrize('gate',['stationarity','position','missing'])
def test_other_failure_classes_excluded(gate):
    inventory=planning.classify(*fixture(gate=gate))
    assert len(inventory)==1 and not inventory[0]['eligible']
    with pytest.raises(ValueError,match='no cost-only'): planning.build(*fixture(gate=gate))


def test_failed_agreement_not_reclassified_as_cost_only():
    args=fixture();args[0]['qualification']['repeatability'][0]['passed']=False
    assert not planning.classify(*args)[0]['eligible']


def test_agreement_unavailable_when_its_primary_failed_requires_fresh_repeat():
    args=fixture();args[0]['qualification']['repeatability']=[]
    assert planning.classify(*args)[0]['eligible']


def test_no_selection_from_cost_values_and_preserve_inputs():
    args=fixture();before=copy.deepcopy(args)
    first=planning.build(*args)
    assert args==before
    for c in args[0]['comparisons'][0]['cases']:
        for f in c['fits']: f['residual_sum_squares']=1e99 if f['model']=='flat_still' else 0
    assert planning.build(*args)==first


def test_completed_trial_targets_excluded():
    args=fixture();args[1]['comparisons']=[dict(segment_id='target',profile=dict(conditional_shape_preference='globe'))]
    assert planning.classify(*args)==[]


def test_incomplete_or_unqualified_dependency_rejected():
    args=fixture();args[1]['qualification']['qualified']=False
    with pytest.raises(ValueError): planning.build(*args)
