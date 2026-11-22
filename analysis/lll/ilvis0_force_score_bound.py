# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bound one signed score of the common rotation and gain remainder."""
import math
import time

import numpy as np

from .ilvis0_force_bounds import _Box
from .ilvis0_interval_calibration import Jet, _input_box, exp_skew
from .ilvis0_common_force_transform import ForceTransform


AXES = (0, 1, 2, 18, 19, 20)


def bound(transform, coefficient_lower, coefficient_upper, *, maximum_boxes, maximum_seconds):
    """Enclose the mathematical force transform over the whole physical box.

    Coefficient intervals refer to the nine normalized errors in row-major
    order. A cell is retained until both subcells have verified intervals.
    No optimisation witness is required to cover the complete box.
    """
    from fractions import Fraction

    lo,hi = tuple(map(Fraction,coefficient_lower)),tuple(map(Fraction,coefficient_upper))
    if (not isinstance(transform,ForceTransform) or len(lo)!=9 or len(hi)!=9
            or any(a>b for a,b in zip(lo,hi,strict=True))
            or type(maximum_boxes) is not int or not 1<=maximum_boxes<=2047
            or not math.isfinite(maximum_seconds) or maximum_seconds<=0):
        raise ValueError('ordered force score coefficients and finite work limits required')
    reference = transform.reference
    weights = []
    for a,b,c in zip(lo,hi,transform.caps,strict=True):
        if c==0.:
            if a or b:
                raise ValueError('zero force cap must have a zero score coefficient')
            weights.append(_Box(0.))
        else:
            weights.append(_input_box(a/Fraction(float(c)),b/Fraction(float(c))))
    weights = np.asarray(weights,dtype=object).reshape(3,3)
    mounted = [[sum((weights[k,j]*_Box(float(reference.initial_r[k,i])) for k in range(3)),_Box(0.))
                for j in range(3)] for i in range(3)]
    baseline = sum((w*_Box(float(v)) for w,v in zip(weights.flat,transform.center.flat)),_Box(0.))
    slopes = {i:sum((w*_Box(float(v)) for w,v in zip(weights.flat,transform.jacobian[:,:,i].flat)),_Box(0.))
              for i in AXES}

    def score(lower,upper):
        axes = [Jet.variable(a,b,i) for i,a,b in zip(AXES,lower,upper,strict=True)]
        angles = [float(reference.limits[i])*x for i,x in zip(AXES[:3],axes[:3],strict=True)]
        rotation = exp_skew(angles)
        total = Jet.constant(0.)
        for j,gain in enumerate(axes[3:]):
            rotated = sum((rotation[i][j]*mounted[i][j] for i in range(3)),Jet.constant(0.))
            total += rotated/(1.+float(reference.limits[18+j])*gain)
        return total-baseline-sum(
            ((x-float(reference.center[i]))*slopes[i] for i,x in zip(AXES,axes,strict=True)),
            Jet.constant(0.))

    def enclose(lower,upper):
        center = tuple(a+(b-a)/2. for a,b in zip(lower,upper,strict=True))
        gradient = score(lower,upper).derivative
        seed = score(center,center).value
        result = seed
        priorities = []
        for i,a,b,m in zip(AXES,lower,upper,center,strict=True):
            g = gradient[i]
            result += g*(_Box(a,b)-_Box(m))
            priorities.append(max(abs(g.lo),abs(g.hi))*(b-a))
        return (result,lower,upper,center,tuple(priorities),seed)

    start = time.monotonic()
    lower = tuple(float(reference.lower[i]) for i in AXES)
    upper = tuple(float(reference.upper[i]) for i in AXES)
    cells = [enclose(lower,upper)]
    count = 1
    while count+2<=maximum_boxes and time.monotonic()-start<maximum_seconds:
        known_high = max(cell[5].lo for cell in cells)
        known_low = min(cell[5].hi for cell in cells)
        index = max(range(len(cells)),key=lambda j:max(cells[j][0].hi-known_high,known_low-cells[j][0].lo))
        _,lo_cell,hi_cell,mid,priorities,_ = cells[index]
        axis = max(range(len(AXES)),key=lambda j:priorities[j])
        if not lo_cell[axis]<mid[axis]<hi_cell[axis]:
            break
        left,right = list(hi_cell),list(lo_cell)
        left[axis] = right[axis] = mid[axis]
        children = [enclose(lo_cell,tuple(left)),enclose(tuple(right),hi_cell)]
        cells[index:index+1] = children
        count += 2
    return dict(lower=min(cell[0].lo for cell in cells),
                upper=max(cell[0].hi for cell in cells),
                evaluated_boxes=count,covering_cells=len(cells),axis_indices=list(AXES),
                elapsed_s=time.monotonic()-start,
                earlier_fit_constraint_used=False,scientific_decision='abstain')
