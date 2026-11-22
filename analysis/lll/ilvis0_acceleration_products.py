# SPDX-License-Identifier: AGPL-3.0-or-later
"""Necessary acceleration consistency with explicit bias/force products."""

from fractions import Fraction as F

from .ilvis0_calibration_consistency import ConsistencyCuts
from .ilvis0_reference_acceleration import AccelerationTerms
from .ilvis0_common_force_transform import ForceTransform
from .ilvis0_rotation_products import product_planes
from .ilvis0_saved_prediction_audit import endpoint


def _range(row, lower, upper):
    terms = [(v*a, v*b) for v,a,b in zip(row, lower, upper, strict=True) if v]
    return sum(min(v) for v in terms), sum(max(v) for v in terms)


def build(acceleration, transform, consistency, lower, upper, *, allowance):
    """Lift nine products without changing the underlying physical box."""
    if (not isinstance(acceleration, AccelerationTerms) or not isinstance(transform, ForceTransform)
            or not isinstance(consistency, ConsistencyCuts)
            or consistency.acceleration_binding!=acceleration.binding
            or consistency.transform_binding!=transform.binding
            or len(lower)!=51 or len(upper)!=51 or F(allowance)<0):
        raise ValueError('bound acceleration, force transform and 51-coordinate box required')
    ref = transform.reference
    center, limits = tuple(map(F, ref.center)), tuple(map(F, ref.limits))
    lo, hi = list(map(F, lower))+[F(0)]*9, list(map(F, upper))+[F(0)]*9
    for i, (a,b) in enumerate(zip(lo[:51],hi[:51],strict=True)):
        want = ((F(ref.lower[i])-center[i], F(ref.upper[i])-center[i])
                if i<27 else (F(-1),F(1)))
        if not a<=want[0]<=0<=want[1]<=b:
            raise ValueError('outer displacement box must cover the original calibration domain')
    force = [F(v)/F(acceleration.period)-limits[12+j]*center[12+j]
             for j,v in enumerate(acceleration.raw_delta_v)]
    jac = transform.jacobian
    caps = tuple(map(F, transform.caps))
    coeffs = consistency.metadata
    equations, planes, products = [], [], []
    for i in range(3):
        constant = F(coeffs['exact_centre_mismatches'][i])
        linear = tuple(map(F, coeffs['exact_linear_mismatches'][i]))
        row = [-v for v in linear]+[F(0)]*33
        acc_cap = F(acceleration.caps[6+i])
        row[39+i] = acc_cap
        relaxation = abs(constant)+F(allowance)*acc_cap
        for j in range(3):
            index = 3*i+j
            matrix = list(map(F, jac[i,j]))+[F(0)]*33
            matrix[42+index] = caps[index]
            bias = [F(0)]*60
            bias[12+j] = limits[12+j]
            matrix_range = _range(matrix,lo,hi)
            bias_range = _range(bias,lo,hi)
            a, b = max(map(abs,matrix_range)), max(map(abs,bias_range))
            row[42+index] = -caps[index]*force[j]
            relaxation += F(allowance)*caps[index]*(abs(force[j])+b)
            # The saved point convention sets the remainder to zero when
            # rotation and gain stay fixed. Cover any residual slope mismatch.
            relaxation += abs(linear[12+j])*max(abs(lo[12+j]),abs(hi[12+j]))
            if a and b:
                x, y = tuple(v/a for v in matrix), tuple(v/b for v in bias)
                u, v = tuple(t/a for t in matrix_range), tuple(t/b for t in bias_range)
                corners = [left*right for left in u for right in v]
                lo[51+index], hi[51+index] = min(corners), max(corners)
                planes.extend(product_planes((F(0),x),u,(F(0),y),v,51+index))
                row[51+index] = a*b
                products.append((x[:51],y[:51]))
            else:
                products.append(((F(0),)*51,(F(0),)*51))
        relaxation += abs(linear[24])*max(abs(lo[24]),abs(hi[24]))
        equations.extend([(row,constant+relaxation), ([-v for v in row],-constant+relaxation)])
    binary_lo, binary_hi = [endpoint(v,False) for v in lo], [endpoint(v,True) for v in hi]
    rows, limits = [], []
    for row, bound in planes+equations:
        output = [float(v) for v in row]
        delta = [F(v)-q for v,q in zip(output,row,strict=True)]
        rounding = _range(delta,list(map(F,binary_lo)),list(map(F,binary_hi)))[1]
        rows.append(output)
        limits.append(endpoint(bound+rounding,True))
    return dict(lower=binary_lo, upper=binary_hi, design=rows, limits=limits,
                products=[[[str(v) for v in row] for row in pair] for pair in products],
                source_binding=ref.binding, map_allowance=float(allowance))


def lift(cuts, point):
    point = tuple(map(F, point))
    if len(point)!=51:
        raise ValueError('complete 51-coordinate calibration required')
    products = [tuple(sum(F(v)*x for v,x in zip(row,point,strict=True) if F(v))
                      for row in pair) for pair in cuts['products']]
    return point+tuple(a*b for a,b in products)
