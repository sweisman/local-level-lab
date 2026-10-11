# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def module():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-geographic-controls-20261011/audit_calibration.py'
    spec=importlib.util.spec_from_file_location('geographic_calibration_audit',path)
    result=importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def test_saved_parameter_errors_and_weak_directions_are_not_prediction_success():
    row=dict(identity='control',truth={'gyro_bias_z':.25,'gyro_gain_z':.005},
        passed=True,maximum_position_error_m=1e-6,
        fit=dict(parameters={'gyro_bias_z':.9,'gyro_gain_z':.004},
            active_parameters=['gyro_bias_z','gyro_gain_z'],active_bounds=[],
            singular_values=[10.,1e-7],right_singular_vectors=[[0.,1.],[1.,0.]],converged=True))
    report=module().audit({'results':[row]},dict(gyro_bias_z=1.,gyro_gain_z=.02))
    assert report['largest_normalized_parameter_error']==pytest.approx(.65)
    assert report['weak_direction_dominant_counts']=={'gyro_bias_z':1}
    assert report['parameter_rows'][0]['error_bound_units']==pytest.approx(.65)
    assert report['fit_rows'][0]['numerical_rank']==1
    assert report['observed_fit_starts']==report['native_sweeps']==0


def test_missing_truth_parameter_does_not_silently_pass_saved_audit():
    row=dict(identity='broken',truth={'gyro_bias_z':.25},fit=dict(parameters={},converged=True))
    with pytest.raises(ValueError): module().audit({'results':[row]},dict(gyro_bias_z=1.))
