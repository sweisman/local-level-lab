# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll.ilvis0_directional_values import Value
from lll.ilvis0_directional_matrices import Matrix,add,scale,product,apply,transpose,skew,identity


def test_sparse_matrix_action_does_not_spread_horizontal_bounds_into_height():
    value=Value([0.,0.,-1.],[.001,0.,.0000005],[1e-10,0.,.0000005])
    result=apply(identity(),value)
    np.testing.assert_array_equal(result.center,value.center)
    np.testing.assert_array_equal(result.change,value.change)
    np.testing.assert_array_equal(result.remainder,value.remainder)


def test_matrix_center_rounding_is_explicitly_bounded():
    a=Matrix.constant([[.1,.2,.3],[.2,.3,.4],[.3,.4,.5]])
    b=Matrix.constant([[.3,.4,.5],[.4,.5,.6],[.5,.6,.7]])
    result=product(a,b)
    for i in range(3):
        for j in range(3):
            exact=sum((F(a.center[i,k])*F(b.center[k,j]) for k in range(3)),F(0))
            error=abs(F(result.center[i,j])-exact)
            assert F(result.change[i,j])>=error and F(result.remainder[i,j])>=error


def test_exact_fractional_scale_and_transpose_preserve_bounds():
    a=Matrix.constant(np.full((3,3),.1));b=transpose(scale(a,F(1,3)))
    error=abs(F(b.center[0,1])-F(.1)/3)
    assert F(b.change[0,1])>=error and F(b.remainder[0,1])>=error


def test_skew_has_exact_sparsity_and_signs():
    a=Value([1.,2.,3.],[.1,.2,.3],[.01,.02,.03]);matrix=skew(a)
    assert matrix.center.tolist()==[[0.,-3.,2.],[3.,0.,-1.],[-2.,1.,0.]]
    assert np.all(np.diag(matrix.change)==0) and np.all(np.diag(matrix.remainder)==0)
    assert matrix.change[0,1]==a.change[2] and matrix.remainder[1,2]==a.remainder[0]


@pytest.mark.parametrize('kind',['product','action'])
def test_exact_polynomial_truth_and_first_derivative_are_enclosed(kind):
    c=[[F(i==j) for j in range(3)] for i in range(3)]
    l=[[F(i-j,8) for j in range(3)] for i in range(3)]
    q=[[F(i+j-2,64) for j in range(3)] for i in range(3)]
    d=[[F(i+j+1,4) for j in range(3)] for i in range(3)]
    m=[[F(i+j-2,16) for j in range(3)] for i in range(3)]
    r=[[F(i-j,128) for j in range(3)] for i in range(3)]
    def mat(a,b,e):return Matrix(np.array(a,float),np.array([[abs(x)+abs(y) for x,y in zip(v,w)] for v,w in zip(b,e)],object),np.array([[abs(x) for x in v] for v in e],object))
    def mul(a,b):return [[sum((a[i][k]*b[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]
    a=mat(c,l,q)
    if kind=='product':
        result=product(a,mat(d,m,r));x=mul(c,m);y=mul(l,d)
        linear=[[v+w for v,w in zip(u,z)] for u,z in zip(x,y)]
    else:
        value=Value([1.,-2.,3.],[F(5,16)]*3,[F(1,16)]*3);result=apply(a,value)
        linear=[sum((c[i][k]*F(1,4)+l[i][k]*F([1,-2,3][k]) for k in range(3)),F(0)) for i in range(3)]
    for step in range(-16,17):
        t=F(step,16);actual_a=[[x+y*t+z*t*t for x,y,z in zip(u,v,w)] for u,v,w in zip(c,l,q)]
        if kind=='product':
            actual_b=[[x+y*t+z*t*t for x,y,z in zip(u,v,w)] for u,v,w in zip(d,m,r)];truth=mul(actual_a,actual_b)
        else:
            actual_b=[F(v)+F(1,4)*t+F(1,16)*t*t for v in (1,-2,3)]
            truth=[sum((v*w for v,w in zip(row,actual_b)),F(0)) for row in actual_a]
        for exact,center,delta,rem,first in zip(np.array(truth,object).flat,result.center.flat,result.change.flat,result.remainder.flat,np.array(linear,object).flat):
            assert abs(exact-F(center))<=F(delta)
            assert abs(exact-F(center)-first*t)<=F(rem)


def test_matrix_is_immutable_and_addition_keeps_all_entries():
    a=identity();result=add(a,scale(a,-1.))
    assert np.all(result.center==0) and np.all(result.change==0) and np.all(result.remainder==0)
    with pytest.raises(ValueError):a.center[0,0]=0


@pytest.mark.parametrize('bad',['shape','negative','nonfinite'])
def test_bad_matrices_are_rejected(bad):
    center=np.eye(3);change=np.zeros((3,3));remainder=np.zeros((3,3))
    if bad=='shape':center=np.zeros((2,3))
    if bad=='negative':change[0,0]=-1
    if bad=='nonfinite':remainder[0,0]=float('nan')
    with pytest.raises(ValueError):Matrix(center,change,remainder)
