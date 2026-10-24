# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only gate and charge checks; no numerical library or native call."""
import importlib

import pytest


def library():return importlib.import_module('lll.airquantumgrav_geographic_report')


def constant(value):
    return dict(rms_neu_m=[value,0.,0.],horizontal_rms_m=value,vertical_rms_m=0.,
        maximum_3d_m=value,total_rms_m=value)


def fixture(method,coarse,fine,passed):
    recipe=dict(queries=2,refinement_factor=dict(left_hold=.6,right_hold=.6,linear_points=.4),
        refinement_allowance_m=.001,linear_accuracy=dict(horizontal_rms_m=1.,vertical_rms_m=1.,maximum_3d_m=5.))
    result=dict(method=method,coarse=constant(coarse),fine=constant(fine),refinement_passed=True,
        accuracy_required=method=='linear_points',accuracy_checks=dict(horizontal_rms_m=coarse<=1.,
            vertical_rms_m=True,maximum_3d_m=coarse<=5.),passed=passed)
    phases=[dict(errors_neu_m=[[v,0.,0.]]*2,metrics=constant(v)) for v in (coarse,fine)]
    return recipe,result,phases


def test_hold_rule_can_pass_refinement_while_failing_absolute_accuracy():
    r,result,phases=fixture('left_hold',100.,50.,True)
    checked=library().case_gate(result,phases,r)
    assert checked['passed'] and not checked['absolute_accuracy']
    assert not checked['accuracy_required']


def test_linear_points_must_pass_accuracy_as_well_as_refinement():
    r,result,phases=fixture('linear_points',100.,25.,False)
    checked=library().case_gate(result,phases,r)
    assert not checked['passed'] and checked['refinement_passed'] and checked['accuracy_required']


@pytest.mark.parametrize('fault',['label','metric','accuracy','refinement'])
def test_saved_gate_rejects_changed_labels_and_error_summaries(fault):
    r,result,phases=fixture('linear_points',.1,.025,True)
    if fault=='label':result['passed']=False
    elif fault=='metric':phases[0]['metrics']['horizontal_rms_m']=1.
    elif fault=='accuracy':result['accuracy_checks']['vertical_rms_m']=False
    else:result['refinement_passed']=False
    with pytest.raises(ValueError):library().case_gate(result,phases,r)


def test_construction_journal_is_verified_against_the_frozen_limits(tmp_path):
    from lll.studies.journal import Journal
    path=tmp_path/'journal.sqlite';limits=dict(constructed_intervals=2,generated_samples=3)
    j=Journal(path,freeze='freeze',limits={'case':limits});j.start('case')
    for key,value in limits.items():j.reserve('case',key,value)
    assert library().construction_counts(path.read_bytes(),'freeze','case',limits)==limits
    with pytest.raises(ValueError):library().construction_counts(path.read_bytes(),'freeze','case',
        dict(constructed_intervals=3,generated_samples=3))
