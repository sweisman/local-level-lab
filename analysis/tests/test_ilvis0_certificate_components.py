# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import pytest
from lll.ilvis0_certificate_components import decompose


def test_exact_known_support_and_each_coordinate_are_retained():
    # max(2*x-y), x+y<=3, in [0,4]^2. Supplied dual is valid,
    # but deliberately not optimal: this is an accounting check, not a solver.
    result=decompose([0,0],[4,4],[[1,1]],[3],[2,-1],[1],7)
    assert F(result['center_value'])==2
    assert list(map(F,result['constraint_terms']))==[-1]
    assert list(map(F,result['box_terms']))==[2,4]
    assert F(result['total'])==7
    assert result['midpoint_feasible'] is False


def test_zero_dual_and_fixed_coordinate():
    result=decompose([1,-2],[1,3],[],[],[-2,3],[],7)
    assert list(map(F,result['box_terms']))==[0,F(15,2)]
    assert F(result['total'])==7


def test_exact_rational_inputs_do_not_round_to_binary():
    result=decompose([F(1,3)],[F(2,3)],[],[],[3],[],2)
    assert F(result['center_value'])==F(3,2)
    assert F(result['box_terms'][0])==F(1,2)


@pytest.mark.parametrize('change',['weight','missing_column','bound','nonfinite','wrong_total'])
def test_invalid_or_changed_certificate_rejected(change):
    args=[[0,0],[4,4],[[1,1]],[3],[2,-1],[1],7]
    if change=='weight':args[5]=[-1]
    if change=='missing_column':args[2]=[[1]]
    if change=='bound':args[1]=[-1,4]
    if change=='nonfinite':args[4]=[float('nan'),-1]
    if change=='wrong_total':args[6]=8
    with pytest.raises(ValueError):decompose(*args)
