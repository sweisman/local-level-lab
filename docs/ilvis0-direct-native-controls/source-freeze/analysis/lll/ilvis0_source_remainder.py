# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact scalar bounds for a direct calibrated rotation-source remainder.

These mathematical components have no source binding or numerical-reference
bridge. Their validity assumes the supplied change/remainder bounds apply to
the same physical parameters. They do not qualify native or observed data.
"""
from fractions import Fraction as F

VERSION='ilvis0-source-product-remainder-v1'


def _nonnegative(values):
    values=tuple(map(F,values))
    if any(v<0 for v in values):raise ValueError('nonnegative finite bounds required')
    return values


def _scalar(center,lower,upper,remainder,**extra):
    if lower>upper or remainder<0:raise ValueError('ordered scalar interval and nonnegative remainder required')
    change=max(abs(lower-center),abs(upper-center))
    return dict(center=str(center),lower=str(lower),upper=str(upper),change=str(change),
        remainder=str(remainder),**{k:str(v) for k,v in extra.items()})


def calibration(raw,period,*,bias_center,gain_center,bias_lower,bias_upper,
        gain_lower,gain_upper,as_rate=False):
    """Bound (raw - bias*period) / (1+gain), optionally divided by period.

    Rows are derivatives with respect to physical bias and gain, rather than
    normalized fit columns. Every calculation uses exact supplied rationals.
    """
    raw,t,b0,g0,bl,bh,gl,gh=map(F,(raw,period,bias_center,gain_center,bias_lower,bias_upper,gain_lower,gain_upper))
    if type(as_rate) is not bool or t<=0 or bl>bh or gl>gh or min(1+gl,1+g0)<=0:
        raise ValueError('positive period/denominators and ordered calibration domain required')
    divisor=t if as_rate else F(1);c0=1+g0;a0=(raw-b0*t)/divisor
    center=a0/c0;db=max(abs(bl-b0),abs(bh-b0));dg=max(abs(gl-g0),abs(gh-g0))
    minimum=min(1+gl,c0)
    remainder=((t/divisor)*db*dg/c0+abs(a0)*dg*dg/(c0*c0))/minimum
    corners=[(raw-b*t)/(1+g)/divisor for b in (bl,bh) for g in (gl,gh)]
    return _scalar(center,min(corners),max(corners),remainder,
        bias_row=-t/divisor/c0,gain_row=-a0/(c0*c0))


def clipped_fraction(query_center,lower,upper,*,start,period):
    """Exact piecewise-linear remainder, preserving the native end convention."""
    q0,lo,hi,s,h=map(F,(query_center,lower,upper,start,period))
    if lo>hi or h<=0:raise ValueError('ordered clock interval and positive packet period required')
    clip=lambda q:max(F(0),min(F(1),(q-s)/h))
    center=clip(q0)
    row=1/h if (s<q0<=s+h) or (s==0 and q0==0) else F(0)
    # The difference from the selected affine row is linear between knots.
    critical=[lo,hi]+[q for q in (s,s+h) if lo<=q<=hi]
    remainder=max(abs(clip(q)-center-row*(q-q0)) for q in critical)
    return _scalar(center,clip(lo),clip(hi),remainder,clock_row=row)


def multiply(first,second):
    """Product Taylor remainder without assuming independent parameters."""
    a,al,ah,da,ra=(F(first[k]) for k in ('center','lower','upper','change','remainder'))
    b,bl,bh,db,rb=(F(second[k]) for k in ('center','lower','upper','change','remainder'))
    if al>ah or bl>bh or min(da,ra,db,rb)<0:raise ValueError('valid scalar change/remainder bounds required')
    if da<max(abs(al-a),abs(ah-a)) or db<max(abs(bl-b),abs(bh-b)):
        raise ValueError('change bound does not cover supplied interval')
    corners=[x*y for x in (al,ah) for y in (bl,bh)]
    remainder=abs(a)*rb+abs(b)*ra+da*db
    return _scalar(a*b,min(corners),max(corners),remainder)


def rotation_prefix(changes,remainders,nominal_norms,*,maximum_packets):
    """Bound a product of genuine skew-exponential rotations about its reference.

    Changes/remainders concern each rotation argument vector, not Euler angles
    extracted from the accumulated orientation. No independence is required.
    """
    if (type(maximum_packets) is not int or not 1<=maximum_packets<=1000000
            or len(changes)!=len(remainders) or len(changes)!=len(nominal_norms)
            or len(changes)>maximum_packets):
        raise ValueError('equal prefix vectors within an explicit finite packet allowance required')
    d=_nonnegative(changes);r=_nonnegative(remainders);n=_nonnegative(nominal_norms)
    total=sum(d,F(0))
    return dict(change=str(min(F(2),total)),remainder=str(sum(r,F(0))+total*total/2),
        nominal_departure=str(min(F(2),sum(n,F(0)))),packets=len(d),
        genuine_rotation_inputs_required=True,reference_bridge_qualified=False)


def force_products(*,mount_norm,nominal_departure,force_norm,mount_change,
        mount_remainder,prefix_change,prefix_remainder,force_change,force_remainder):
    """Bound ideal first-order remainders of R f and R (P-I) f in operator norm."""
    s,p0,f0,dR,rR,dP,rP,df,rf=_nonnegative((mount_norm,nominal_departure,force_norm,
        mount_change,mount_remainder,prefix_change,prefix_remainder,force_change,force_remainder))
    a=rR*f0+s*rf+dR*df
    terms=dict(mount=rR*p0*f0,prefix=s*rP*f0,force=s*p0*rf,
        mount_prefix=dR*dP*f0,mount_force=dR*p0*df,prefix_force=s*dP*df,
        triple=dR*dP*df)
    return dict(a_remainder=str(a),b_remainder=str(sum(terms.values(),F(0))),
        b_terms={k:str(v) for k,v in terms.items()},version=VERSION,
        reference_bridge_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
