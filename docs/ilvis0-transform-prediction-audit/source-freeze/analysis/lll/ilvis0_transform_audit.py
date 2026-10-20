# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent rational audit of supplied 51-column prediction certificates.

Standard library only. No integration, LP proposals or original observations.
This verifies internal mathematics, not physical coverage or measured accuracy.
"""
from fractions import Fraction as F
import json
import math
from .ilvis0_saved_prediction_audit import support, endpoint


def audit_case(result,training,future):
    region=training['region'];bound=future['bound'];env=future['envelope'];ref=future['reference']
    if (any(r['parameter_count']!=51 for r in (result,region,future,env))
            or bound['enclosure_parameter_count']!=51
            or not result['passed'] or result['excluded']
            or region['future_truth_used'] or env['future_truth_used']
            or not result['future_truth_evaluated_after_bounds']
            or not result['known_truth_retained']):
        raise ValueError('complete passing 51-column, training-only evidence required')
    if (region['binding']!=ref['binding'] or env['shared_binding']!=ref['binding']
            or bound['reference_binding']!=ref['binding']
            or bound['shared_binding']!=ref['parent']['binding']
            or bound['acceleration_binding']!=ref['acceleration']['binding']
            or bound['transform_binding']!=ref['transform']['binding']
            or bound['transform_reference']['binding']!=ref['transform']['binding']
            or bound['clock_transform']['matrix_binding']!=ref['transform']['binding']
            or any(r['source_id']!=region['source_id'] for r in (bound,env))):
        raise ValueError('saved source or shared-block binding changed')
    force=region['force_source_id']
    if (not isinstance(force,str) or len(force)!=64 or any(c not in '0123456789abcdef' for c in force)
            or env['force_source_id']!=force or bound['force_integrals']['source_id']!=force
            or bound['clock_transform']['source_id']!=force):
        raise ValueError('saved force/clock source changed')
    if (future['time_s']!=bound['time_s'] or future['lower']!=result['contraction']['lower']
            or future['upper']!=result['contraction']['upper']
            or region['center'][:27]!=future['fixed_center']):
        raise ValueError('saved domain, time or expansion changed')
    scale=region['coordinate_scale']
    if len(scale)!=3 or any(not math.isfinite(v) or v<=0 for v in scale):
        raise ValueError('three positive fixed coordinate scales required')
    if len(region['center'])!=51 or len(region['origin'])!=3:
        raise ValueError('all expansion columns and origin coordinates required')
    ratios=[]
    for a,b,c,d in zip(region['lower'],region['upper'],future['lower'],future['upper'],strict=True):
        if not all(math.isfinite(v) for v in (a,b,c,d)) or not a<=c<=d<=b:
            raise ValueError('contracted box escapes supplied domain')
        ratios.append(float((F(d)-F(c))/(F(b)-F(a))) if b!=a else 1.)
    if len(ratios)!=51:raise ValueError('physical or shared-error columns missing')
    rows=[]
    for axis in range(3):
        blocks=[future['jacobian'][axis],bound['previous_coefficients'][axis],
            bound['acceleration_coefficients'][axis],bound['transform_coefficients'][axis]]
        if [len(v) for v in blocks]!=[27,6,9,9]:raise ValueError('all four coefficient blocks required')
        objective=[v*scale[axis] for block in blocks for v in block]
        certificate=env['certificates'][axis]
        args=(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'])
        high=support(*args,objective,certificate['upper_multipliers'])
        low=support(*args,[-v for v in objective],certificate['lower_multipliers'])
        if high!=F(certificate['upper']) or low!=F(certificate['negated_lower']):
            raise ValueError('saved exact support certificate changed')
        shift=(F(future['nominal'][axis])-F(region['origin'][axis]))*F(scale[axis])-sum(
            (F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
        remainder=F(bound['unshared_remainder'][axis])*F(scale[axis])
        arithmetic=F(region['arithmetic_allowance'])
        if remainder<0 or arithmetic<0:raise ValueError('negative error allowance')
        left=endpoint(shift-low-remainder-arithmetic,False)
        right=endpoint(shift+high+remainder+arithmetic,True)
        if (left!=env['lower'][axis] or right!=env['upper'][axis]
                or left!=result['future_lower_m'][axis] or right!=result['future_upper_m'][axis]):
            raise ValueError('saved future endpoints do not follow certificates')
        if result['truth_in_sector'] and not left<=result['future_truth_m'][axis]<=right:
            raise ValueError('known in-sector future truth not retained')
        width=right-left
        rows.append(dict(axis=axis,width_m=width,affine_width_m=float(high+low),
            unshared_width_m=float(2*remainder),arithmetic_width_m=float(2*arithmetic),
            position_width_m=2*bound['position_unshared_remainder'][axis]*scale[axis],
            lever_width_m=2*bound['lever_unshared_remainder'][axis]*scale[axis],
            unshared_fraction=float(2*remainder)/width if width>0 else None))
    return dict(passed=True,identity=result['identity'],model=result['task']['model'],
        profile=result['task']['profile'],sector=result['task']['sector'],exact_supports_checked=6,
        parameter_width_ratios=ratios,narrowed_physical_columns=[i for i,r in enumerate(ratios[:27]) if r<1.],
        narrowed_auxiliary_columns=[i+27 for i,r in enumerate(ratios[27:]) if r<1.],axes=rows,
        original_reads=0,optimizer_starts=0,native_evaluations=0,
        observational_coverage_qualified=False,scientific_decision='abstain')


def evaluate(task,context):
    bundle=json.loads(context.input_path().read_text())
    if bundle['result']['identity']!=task['identity']:raise ValueError('saved audit task/input mismatch')
    return audit_case(**bundle)
