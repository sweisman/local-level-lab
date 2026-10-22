# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from fractions import Fraction as F
from pathlib import Path

import pytest


def module():
    p=Path(__file__).resolve().parents[2]/'docs/ilvis0-long-staged-feasibility-v2/audit_linear_leverage.py'
    spec=importlib.util.spec_from_file_location('_leverage_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_known_unobserved_direction_has_exact_feasible_forecast_spread():
    calls=[];value=module();left=value.probe([[1.,0.]],[0.,2.],-1,1.,lambda:calls.append(1))
    right=value.probe([[1.,0.]],[0.,2.],1,1.,lambda:calls.append(1))
    assert len(calls)==2 and F(right['future_change_m'])-F(left['future_change_m'])==4
    assert left['feasible'] and right['feasible']


def test_witness_has_exact_box_and_training_feasibility():
    result=module().probe([[10.,3.]],[1.,2.],1,.01,lambda:None)
    point=list(map(F,result['point']))
    assert all(abs(v)<=1 for v in point)
    assert abs(10*point[0]+3*point[1])<=F(.01)
    assert F(result['future_change_m'])==point[0]+2*point[1]


def test_invalid_design_is_rejected_without_spending_a_proposal():
    def reserve():pytest.fail('invalid input spent a proposal')
    with pytest.raises(ValueError):module().probe([[1.,2.]],[1.],1,1.,reserve)
