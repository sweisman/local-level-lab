# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import importlib,importlib.util
import pytest
from test_ilvis0_rotation_roundoff import multiply


def implementation():
    name='lll.ilvis0_rotation_derivative'
    assert importlib.util.find_spec(name) is not None,'rotation-derivative enclosure is not implemented'
    return importlib.import_module(name)


def skew(vector):
    x,y,z=map(F,vector)
    return [[F(0),-z,y],[z,F(0),-x],[-y,x,F(0)]]


def reference(angle,axis):
    k=skew(angle);basis=[0,0,0];basis[axis]=1;dk=skew(basis)
    term=[[F(int(i==j)) for j in range(3)] for i in range(3)]
    derivative=[[F(0) for _ in range(3)] for _ in range(3)]
    result=[row.copy() for row in derivative]
    for n in range(1,61):
        first=multiply(derivative,k);second=multiply(term,dk)
        derivative=[[(first[i][j]+second[i][j])/n for j in range(3)] for i in range(3)]
        term=[[v/n for v in row] for row in multiply(term,k)]
        result=[[result[i][j]+derivative[i][j] for j in range(3)] for i in range(3)]
    return result


@pytest.mark.parametrize('angle',[(0.,0.,0.),(.003,-.004,.005),(.3,-.2,.8)])
def test_derivative_enclosures_contain_independent_frechet_series(angle):
    report=implementation().enclose(angle)
    for axis in range(3):
        expected=reference(angle,axis)
        for i in range(3):
            for j in range(3):
                assert F(report['lower'][axis][i][j])<=expected[i][j]<=F(report['upper'][axis][i][j])
    assert not report['initial_source_bridge_qualified']


def test_zero_angle_derivatives_are_exact_signed_generators():
    report=implementation().enclose([0.,0.,0.])
    for axis in range(3):
        vector=[0,0,0];vector[axis]=1;expected=skew(vector)
        for i in range(3):
            for j in range(3):
                assert F(report['lower'][axis][i][j])==F(report['upper'][axis][i][j])==expected[i][j]
