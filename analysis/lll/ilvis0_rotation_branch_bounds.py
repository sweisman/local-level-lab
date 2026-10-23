# SPDX-License-Identifier: AGPL-3.0-or-later
"""Local piecewise rotation bounds, separate from frozen motion controls."""
from dataclasses import dataclass
from fractions import Fraction as F
import math
from .ilvis0_path_jets import Jet3 as J,exp_skew,_product
from .ilvis0_exact_scale import sqrt_upper

THRESHOLD=F(1e-4)


@dataclass(frozen=True)
class BranchRotation:
    matrix:tuple
    branches:tuple
    jump_norms:tuple
    arguments:tuple

    def report(self):
        return dict(version='ilvis0-native-rotation-branch-bounds-v1',
            matrix=[[v.report() for v in row] for row in self.matrix],
            arguments=[v.report() for v in self.arguments],branches=list(self.branches),
            switch_jump_norms=list(map(str,self.jump_norms)),input_path_smooth_assumed=True,
            local_branch_coverage_verified=True,trajectory_branch_partition_verified=False,
            incoming_argument_jumps_covered=False,orthogonality_assumed=False,
            floating_point_execution_covered=False,observational_coverage_qualified=False,
            scientific_decision='abstain')


def _polynomial(vector):
    x,y,z=vector;zero=J.constant(0);k=((zero,-z,y),(z,zero,-x),(-y,x,zero))
    term=tuple(tuple(J.constant(int(i==j)) for j in range(3)) for i in range(3));result=term
    for n in range(1,9):
        term=tuple(tuple(v/F(n) for v in row) for row in _product(term,k))
        result=tuple(tuple(a+b for a,b in zip(row,addition)) for row,addition in zip(result,term))
    return result


def enclose(vector):
    """Cover both ideal native formulas even when the switch is crossed.

For a real skew matrix K, the native small-angle Rodrigues polynomial equals
sum(K**n/n!,n=0..8). Its difference from exp(K), and derivatives through order
three along a smooth input path, have explicit omitted-series norm bounds.
These bound the jump between branch expressions at the switch. They do not
cover incoming argument jumps or floating-point execution differences.
"""
    if len(vector)!=3 or not all(isinstance(v,J) for v in vector):
        raise ValueError('three complete smooth-input derivative enclosures required')
    q=sum((v.square() for v in vector),J.constant(0));lo,hi=q.exact[0]
    if hi<THRESHOLD:
        return BranchRotation(_polynomial(vector),('polynomial',),(F(0),)*4,tuple(vector))
    truth=exp_skew(vector)
    if lo>=THRESHOLD:
        return BranchRotation(truth.matrix,('trigonometric',),(F(0),)*4,tuple(vector))
    a0=F(sqrt_upper(THRESHOLD));_,a1,a2,a3=truth.argument_norms
    def tail(m):return a0**(m+1)/F(math.factorial(m+1))/(1-a0/F(m+2))
    jumps=(tail(8),a1*tail(7),a2*tail(7)+a1*a1*tail(6),
        a3*tail(7)+3*a1*a2*tail(6)+a1**3*tail(5))
    matrix=tuple(tuple(J(tuple((left-radius,right+radius)
        for (left,right),radius in zip(v.exact,jumps))) for v in row) for row in truth.matrix)
    return BranchRotation(matrix,('polynomial','trigonometric'),jumps,tuple(vector))
