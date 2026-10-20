# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact feasible witnesses in a declared linear relaxation.

A witness establishes feasibility in this region only. It need not correspond
to a physical calibration or a realizable nonlinear trajectory.
"""
from dataclasses import dataclass
from fractions import Fraction as F


def _fraction(value):
    try:result=F(value)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite rational-compatible value required') from None
    if max(result.numerator.bit_length(),result.denominator.bit_length())>8192:
        raise ValueError('finite exact-arithmetic precision allowance exceeded')
    return result


def _vector(values,size):
    if len(values)!=size:raise ValueError('all declared coordinates required')
    return tuple(_fraction(v) for v in values)


def _dot(left,right):return sum((a*b for a,b in zip(left,right,strict=True) if a),F(0))


@dataclass(frozen=True)
class Region:
    lower:tuple
    upper:tuple
    design:tuple
    bound:tuple

    def __post_init__(self):
        n=len(self.lower)
        if not 1<=n<=256 or len(self.design)>1024:
            raise ValueError('finite complete region size required')
        lo=_vector(self.lower,n);hi=_vector(self.upper,n)
        a=tuple(_vector(row,n) for row in self.design);b=_vector(self.bound,len(a))
        if any(left>right for left,right in zip(lo,hi)):raise ValueError('ordered box required')
        for name,value in (('lower',lo),('upper',hi),('design',a),('bound',b)):
            object.__setattr__(self,name,value)

    def slacks(self,point):
        x=_vector(point,len(self.lower))
        return tuple(_dot(row,x)-b for row,b in zip(self.design,self.bound))+tuple(
            v-b for v,b in zip(x,self.upper))+tuple(a-v for a,v in zip(self.lower,x))

    def objective(self,coefficients,point):
        n=len(self.lower)
        return _dot(_vector(coefficients,n),_vector(point,n))

    def repair(self,proposal,anchor):
        n=len(self.lower);candidate=_vector(proposal,n);known=_vector(anchor,n)
        anchor_slacks=self.slacks(known)
        if max(anchor_slacks)>0:raise ValueError('anchor is not exactly feasible in the supplied region')
        violations=self.slacks(candidate);fraction=F(0)
        for before,fixed in zip(violations,anchor_slacks):
            if before>0:fraction=max(fraction,before/(before-fixed))
        point=tuple((1-fraction)*v+fraction*a for v,a in zip(candidate,known))
        after=self.slacks(point)
        if max(after)>0:raise ArithmeticError('exact feasible-witness repair failed')
        return dict(point=point,mixing_fraction=fraction,
            maximum_proposal_violation=max(F(0),max(violations)),maximum_final_slack=max(after),
            constraint_checks=3*len(violations),parameter_count=n,
            physical_realizability_established=False,observational_coverage_qualified=False)
