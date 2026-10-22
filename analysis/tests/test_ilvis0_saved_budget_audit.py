# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from lll.ilvis0_saved_budget_audit import budget_row


def test_evaluator_loads_under_shared_workers_standalone_module_name():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_saved_budget_audit.py'
    spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.budget_row(material())['prior_useful'] is False


def material():
    return dict(identity='case',result=dict(model=0,profile=False,useful=False,
        numerical_checks_passed=True,future_width_m=[100,200,300]),
        certificate=dict(time_s=438,position_unshared_remainder=[9,18,27],
            lever_unshared_remainder=[1,2,3],unshared_remainder=[10,20,30]),
        result_sha256='a'*64,bound_sha256='b'*64)


def test_saved_budget_share_does_not_relabel_failed_prediction():
    row=budget_row(material())
    assert row['position_share']==[0.9,0.9,0.9]
    assert row['prior_useful'] is False
    assert row['future_width_m']==[100,200,300]


def test_components_must_reconstruct_saved_total():
    value=material();value['certificate']['unshared_remainder'][0]=12
    with pytest.raises(ValueError,match='components'):budget_row(value)


@pytest.mark.parametrize('bad',[float('nan'),-1])
def test_invalid_allowance_is_rejected(bad):
    value=material();value['certificate']['position_unshared_remainder'][0]=bad
    with pytest.raises(ValueError):budget_row(value)
