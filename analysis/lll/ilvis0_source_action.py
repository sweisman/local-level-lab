# SPDX-License-Identifier: AGPL-3.0-or-later
"""Carry separate force-source directions through (Q-I)(A+B)+B.

Input change/remainder bounds must cover the supplied affine reference rows.
No source certificate, derivative equality or full native propagation is
inferred here. Coefficient rounding is explicitly included in output errors.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import numpy as np
from . import ilvis0_directional_values as vectors
from . import ilvis0_directional_matrices as matrices
from .ilvis0_saved_prediction_audit import endpoint


@dataclass(frozen=True)
class Action:
    value:object
    jacobian:object
    coefficient_rounding:object

    def report(self):
        return dict(value=self.value.report(),jacobian=self.jacobian.tolist(),
            coefficient_rounding=self.coefficient_rounding.tolist(),parameter_count=27,
            input_affine_bounds_require_qualification=True,native_propagation_qualified=False,
            observational_coverage_qualified=False,scientific_decision='abstain')


def source_action(left,a,b,left_jacobian,a_jacobian,b_jacobian,*,lower,upper,reference):
    """left denotes Q-I, not Q. Keep every physical column, including zeros."""
    if (not isinstance(left,matrices.Matrix) or not isinstance(a,vectors.Value)
            or not isinstance(b,vectors.Value) or a.center.shape!=(3,) or b.center.shape!=(3,)):
        raise ValueError('matrix departure and two three-vector affine bounds required')
    jl,ja,jb=(np.asarray(x,float) for x in (left_jacobian,a_jacobian,b_jacobian))
    lo,hi,z=(np.asarray(x,float) for x in (lower,upper,reference))
    if (jl.shape!=(3,3,27) or ja.shape!=(3,27) or jb.shape!=(3,27)
            or any(x.shape!=(27,) for x in (lo,hi,z)) or np.any(lo>hi)
            or not all(np.all(np.isfinite(x)) for x in (jl,ja,jb,lo,hi,z))):
        raise ValueError('all 27 finite affine columns and ordered parameter domain required')
    combined=vectors.add(a,b);value=vectors.add(matrices.apply(left,combined),b)
    jacobian=left.center@(ja+jb)+np.einsum('ikj,k->ij',jl,combined.center)+jb
    widths=[max(abs(F(x)-F(v)),abs(F(y)-F(v))) for x,y,v in zip(lo,hi,z,strict=True)]
    rounding=[];remainders=[]
    for axis in range(3):
        error=F(0)
        for column in range(27):
            exact=F(jb[axis,column])+sum((
                F(left.center[axis,k])*(F(ja[k,column])+F(jb[k,column]))
                +F(jl[axis,k,column])*F(combined.center[k]) for k in range(3)),F(0))
            error+=abs(F(jacobian[axis,column])-exact)*widths[column]
        rounding.append(endpoint(error,True));remainders.append(F(value.remainder[axis])+error)
    result=vectors.Value(value.center,value.change,remainders)
    jacobian=np.array(jacobian,copy=True);jacobian.setflags(write=False)
    rounding=np.array(rounding);rounding.setflags(write=False)
    return Action(result,jacobian,rounding)
