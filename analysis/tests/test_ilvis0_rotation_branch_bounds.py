# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F
import math


def polynomial(x,cosine,order):
    # Independent scalar truncated sine/cosine, differentiated term by term.
    degrees=range(0,9,2) if cosine else range(1,8,2)
    return sum((F((-1)**(n//2),math.factorial(n-order))*x**(n-order)
        for n in degrees if n>=order),F(0))


def test_small_branch_retains_native_polynomial_instead_of_exact_rotation():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_rotation_branch_bounds import enclose
    z=J.affine(0,[1,1],[F(1,200)]*2)
    answer=enclose([J.constant(0),J.constant(0),z])
    assert answer.branches==('polynomial',)
    for n in range(4):
        assert answer.matrix[0][0].exact[n]==(polynomial(F(1,200),True,n),)*2
        assert answer.matrix[1][0].exact[n]==(polynomial(F(1,200),False,n),)*2


def test_crossing_switch_covers_both_branches_and_reports_nonzero_jumps():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_rotation_branch_bounds import enclose
    from test_ilvis0_path_jets import trig_interval
    z=J.affine(0,[1,1],[F(9,1000),F(11,1000)])
    answer=enclose([J.constant(0),J.constant(0),z])
    assert set(answer.branches)=={'polynomial','trigonometric'}
    for point in (F(9,1000),F(1,100),F(11,1000)):
        for n in range(4):
            # Include small-branch polynomial values and the true rotation,
            # independently bracketed by alternating scalar Taylor series.
            lo,hi=answer.matrix[0][0].exact[n]
            assert lo<=polynomial(point,True,n)<=hi
            trig=trig_interval(point,n%2==0)
            sign=1 if n in (0,3) else -1
            assert lo<=min(sign*v for v in trig)<=max(sign*v for v in trig)<=hi
    assert all(v>0 for v in answer.jump_norms)
    assert answer.jump_norms[0]<F(1,10**20)
    report=answer.report()
    assert report['local_branch_coverage_verified']
    assert not report['trajectory_branch_partition_verified']
    assert not report['floating_point_execution_covered']


def test_large_branch_needs_no_polynomial_switch_allowance_within_its_domain():
    from lll.ilvis0_path_jets import Jet3 as J
    from lll.ilvis0_rotation_branch_bounds import enclose
    result=enclose([J.constant(0),J.constant(0),J.constant(F(1,4))])
    assert result.branches==('trigonometric',)
    assert result.jump_norms==(0,0,0,0)
