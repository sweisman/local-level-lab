# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calibrated force boxes and direction-preserving rotation actions.

Exact rational endpoints with independently checked upper square roots.
Dependencies between input intervals are relaxed conservatively. This bounds
an action, not a Taylor remainder or a complete navigation calculation.
"""
from fractions import Fraction as F
from .ilvis0_axis_rotation_bounds import bound as axis_bound
from .ilvis0_exact_scale import sqrt_upper


def _three(values):
    if len(values)!=3:raise ValueError('three finite coordinates required')
    try:return list(map(F,values))
    except (ValueError,OverflowError,TypeError):raise ValueError('finite rational coordinates required') from None


def _box(lower,upper):
    lo=_three(lower);hi=_three(upper)
    if any(a>b for a,b in zip(lo,hi)):raise ValueError('ordered intervals required')
    return lo,hi


def _product(a,b,c,d):
    values=(a*c,a*d,b*c,b*d)
    return min(values),max(values)


def calibrated_force(raw_delta_v,period,bias_bounds,gain_bounds):
    raw=_three(raw_delta_v)
    try:dt=F(period)
    except (ValueError,OverflowError,TypeError):raise ValueError('finite positive period required') from None
    if dt<=0 or len(bias_bounds)!=3 or len(gain_bounds)!=3:
        raise ValueError('positive period and three bias/gain intervals required')
    if any(len(row)!=2 for row in list(bias_bounds)+list(gain_bounds)):
        raise ValueError('two endpoints per calibration interval required')
    blo,bhi=_box([r[0] for r in bias_bounds],[r[1] for r in bias_bounds])
    glo,ghi=_box([r[0] for r in gain_bounds],[r[1] for r in gain_bounds])
    if any(g<=-1 for g in glo):raise ValueError('positive gain factor throughout the domain required')
    lower=[];upper=[]
    for v,a,b,c,d in zip(raw,blo,bhi,glo,ghi):
        lo,hi=_product(v/dt-b,v/dt-a,1/(1+d),1/(1+c))
        lower.append(lo);upper.append(hi)
    return lower,upper


def action(rotation_lower,rotation_upper,force_lower,force_upper,*,installation=None):
    """Enclose installation @ exp([w]x) @ force, with w in radians.

    The installation is an exact supplied linear map. It is never silently
    normalized into a rotation; validating its physical meaning is the caller's
    responsibility. No floating matrix-product roundoff is inferred here.
    """
    lo,hi=_box(rotation_lower,rotation_upper);flo,fhi=_box(force_lower,force_upper)
    if installation is None:installation=[[int(i==j) for j in range(3)] for i in range(3)]
    if len(installation)!=3:raise ValueError('complete three-by-three installation map required')
    matrix=[_three(row) for row in installation]
    left=[];right=[]
    for axis in range(3):
        rotation=axis_bound(lo,hi,axis=axis)
        a,b=_product(flo[axis],fhi[axis],F(rotation['parallel_lower']),F(rotation['parallel_upper']))
        transverse_force=sum((max(abs(x),abs(y))**2 for j,(x,y) in enumerate(zip(flo,fhi)) if j!=axis),F(0))
        cross=F(sqrt_upper(F(rotation['transverse_squared_upper'])*transverse_force))
        left.append(a-cross);right.append(b+cross)
    output_lower=[];output_upper=[]
    for row in matrix:
        pieces=[_product(c,c,a,b) for c,a,b in zip(row,left,right)]
        output_lower.append(sum((a for a,b in pieces),F(0)))
        output_upper.append(sum((b for a,b in pieces),F(0)))
    return dict(lower=list(map(str,output_lower)),upper=list(map(str,output_upper)),
        before_installation_lower=list(map(str,left)),before_installation_upper=list(map(str,right)),
        input_dependencies_relaxed=True,installation_normalized=False,
        result='force action box, not a Taylor remainder',floating_execution_enclosed=False,
        native_propagation_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
