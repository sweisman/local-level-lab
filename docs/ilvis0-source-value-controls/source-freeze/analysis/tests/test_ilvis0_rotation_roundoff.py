# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import importlib,importlib.util
import math
import pytest


def implementation():
    name='lll.ilvis0_rotation_roundoff'
    assert importlib.util.find_spec(name) is not None,'rotation-center enclosure is not implemented'
    return importlib.import_module(name)


def multiply(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]


def independent_matrix_series(vector):
    # Matrix powers, independently of scalar Rodrigues/sinc coefficients.
    x,y,z=map(F,vector);k=[[F(0),-z,y],[z,F(0),-x],[-y,x,F(0)]]
    term=[[F(int(i==j)) for j in range(3)] for i in range(3)]
    total=[row.copy() for row in term]
    terms=100 if x*x+y*y+z*z>4 else 60
    for n in range(1,terms+1):
        term=[[v/n for v in row] for row in multiply(term,k)]
        total=[[total[i][j]+term[i][j] for j in range(3)] for i in range(3)]
    return total


@pytest.mark.parametrize('angle',[(0.,0.,0.),(.001,-.002,.003),(.3,-.5,.8),(1.,-1.,1.),(8.,0.,0.),(1e-300,0.,0.)])
def test_enclosure_covers_independent_matrix_power_series(angle):
    module=implementation()
    from scipy.spatial.transform import Rotation
    center=Rotation.from_rotvec(angle).as_matrix().tolist()
    report=module.enclose(angle,center)
    oracle=independent_matrix_series(angle)
    for i in range(3):
        for j in range(3):
            assert F(report['lower'][i][j])<=oracle[i][j]<=F(report['upper'][i][j])
            assert abs(oracle[i][j]-F(center[i][j]))<=F(report['component_errors'][i][j])
    assert F(report['norm_error'])**2>=sum((F(v)**2 for row in report['component_errors'] for v in row),F(0))
    assert not report['whole_source_rounding_qualified']


def test_identity_is_exact_and_supplied_center_errors_are_not_hidden():
    module=implementation();identity=[[float(i==j) for j in range(3)] for i in range(3)]
    report=module.enclose([0.,0.,0.],identity)
    assert report['norm_error']==0
    identity[1][0]=1e-4
    report=module.enclose([0.,0.,0.],identity)
    assert F(report['component_errors'][1][0])>=F(1e-4)


def test_unsupported_reference_inputs_are_rejected():
    module=implementation();identity=[[float(i==j) for j in range(3)] for i in range(3)]
    for angle in ([9.,0.,0.],[math.nan,0.,0.],[0.,0.]):
        with pytest.raises(ValueError):module.enclose(angle,identity)
