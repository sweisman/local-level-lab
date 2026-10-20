# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary joint-rotation constraints with 27 arithmetic product coordinates.

All original 51 coordinates remain. McCormick planes relax product equalities;
neither those planes nor Gram constraints establish a physically realizable
proper rotation. Exact construction/outward export is not full-program roundoff.
"""
from fractions import Fraction as F
import hashlib
import json
import math

PAIRS=((0,0),(1,1),(2,2),(0,1),(0,2),(1,2))


def _f(value):
    try:result=F(value)
    except (ValueError,TypeError,OverflowError):raise ValueError('finite exact input required') from None
    return result


def _add(a,b,scale=F(1)):
    return a[0]+scale*b[0],tuple(x+scale*y for x,y in zip(a[1],b[1],strict=True))


def _scale(a,scale):return scale*a[0],tuple(scale*v for v in a[1])


def _variable(index,n=78):return F(0),tuple(F(int(i==index)) for i in range(n))


def _range(a,lower,upper):
    return (a[0]+sum((v*(lo if v>=0 else hi) for v,lo,hi in zip(a[1],lower,upper,strict=True)),F(0)),
        a[0]+sum((v*(hi if v>=0 else lo) for v,lo,hi in zip(a[1],lower,upper,strict=True)),F(0)))


def _product_range(a,b):
    values=[x*y for x in a for y in b];return min(values),max(values)


def product_planes(x,x_bounds,y,y_bounds,product_index):
    """Four exact inequalities for z=x*y, allowing affine x and y."""
    xl,xh=map(_f,x_bounds);yl,yh=map(_f,y_bounds)
    if xl>xh or yl>yh or len(x[1])!=len(y[1]):raise ValueError('ordered aligned product domain required')
    z=_variable(product_index,len(x[1]));planes=[]
    for a,b,value,sign in ((xl,yl,xl*yl,1),(xh,yh,xh*yh,1),
            (xh,yl,xh*yl,-1),(xl,yh,xl*yh,-1)):
        expression=_add(_add(_scale(y,a),_scale(x,b)),z,F(-1))
        expression=_scale(expression,F(sign))
        planes.append((expression[1],F(sign)*value-expression[0]))
    return planes


def build(transform,*,initial_r,limits,physical_center,lower,upper,reference_binding,source_id,numerical_allowance=0.):
    from .ilvis0_saved_prediction_audit import endpoint
    from .ilvis0_exact_scale import sqrt_upper
    if (transform['reference_binding']!=reference_binding or not isinstance(source_id,str) or not source_id
            or len(lower)!=51 or len(upper)!=51 or len(limits)!=27 or len(physical_center)!=27
            or len(initial_r)!=3 or any(len(row)!=3 for row in initial_r)
            or len(transform['center'])!=3 or any(len(row)!=3 for row in transform['center'])
            or len(transform['jacobian'])!=3 or any(len(row)!=3 for row in transform['jacobian'])
            or any(len(col)!=27 for row in transform['jacobian'] for col in row) or len(transform['caps'])!=9):
        raise ValueError('complete source-bound 51-coordinate matrix expression required')
    lo=list(map(_f,lower));hi=list(map(_f,upper));lim=list(map(_f,limits));z=list(map(_f,physical_center))
    caps=list(map(_f,transform['caps']));eps=_f(numerical_allowance)
    if (any(a>b for a,b in zip(lo,hi)) or min(lim+caps+[eps])<0
            or any(lim[18+j]*lo[18+j]<=-1 for j in range(3))):
        raise ValueError('ordered finite domain, nonnegative caps and positive gain denominators required')
    initial=[list(map(_f,row)) for row in initial_r]
    defect=[sum((initial[k][i]*initial[k][j] for k in range(3)),F(0))-int(i==j)
        for i in range(3) for j in range(3)]
    gram_error=F(sqrt_upper(sum((v*v for v in defect),F(0))))
    tolerance=gram_error+eps
    matrix=[];matrix_ranges=[]
    for i in range(3):
        row=[];ranges=[]
        for j in range(3):
            jac=list(map(_f,transform['jacobian'][i][j]));coeff=jac+[F(0)]*51
            coeff[42+3*i+j]=caps[3*i+j]
            offset=_f(transform['center'][i][j])-sum((a*b for a,b in zip(jac,z)),F(0))
            expression=(offset,tuple(coeff));row.append(expression)
            ranges.append(_range((offset,tuple(coeff[:51])),lo,hi))
        matrix.append(row);matrix_ranges.append(ranges)
    gains=[(F(0),tuple(lim[18+j] if k==18+j else F(0) for k in range(78))) for j in range(3)]
    gain_ranges=[(lim[18+j]*lo[18+j],lim[18+j]*hi[18+j]) for j in range(3)]
    product_ranges=[_product_range(matrix_ranges[i][j],gain_ranges[j]) for i in range(3) for j in range(3)]
    lo += [v[0] for v in product_ranges]+[F(0)]*18
    hi += [v[1] for v in product_ranges]+[F(0)]*18
    b=[[_add(matrix[i][j],_variable(51+3*i+j)) for j in range(3)] for i in range(3)]
    b_ranges=[[_range(b[i][j],lo,hi) for j in range(3)] for i in range(3)]
    planes=[]
    for i in range(3):
        for j in range(3):
            planes+=product_planes(matrix[i][j],matrix_ranges[i][j],gains[j],gain_ranges[j],51+3*i+j)
        for pair,(j,k) in enumerate(PAIRS):
            index=60+6*i+pair;left,right=b_ranges[i][j],b_ranges[i][k]
            bounds=_product_range(left,right)
            if j==k:bounds=(max(F(0),bounds[0]),bounds[1])
            lo[index],hi[index]=bounds
            planes+=product_planes(b[i][j],left,b[i][k],right,index)
            if j==k:
                # The midpoint tangent is also necessary for an exact square.
                midpoint=sum(left)/2
                expression=_add(_scale(b[i][j],2*midpoint),_variable(index),F(-1))
                planes.append((expression[1],midpoint**2-expression[0]))
    for pair,(j,k) in enumerate(PAIRS):
        row=[F(0)]*78
        for i in range(3):row[60+6*i+pair]=F(1)
        target=F(int(j==k))
        planes.append((tuple(row),target+tolerance))
        planes.append((tuple(-v for v in row),-target+tolerance))
    binary_lo=[endpoint(v,False) for v in lo];binary_hi=[endpoint(v,True) for v in hi]
    out_lo=list(map(F,binary_lo));out_hi=list(map(F,binary_hi));design=[];bounds=[];exports=[]
    for row,bound in planes:
        binary=[float(v) for v in row]
        if any(not math.isfinite(v) for v in binary):raise ValueError('finite inequality export required')
        error=sum(((F(v)-q)*(h if F(v)>=q else l) for v,q,l,h in zip(binary,row,out_lo,out_hi)),F(0))
        design.append(binary);bounds.append(endpoint(bound+error,True));exports.append(str(error))
    definition=dict(version='ilvis0-joint-rotation-products-v1',reference_binding=reference_binding,
        source_id=source_id,transform_binding=transform['binding'],lower=binary_lo,upper=binary_hi,
        design=design,inequality_upper=bounds)
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return dict(definition,binding=binding,parameter_count=78,original_parameter_count=51,
        physical_parameter_count=27,new_physical_parameters=0,product_coordinate_count=27,
        reference_gram_defect_bound=str(gram_error),numerical_allowance=str(eps),gram_tolerance=str(tolerance),
        matrix_affine=[dict(constant=str(m[0]),coefficients=[str(v) for v in m[1][:51]]) for row in matrix for m in row],
        gain_limits=[str(v) for v in lim[18:21]],export_allowances=exports,
        exact_product_equalities_enforced=False,physical_realizability_established=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def lift(cuts,point):
    if len(point)!=51:raise ValueError('all original 51 coordinates required')
    x=list(map(_f,point))
    if any(not F(a)<=v<=F(b) for a,v,b in zip(cuts['lower'][:51],x,cuts['upper'][:51])):
        raise ValueError('known-control point outside original domain')
    m=[F(r['constant'])+sum((F(a)*v for a,v in zip(r['coefficients'],x)),F(0)) for r in cuts['matrix_affine']]
    g=[F(cuts['gain_limits'][j])*x[18+j] for j in range(3)]
    p=[m[3*i+j]*g[j] for i in range(3) for j in range(3)];b=[a+c for a,c in zip(m,p)]
    t=[b[3*i+j]*b[3*i+k] for i in range(3) for j,k in PAIRS]
    return tuple(x+p+t)


def slacks(cuts,point):
    if len(point)!=78:raise ValueError('complete lifted 78-coordinate point required')
    x=list(map(_f,point))
    return tuple(sum((F(a)*v for a,v in zip(row,x)),F(0))-F(bound)
        for row,bound in zip(cuts['design'],cuts['inequality_upper'],strict=True))
