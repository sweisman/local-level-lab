# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import numpy as np
import pytest
from lll import ilvis0_force_integrals as integral,ilvis0_clocked_force_transform as clocked
from test_ilvis0_common_force_transform import terms,independent
from test_ilvis0_force_integrals import oracle


def setup():
    ref,matrix=terms();periods=[.25]*8;forces=[[.1*i,(-1.)**i*.2,-.05*i] for i in range(8)]
    time=F(.75);limit=F(float(ref.limits[25]));center=time+limit*F(float(ref.center[25]))
    profile=integral.enclose(periods,forces,center=center,lower=time+limit*F(float(ref.lower[25])),upper=time+limit*F(float(ref.upper[25])))
    return ref,matrix,periods,forces,time,profile


def test_one_clock_matrix_weighted_remainder_and_all_columns():
    ref,matrix,periods,forces,time,profile=setup();obj=clocked.ClockedForceTransform(matrix,profile,nominal_time=time,metric=[1.,2.,-1.])
    assert obj.jacobian.shape==(3,27) and obj.coefficients.matrix.shape==(3,9)
    rng=np.random.default_rng(628)
    for point in [ref.lower,ref.upper,ref.center,*rng.uniform(-1,1,(64,27))]:
        at=time+F(float(ref.limits[25]))*F(float(point[25]));h=oracle(periods,forces,at)[1]
        actual=(independent(ref,point)@np.array([float(v) for v in h]))*[1.,2.,-1.]
        predicted=obj.center+obj.jacobian@(point-ref.center)+obj.coefficients.matrix@matrix.normalized_values_at(point)
        assert np.all(abs(actual-predicted)<=obj.unshared_remainder+2e-13)


def test_uncovered_clock_is_rejected_and_coefficients_are_immutable():
    ref,matrix,periods,forces,time,profile=setup()
    with pytest.raises(ValueError):clocked.ClockedForceTransform(matrix,profile,nominal_time=time+F(1,10),metric=[1.,1.,1.])
    obj=clocked.ClockedForceTransform(matrix,profile,nominal_time=time,metric=[1.,1.,1.])
    with pytest.raises(ValueError):obj.center[0]=1.
