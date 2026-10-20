# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll.ilvis0_rotation_interval import vertical_interval


@pytest.mark.parametrize('sign',[-1,1])
def test_value_only_closure_needs_no_claim_about_taylor_coefficients(sign):
    eps=F(1,1000);a=[0,0,sign];lo=[-eps,0,-eps];hi=[eps,0,eps]
    result=vertical_interval(a,a,lo,hi,norm_identity=True)
    left=F(result['raw_lower']);right=F(result['raw_upper'])
    assert right-left<F(1,1000000)
    for t in np.linspace(-1,1,65):
        actual=sign*(np.cos(.001*t)-1)
        assert float(left)-2e-15<=actual<=float(right)+2e-15
    assert result['taylor_remainder_qualified'] is False


def test_wider_geometric_result_does_not_replace_a_tighter_input():
    a=[0,0,-1];result=vertical_interval(a,a,[-.01,-.01,-1e-9],[.01,.01,1e-9],norm_identity=True)
    assert F(result['combined_lower'])>=F(-1e-9) and F(result['combined_upper'])<=F(1e-9)
    assert F(result['raw_upper'])>F(1e-9)


def test_source_identity_and_sign_branch_are_required():
    with pytest.raises(ValueError,match='identity'):vertical_interval([0,0,-1],[0,0,-1],[-.1]*3,[.1]*3)
    with pytest.raises(ValueError,match='branch'):vertical_interval([0,0,-1],[0,0,-1],[-2]*3,[2]*3,norm_identity=True)


def test_a_declared_norm_defect_is_propagated_without_normalizing_inputs():
    a=[0,0,-1];b=[0,0,.0001]
    result=vertical_interval(a,a,b,b,norm_identity=True,norm_error=F(1,5000))
    assert F(result['combined_lower'])==F(result['combined_upper'])==F(.0001)
    with pytest.raises(ValueError):vertical_interval(a,a,b,b,norm_identity=True,norm_error=-1)
