# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction

import numpy as np
import pytest

from lll import ilvis0_training_box as boxes


def test_known_signed_intervals_are_conservative_and_tighter():
    result=boxes.contract([-1.,-1.],[1.,1.],[[2.,0.],[0.,-4.]],[.4,-2.],[.8,-1.])
    assert not result['empty']
    assert result['lower'][0]<=.2 and result['upper'][0]>=.4
    assert result['lower'][1]<=.25 and result['upper'][1]>=.5
    np.testing.assert_allclose(result['lower'],[.2,.25],atol=1e-14)
    np.testing.assert_allclose(result['upper'],[.4,.5],atol=1e-14)
    assert result['scientific_decision']=='abstain'


def test_zero_unidentified_columns_are_not_deleted():
    matrix=np.zeros((2,27));matrix[0,0]=1.;matrix[1,20]=-1.
    result=boxes.contract(np.full(27,-1.),np.full(27,1.),matrix,[.2,-.3],[.3,-.2])
    assert len(result['lower'])==27
    indices=[i for i in range(27) if i not in (0,20)]
    np.testing.assert_array_equal(result['lower'][indices],-np.ones(25))
    np.testing.assert_array_equal(result['upper'][indices],np.ones(25))


def test_contradictory_zero_row_and_infeasible_box_are_explicit():
    assert boxes.contract([-1.],[1.],[[0.]],[.1],[.2])['empty']
    result=boxes.contract([-1.],[1.],[[1.]],[2.],[3.])
    assert result['empty'] and result['contradiction']['row']==0


def test_exact_rational_feasible_points_survive_signed_constraints():
    rng=np.random.default_rng(71)
    for _ in range(30):
        point=rng.integers(-7,8,size=27)/8.;matrix=rng.integers(-4,5,size=(12,27))/4.
        target=matrix@point;lower=target-.125;upper=target+.125
        # The oracle computes exact dyadic products, separately from the contractor.
        for row,lo,hi in zip(matrix,lower,upper):
            exact=sum((Fraction(float(a))*Fraction(float(x)) for a,x in zip(row,point)),Fraction(0))
            assert Fraction(float(lo))<=exact<=Fraction(float(hi))
        result=boxes.contract(np.full(27,-1.),np.full(27,1.),matrix,lower,upper,maximum_passes=3)
        assert not result['empty']
        assert np.all(result['lower']<=point) and np.all(point<=result['upper'])


def test_weak_constraints_can_leave_the_entire_box_unchanged():
    result=boxes.contract([-1.,-1.],[1.,1.],[[1.,1.]],[-10.],[10.],maximum_passes=1)
    np.testing.assert_array_equal(result['lower'],[-1.,-1.])
    np.testing.assert_array_equal(result['upper'],[1.,1.])


@pytest.mark.parametrize('matrix,lower,upper',[( [[float('nan')]],[-1.],[1.]),([[1.]], [2.],[1.])])
def test_invalid_constraints_are_rejected(matrix,lower,upper):
    with pytest.raises(ValueError):boxes.contract([-1.],[1.],matrix,lower,upper)


def test_nearly_touching_binary_bounds_do_not_lose_exact_solution():
    target=1/3.;result=boxes.contract([0.],[1.],[[3.]],[1.],[1.])
    assert not result['empty']
    assert Fraction(float(result['lower'][0]))<=Fraction(1,3)<=Fraction(float(result['upper'][0]))
    assert result['lower'][0]<=target<=result['upper'][0]


def test_every_exact_grid_solution_survives_contraction():
    matrix=np.array([[2.,-3.],[-1.,2.],[1.,1.]])
    lower=np.array([-.5,-.25,-.125]);upper=np.array([.75,.5,.625])
    result=boxes.contract([-1.,-1.],[1.,1.],matrix,lower,upper)
    count=0
    for x in range(-16,17):
        for y in range(-16,17):
            point=[Fraction(x,16),Fraction(y,16)]
            feasible=all(Fraction(float(lo))<=sum(Fraction(float(a))*v for a,v in zip(row,point))<=Fraction(float(hi))
                for row,lo,hi in zip(matrix,lower,upper))
            if feasible:
                count+=1;assert not result['empty']
                for i,value in enumerate(point):
                    assert Fraction(float(result['lower'][i]))<=value<=Fraction(float(result['upper'][i]))
    assert count>0


def test_outward_overflow_is_unsupported_instead_of_silent_exclusion():
    with pytest.raises(ValueError,match='overflow'):
        boxes.contract([1e308],[1.1e308],[[1e308]],[0.],[1.])
