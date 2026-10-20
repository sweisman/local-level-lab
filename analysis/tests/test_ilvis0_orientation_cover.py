# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np
import pytest
from lll import ilvis0_orientation_cover as cover


def test_closed_dyadic_sectors_cover_original_box_without_changing_other_columns():
    sectors=[cover.sector(i) for i in range(8)]
    assert sectors[0]['lower'][2]==-1. and sectors[-1]['upper'][2]==1.
    for i,s in enumerate(sectors):
        assert len(s['lower'])==len(s['center'])==27
        indices=[j for j in range(27) if j!=2]
        np.testing.assert_array_equal(s['lower'][indices],-np.ones(26))
        np.testing.assert_array_equal(s['upper'][indices],np.ones(26))
        if i:assert sectors[i-1]['upper'][2]==s['lower'][2]
    for k in range(-1024,1025):
        value=F(k,1024)
        assert any(F(s['lower'][2])<=value<=F(s['upper'][2]) for s in sectors)


def test_training_constraints_use_absolute_parameters_at_nonzero_center():
    center=np.linspace(-.2,.2,27);matrix=np.zeros((2,27));matrix[0,:2]=[2.,-3.];matrix[1,12]=.25
    delta=np.array([.1,-.3]);allowance=np.array([.02,.04])
    result=cover.training_constraints(matrix,delta,allowance,center)
    for i,row in enumerate(matrix):
        exact=sum((F(float(a))*F(float(x)) for a,x in zip(row,center)),F(0))
        assert F(result['lower'][i])<=exact+F(delta[i])-F(allowance[i])
        assert F(result['upper'][i])>=exact+F(delta[i])+F(allowance[i])
    np.testing.assert_array_equal(result['design'],matrix)


def test_future_envelope_retains_correlation_and_unidentified_axis():
    center=np.full(27,.25);matrix=np.zeros((1,27));matrix[0,:2]=[1.,-1.]
    constraints=cover.training_constraints(matrix,[0.],[.001],center)
    j=np.zeros((3,27));j[0,:2]=[1.,-1.];j[1,7]=2.
    result=cover.future_envelope([5.,2.5,9.],j,center,-np.ones(27),np.ones(27),constraints,[.01,.01,.01],arithmetic_allowance=0.)
    assert result['lower'][0]<=4.989 and result['upper'][0]>=5.011
    assert result['upper'][0]-result['lower'][0]<.023
    assert result['lower'][1]<=-.01 and result['upper'][1]>=4.01
    assert result['parameter_count']==27 and result['scientific_decision']=='abstain'


def test_future_truth_is_not_an_envelope_input_and_remainder_cannot_disappear():
    center=np.zeros(27);j=np.zeros((3,27));constraints=cover.training_constraints(np.zeros((1,27)),[0.],[1.],center)
    result=cover.future_envelope([0.,0.,0.],j,center,-np.ones(27),np.ones(27),constraints,[2.,3.,4.],arithmetic_allowance=.1)
    np.testing.assert_allclose(result['lower'],[-2.1,-3.1,-4.1],atol=1e-14)
    np.testing.assert_allclose(result['upper'],[2.1,3.1,4.1],atol=1e-14)
    assert not result['floating_point_enclosure_verified']


def test_invalid_cover_and_constraints_fail_explicitly():
    with pytest.raises(ValueError):cover.sector(8)
    with pytest.raises(ValueError):cover.sector(0,count=3)
    with pytest.raises(ValueError):cover.training_constraints(np.zeros((1,26)),[0.],[1.],np.zeros(27))
    with pytest.raises(ValueError):cover.training_constraints(np.zeros((1,27)),[0.],[-1.],np.zeros(27))
