# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact-rational first derivatives of the ideal literal-angle rotation.

This separate component leaves the frozen value-enclosure implementation
unchanged. Input-parameter rounding and a training-source bridge are separate.
"""
from fractions import Fraction as F
from .ilvis0_rotation_roundoff import enclose as values

VERSION='ilvis0-rotation-derivative-rational-v1'


def _skew(vector):
    x,y,z=vector
    return [[F(0),-z,y],[z,F(0),-x],[-y,x,F(0)]]


def _multiply(a,b):
    return [[sum((a[i][k]*b[k][j] for k in range(3)),F(0)) for j in range(3)] for i in range(3)]


def enclose(angle):
    proof=values(angle,[[float(i==j) for j in range(3)] for i in range(3)])
    vector=[F(float(v)) for v in angle];q=F(proof['angle_squared']);order=proof['series_order']
    a=ta=F(1);b=tb=F(1,2);ap=bp=F(0)
    for k in range(1,order+1):
        ta=-ta*q/((2*k)*(2*k+1));tb=-tb*q/((2*k+1)*(2*k+2))
        a+=ta;b+=tb
        if q:ap+=k*ta/q;bp+=k*tb/q
    ea=F(proof['first_omitted_sinc']);eb=F(proof['first_omitted_cosc'])
    if q:
        k=order+1
        if q*(k+1)>k*(2*k+2)*(2*k+3):raise ValueError('decreasing derivative-series tail required')
        eap=k*ea/q;ebp=k*eb/q
    else:ap=F(-1,6);bp=F(-1,24);eap=ebp=F(0)
    skew=_skew(vector);square=_multiply(skew,skew);lower=[];upper=[]
    for axis in range(3):
        direction=[F(0)]*3;direction[axis]=F(1);dskew=_skew(direction)
        first=_multiply(dskew,skew);second=_multiply(skew,dskew)
        dsquare=[[first[i][j]+second[i][j] for j in range(3)] for i in range(3)]
        lo=[];hi=[]
        for i in range(3):
            lrow=[];hrow=[]
            for j in range(3):
                polynomial=a*dskew[i][j]+b*dsquare[i][j]+2*vector[axis]*(ap*skew[i][j]+bp*square[i][j])
                tail=ea*abs(dskew[i][j])+eb*abs(dsquare[i][j])+abs(2*vector[axis])*(
                    eap*abs(skew[i][j])+ebp*abs(square[i][j]))
                lrow.append(str(polynomial-tail));hrow.append(str(polynomial+tail))
            lo.append(lrow);hi.append(hrow)
        lower.append(lo);upper.append(hi)
    return dict(version=VERSION,lower=lower,upper=upper,series_order=order,
        exact_rational_reference=True,libm_accuracy_assumed=False,
        first_omitted_sinc_derivative=str(eap),first_omitted_cosc_derivative=str(ebp),
        initial_source_bridge_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
