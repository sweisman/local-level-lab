# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from lll import ilvis0_column_orientation_prediction as candidate


def test_saved_support_uses_added_constraint_without_future_truth():
    lo=[-1.]*51;hi=[1.]*51;zero=[0.]*51;one=zero.copy();one[0]=1.
    region=dict(lower=lo,upper=hi,center=zero,coordinate_scale=[1.]*3,origin=[0.]*3,
        arithmetic_allowance=0.,inequality_design=[zero,one],inequality_upper=[0.,.25])
    bound=dict(previous_coefficients=[[0.]*6]*3,acceleration_coefficients=[[0.]*9]*3,
        transform_coefficients=[[0.]*9]*3,unshared_remainder=[0.]*3)
    cert=dict(upper_multipliers=[0.],lower_multipliers=[0.])
    saved=dict(nominal=[0.]*3,jacobian=[[1.]+[0.]*26,[0.]*27,[0.]*27],bound=bound,
        envelope=dict(certificates=[cert]*3,lower=[-1.,0.,0.],upper=[1.,0.,0.]))
    reservations=[]
    result=candidate.rebuild_future(region,saved,lo,hi,reserve=reservations.append)
    assert reservations==list(range(1,7))
    assert result['lower']==[-1.,0.,0.] and result['upper']==[.25,0.,0.]


def test_standalone_entry_does_not_need_a_package_relative_import():
    spec=importlib.util.spec_from_file_location('consistent_prediction_standalone',Path(candidate.__file__))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.evaluate)


def test_generated_case_reuses_inputs_without_native_calls(tmp_path,monkeypatch):
    from saved_prediction_fixtures import generated_context
    root=Path(__file__).resolve().parents[2]
    task,context,saved=generated_context(root/'docs/ilvis0-orientation-gain-prediction',tmp_path,monkeypatch)
    result=candidate.evaluate(task,context)
    assert result['passed'] and result['native_evaluations']==0
    assert result['exact_supports_checked']==6 and 'independent-audit.json' in saved
