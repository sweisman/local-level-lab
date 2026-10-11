# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
import importlib.util
import json
import math
from pathlib import Path

import pytest


def audit():
    from lll import ilvis0_prediction_audit
    return ilvis0_prediction_audit


def epochs():
    return [dict(epoch=i,time_s=float(i),role='training' if i<3 else 'prediction',
        north_direct_error_m=3.*i,east_direct_error_m=4.*i,up_direct_error_m=-2.*i)
        for i in range(7)]


def test_growth_windows_preserve_counts_and_signed_endpoint():
    out=audit().error_growth(epochs(),3,window_seconds=2)
    assert out['training']['horizontal_rms_m']==pytest.approx(5*math.sqrt(5/3))
    assert out['prediction']['horizontal_rms_m']==pytest.approx(5*math.sqrt(86/4))
    assert out['prediction']['endpoint_horizontal_m']==30
    assert out['prediction']['endpoint_up_m']==-12
    assert [w['epochs'] for w in out['windows']]==[2,2]
    assert [w['offset_start_s'] for w in out['windows']]==[0,2]
    assert not out['windows_are_independent_trials']
    assert out['optimizer_starts']==out['native_predictions']==0


@pytest.mark.parametrize('fault',['role','order','epoch','nonfinite','missing'])
def test_invalid_epoch_records_rejected(fault):
    rows=epochs()
    if fault=='role': rows[3]['role']='training'
    if fault=='order': rows[3]['time_s']=1.
    if fault=='epoch': rows[3]['epoch']=2
    if fault=='nonfinite': rows[3]['north_direct_error_m']=float('nan')
    if fault=='missing': del rows[3]['up_direct_error_m']
    with pytest.raises(ValueError): audit().error_growth(rows,3)


def test_conditioning_does_not_promote_unfinished_fit():
    fit=dict(converged=False,solver_reported_success=False,
        exact_projected_gradient_relative=.004,stationarity_tolerance=1e-4,
        singular_values=[5e4,.001],active_parameters=['a','b'])
    out=audit().conditioning(fit)
    assert out['status']=='unresolved' and out['stationarity_ratio']==40
    assert out['jacobian_condition_ratio']==5e7
    assert out['parameter_coupling_identified'] is False
    zero=copy.deepcopy(fit); zero['singular_values']=[1.,0.]
    assert audit().conditioning(zero)['jacobian_condition_ratio'] is None


def test_parameter_comparison_preserves_limits_and_units():
    case=dict(profile=False,limits={'gyro_gain_z':.02,'gyro_bias_z':math.pi/648000})
    fit=dict(active_parameters=['gyro_gain_z','gyro_bias_z'],normalized_parameters=[-1.,1.],
        parameters=dict(gyro_gain_z=-.02,gyro_bias_z=math.pi/648000),
        active_bounds=['gyro_gain_z','gyro_bias_z'])
    old=copy.deepcopy(fit); old.update(normalized_parameters=[0.,0.],
        parameters=dict(gyro_gain_z=0.,gyro_bias_z=0.),active_bounds=[])
    rows=audit().parameter_changes(fit,old,case)
    assert rows[0]['training_value']==-2 and rows[0]['unit']=='%'
    assert rows[1]['training_value']==pytest.approx(1.)
    assert rows[1]['full_window_boundary']=='interior'
    assert rows[1]['training_boundary']=='upper'
    assert rows[1]['change']==pytest.approx(1.)
    bad=copy.deepcopy(fit); bad['parameters']['gyro_gain_z']=.02
    with pytest.raises(ValueError): audit().parameter_changes(bad,old,case)


def renderer():
    source=Path(__file__).resolve().parents[2]/'docs/ilvis0-prediction-audit-20261011/build_report.py'
    spec=importlib.util.spec_from_file_location('prediction_audit_report',source)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_corrupt_publication_is_rejected_before_any_output(tmp_path):
    source=tmp_path/'source'; source.mkdir()
    (source/'summary.json').write_text('{}')
    (source/'evidence-receipt.json').write_text(json.dumps({'artifacts':{'summary.json':'bad'}}))
    output=tmp_path/'output'
    with pytest.raises(ValueError,match='hash'): renderer().build(source,tmp_path/'clock',output)
    assert not output.exists()
