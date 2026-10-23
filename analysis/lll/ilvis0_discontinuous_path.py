# SPDX-License-Identifier: AGPL-3.0-or-later
"""Endpoint enclosure allowing explicit residual jumps, including endpoints."""
from fractions import Fraction as F
import hashlib
import json
import math
from .ilvis0_piecewise_trapezoid import enclose as continuous_primitive,_rows


def _jumps(values,count):
    if len(values)!=count:raise ValueError('every declared residual jump requires explicit signed bounds')
    return [_rows(row,3,2,interval=True) for row in values]


def enclose(*,initial,derivative_start,derivative_end,partition,smooth_second_bounds,
            value_jump_bounds,slope_jump_bounds,residual_jump_intervals,endpoint_jump_intervals):
    """Bound r(1) with r' piecewise C2 and all three orders of jumps.

Derivative inputs use the interior one-sided limits at0 and1. Signed residual
jumps are r(c+)-r(c-). The two endpoint intervals describe r(0+)-r(0) and
r(1)-r(1-), respectively. Missing terms are rejected, including explicit zeros.
The caller must prove the complete partition and every supplied bound.
"""
    from .ilvis0_saved_prediction_audit import endpoint
    base=continuous_primitive(initial=initial,derivative_start=derivative_start,derivative_end=derivative_end,
        partition=partition,smooth_second_bounds=smooth_second_bounds,value_jump_bounds=value_jump_bounds,
        slope_jump_bounds=slope_jump_bounds,residual_continuous=True)
    interior=_jumps(residual_jump_intervals,base['interior_boundaries'])
    ends=_jumps(endpoint_jump_intervals,2);all_jumps=interior+ends
    low=[sum((row[i][0] for row in all_jumps),F(0)) for i in range(3)]
    high=[sum((row[i][1] for row in all_jumps),F(0)) for i in range(3)]
    radius=[sum((max(map(abs,row[i])) for row in all_jumps),F(0)) for i in range(3)]
    lower=[F(v)+a for v,a in zip(base['exact_lower'],low)]
    upper=[F(v)+a for v,a in zip(base['exact_upper'],high)]
    total=[F(v)+a for v,a in zip(base['exact_error_radius'],radius)]
    try:
        lo=[endpoint(v,False) for v in lower];hi=[endpoint(v,True) for v in upper]
        rad=[endpoint(v,True) for v in total]
        if not all(math.isfinite(v) for v in lo+hi+rad):raise ValueError('finite output required')
    except (ValueError,OverflowError):raise ValueError('finite outward jump enclosure unsupported') from None
    encode=lambda rows:[[[str(v) for v in interval] for interval in row] for row in rows]
    definition=dict(continuous_primitive_binding=base['input_binding'],
        residual_jump_intervals=encode(interior),endpoint_jump_intervals=encode(ends),
        endpoint_derivatives_are_one_sided=True)
    binding=hashlib.sha256(json.dumps(definition,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    result=dict(base);result.update(version='ilvis0-discontinuous-path-enclosure-v1',
        input_binding=binding,continuous_primitive_binding=base['input_binding'],lower=lo,upper=hi,error_radius=rad,
        exact_lower=list(map(str,lower)),exact_upper=list(map(str,upper)),exact_error_radius=list(map(str,total)),
        exact_residual_jump_lower=list(map(str,low)),exact_residual_jump_upper=list(map(str,high)),
        residual_jump_intervals=definition['residual_jump_intervals'],endpoint_jump_intervals=definition['endpoint_jump_intervals'],
        continuous_residual_assumed=False,continuous_primitive_assumed=True,
        endpoint_derivatives_are_one_sided=True,trajectory_jump_bounds_verified=False)
    return result
