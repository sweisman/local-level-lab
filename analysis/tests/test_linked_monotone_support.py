# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for an interval-certified maximum over a box."""

from fractions import Fraction as F

from lll.ilvis0_interval_calibration import Jet
from lll.linked_monotone_support import upper_bound
from lll.esa_linked_monotone_study import checked_parent


def variable(axis, lo, hi):
    return Jet.variable(lo[axis], hi[axis], axis)


def test_monotone_upper_face_retains_the_true_maximum():
    def expression(lo, hi):
        x, y = (variable(axis, lo, hi) for axis in (0, 1))
        return x*(y+3)-4*y

    result = upper_bound(expression, [-1., 0.]+[0.]*25, [2., 4.]+[0.]*25)
    assert result['fixed'] == [0, 1]
    assert F(result['upper']) >= 6
    assert F(result['upper']) < F(60001, 10000)


def test_uncertain_derivative_is_retained_and_interior_maximum_is_enclosed():
    def expression(lo, hi):
        x, y = (variable(axis, lo, hi) for axis in (0, 1))
        return y-x.square()

    result = upper_bound(expression, [-2., 0.]+[0.]*25, [1., 3.]+[0.]*25)
    assert result['fixed'] == [1]
    assert result['lower'][0] == -2
    assert result['higher'][0] == 1
    assert F(result['upper']) >= 3
    assert F(result['upper']) < F(30001, 10000)


def test_recomputed_gradient_can_qualify_a_second_face():
    def expression(lo, hi):
        x, y = (variable(axis, lo, hi) for axis in (0, 1))
        return x*(y+3.)-y

    result = upper_bound(expression, [-1., 0.]+[0.]*25, [2., 4.]+[0.]*25)
    assert result['fixed'] == [0, 1]
    assert result['evaluations'] == 4
    assert F(result['upper']) >= 10
    assert F(result['upper']) < F(100001, 10000)


def test_original_graph_and_full_loss_reports_use_their_own_closure_layout():
    closure = dict(manifest_sha256='manifest', summary_sha256='summary', state='complete')
    prefix = 'data/example'
    assert checked_parent(closure, closure, prefix, joint_report=False)
    combined = {'closures': {prefix: closure}}
    assert checked_parent(combined, closure, prefix, joint_report=True)
    assert not checked_parent(combined, dict(closure, state='incomplete'), prefix, joint_report=True)
