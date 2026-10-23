# SPDX-License-Identifier: AGPL-3.0-or-later
from pathlib import Path
import importlib.util
import pytest


def audit():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-ray-probes/audit_results.py'
    spec=importlib.util.spec_from_file_location('_independent_ray_audit',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_audit_recomputes_exact_training_maxima_and_future_difference():
    baseline=[[0,0,0]]*3;actual=[[.25,-.5,0],[-.5,.25,0],[2,-3,4]]
    result=audit().recompute(actual,baseline,[0]*27,[2,3,1])
    assert result['training_max_axis_exact']==['1','3/2','0']
    assert not result['feasible']
    assert result['future_change_exact']==['4','-9','4']


def test_audit_rejects_missing_parameter_columns_and_nonfinite_positions():
    module=audit();base=[[0,0,0]]*2
    with pytest.raises(ValueError):module.recompute(base,base,[0]*26,[1,1,1])
    with pytest.raises(ValueError):module.recompute([[0,0,0],[float('nan'),0,0]],base,[0]*27,[1,1,1])


def test_audit_does_not_change_feasibility_when_only_the_future_changes():
    module=audit();base=[[0,0,0]]*2
    first=module.recompute([[.5,.5,.5],[0,0,0]],base,[0]*27,[1,1,1])
    second=module.recompute([[.5,.5,.5],[1000,1000,1000]],base,[0]*27,[1,1,1])
    assert first['feasible'] and second['feasible']
    assert first['training_max_axis_exact']==second['training_max_axis_exact']
