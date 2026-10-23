# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
import pytest


def audit():
    path=Path(__file__).resolve().parents[2]/'docs/ilvis0-truth-probes/audit_results.py'
    spec=importlib.util.spec_from_file_location('_truth_output_audit',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_independent_check_compares_with_the_actual_nonzero_observations():
    raw=dict(status=0,point=[0]*27,prediction=[[100.5,200,1000],[102,202,1000]])
    result=audit().recompute_native(raw,dict(point=[0]*27),[[100,200,1000]],[102,202,1000],[1,1,1])
    assert result['feasible'] and result['training_max_axis_exact']==['1/2','0','0']
    assert result['future_change_exact']==['0','0','0']


def test_mismatched_or_failed_native_records_are_not_accepted():
    module=audit();raw=dict(status=0,point=[0]*27,prediction=[[0,0,0],[0,0,0]])
    with pytest.raises(ValueError):module.recompute_native(raw,dict(point=[.1]*27),[[0,0,0]],[0,0,0],[1,1,1])
    raw['status']=3
    with pytest.raises(ValueError):module.recompute_native(raw,dict(point=[0]*27),[[0,0,0]],[0,0,0],[1,1,1])
