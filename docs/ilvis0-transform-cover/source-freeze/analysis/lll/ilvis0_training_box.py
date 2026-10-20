# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conservative affine necessary-constraint propagation, with all columns kept.

The caller must separately justify any training-noise/nonlinear allowances used
to construct these inequalities. No native model, observation law or coverage
claim is supplied here. Nonfinite outward arithmetic is unsupported.
"""
import math

import numpy as np

VERSION='ilvis0-affine-training-box-contraction-v1'


def _out(value,direction):
    if not math.isfinite(value):raise ValueError('outward arithmetic overflow; region unsupported')
    result=math.nextafter(value,direction)
    if not math.isfinite(result):raise ValueError('outward endpoint overflow; region unsupported')
    return result


def _sum_range(row,lower,upper,omit=None):
    lo=0.;hi=0.;first=True
    for i,coefficient in enumerate(row):
        a=float(coefficient)
        if i==omit or a==0.:continue
        x=float(lower[i] if a>0. else upper[i]);y=float(upper[i] if a>0. else lower[i])
        left=_out(a*x,-math.inf) if x else 0.;right=_out(a*y,math.inf) if y else 0.
        if first:lo=left;hi=right;first=False
        else:lo=_out(lo+left,-math.inf);hi=_out(hi+right,math.inf)
    return lo,hi


def contract(lower,upper,design,target_lower,target_upper,*,maximum_passes=8):
    """Retain a box containing every feasible point of L <= design*x <= U.

    A finite pass limit may leave a loose enclosure. Its failure to contract is
    informative. A coordinate is never removed for being unidentifiable.
    """
    lo=np.array(lower,float,copy=True);hi=np.array(upper,float,copy=True)
    a=np.array(design,float,copy=True);left=np.array(target_lower,float,copy=True);right=np.array(target_upper,float,copy=True)
    if (lo.ndim!=1 or not len(lo) or hi.shape!=lo.shape or a.ndim!=2 or a.shape[1]!=len(lo) or not len(a)
            or left.shape!=(len(a),) or right.shape!=left.shape
            or any(not np.all(np.isfinite(x)) for x in (lo,hi,a,left,right))
            or np.any(lo>hi) or np.any(left>right) or type(maximum_passes) is not int or not 1<=maximum_passes<=32):
        raise ValueError('complete finite ordered box/row inequalities and a finite pass limit required')
    updates=0;contradiction=None;fixed=False
    for passes in range(1,maximum_passes+1):
        changed=False
        for index,row in enumerate(a):
            minimum,maximum=_sum_range(row,lo,hi)
            if minimum>right[index] or maximum<left[index]:
                contradiction=dict(row=index,outward_minimum=minimum,outward_maximum=maximum,
                    required_lower=float(left[index]),required_upper=float(right[index]));break
            for axis,coefficient in enumerate(row):
                coefficient=float(coefficient)
                if coefficient==0.:continue
                other_min,other_max=_sum_range(row,lo,hi,omit=axis)
                numerator_lo=_out(float(left[index])-other_max,-math.inf)
                numerator_hi=_out(float(right[index])-other_min,math.inf)
                if coefficient>0.:
                    implied_lo=_out(numerator_lo/coefficient,-math.inf)
                    implied_hi=_out(numerator_hi/coefficient,math.inf)
                else:
                    implied_lo=_out(numerator_hi/coefficient,-math.inf)
                    implied_hi=_out(numerator_lo/coefficient,math.inf)
                new_lo=max(float(lo[axis]),implied_lo);new_hi=min(float(hi[axis]),implied_hi)
                if new_lo>new_hi:
                    contradiction=dict(row=index,axis=axis,implied_lower=implied_lo,implied_upper=implied_hi,
                        previous_lower=float(lo[axis]),previous_upper=float(hi[axis]));break
                if new_lo>lo[axis] or new_hi<hi[axis]:
                    lo[axis]=new_lo;hi[axis]=new_hi;changed=True;updates+=1
            if contradiction is not None:break
        if contradiction is not None:break
        if not changed:fixed=True;break
    lo.setflags(write=False);hi.setflags(write=False)
    return dict(version=VERSION,lower=lo,upper=hi,empty=contradiction is not None,contradiction=contradiction,
        passes=passes,updates=updates,fixed_point_reached=fixed,parameter_count=len(lo),
        input_inequalities_scientifically_justified=False,nonlinear_bound_qualified=False,
        observational_coverage_calibrated=False,scientific_decision='abstain')
