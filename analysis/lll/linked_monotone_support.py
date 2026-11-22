# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outward upper bound using verified monotone derivatives of a linked map."""

from fractions import Fraction as F

from .ilvis0_saved_prediction_audit import endpoint


def upper_bound(expression, lower, higher):
    """Enclose the maximum by moving sign-definite coordinates to a face."""
    lo, hi = list(lower), list(higher)
    if len(lo) != 27 or len(hi) != 27 or any(a > b for a, b in zip(lo, hi, strict=True)):
        raise ValueError('all ordered physical coordinates required')
    value = expression(lo, hi)
    faces = []
    evaluations = 1
    for _ in range(2):
        changes = {}
        for axis, derivative in enumerate(value.derivative):
            if lo[axis] == hi[axis]:
                continue
            if derivative.lo > 0.:
                changes[axis] = hi[axis]
            elif derivative.hi < 0.:
                changes[axis] = lo[axis]
        if not changes:
            break
        faces.append([dict(axis=axis, endpoint=target,
                           derivative=[value.derivative[axis].lo, value.derivative[axis].hi])
                      for axis, target in changes.items()])
        for axis, target in changes.items():
            lo[axis] = hi[axis] = target
        value = expression(lo, hi)
        evaluations += 1
    center = [float((F(a)+F(b))/2) for a, b in zip(lo, hi, strict=True)]
    at_center = expression(center, center).value
    from_center = F(at_center.hi)
    for a, b, mid, gradient in zip(lo, hi, center, value.derivative, strict=True):
        from_center += max(F(g)*(F(x)-F(mid)) for g in (gradient.lo, gradient.hi) for x in (a, b))
    upper = min(F(value.value.hi), from_center)
    return dict(upper=endpoint(upper, True), exact_upper=str(upper), lower=lo, higher=hi,
                faces=faces, fixed=sorted(item['axis'] for face in faces for item in face),
                evaluations=evaluations+1)
