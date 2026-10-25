# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent standard-library verification of saved 42-column predictions.

No integration, optimization, numerical packages or original observations.
The proof verifies supplied inequalities, not their physical error assumptions.
"""
from fractions import Fraction as F
import json
import math


def support(lower,upper,design,bound,objective,multipliers):
    n=len(lower)
    if (not n or len(upper)!=n or len(objective)!=n or len(design)!=len(bound) or len(multipliers)!=len(bound)
            or any(len(row)!=n for row in design) or any(a>b for a,b in zip(lower,upper))
            or any(v<0 for v in multipliers)):
        raise ValueError('complete ordered box, all columns and nonnegative dual required')
    values=list(lower)+list(upper)+list(bound)+list(objective)+list(multipliers)+[v for row in design for v in row]
    if any(not math.isfinite(v) for v in values):raise ValueError('finite exact-certificate inputs required')
    weights=[F(v) for v in multipliers];value=sum((w*F(b) for w,b in zip(weights,bound)),F(0))
    for axis,c in enumerate(objective):
        residue=F(c)-sum((weight*F(row[axis]) for weight,row in zip(weights,design)),F(0))
        value+=residue*F(upper[axis] if residue>=0 else lower[axis])
    return value


def endpoint(value,up):
    result=float(value)
    if not math.isfinite(result):raise ValueError('finite outward endpoint required')
    if (up and F(result)<value) or (not up and F(result)>value):result=math.nextafter(result,math.inf if up else -math.inf)
    return result


def verify_joint_envelope(region,saved):
    """Verify a 51-column envelope without requiring or opening known truth."""
    bound=saved['bound'];env=saved['envelope']
    if (any(v['parameter_count']!=51 for v in (region,saved,env))
            or bound['enclosure_parameter_count']!=51
            or region['future_truth_used'] is not False or env['future_truth_used'] is not False
            or region['binding']!=env['shared_binding'] or region['binding']!=bound['reference_binding']
            or region['binding']!=saved['reference']['binding']
            or region['source_id']!=bound['source_id'] or region['source_id']!=env['source_id']
            or region['force_source_id']!=env['force_source_id'] or saved['time_s']!=bound['time_s']):
        raise ValueError('complete unchanged-source training-only joint envelope required')
    if (any(len(saved[k])!=51 or len(region[k])!=51 for k in ('lower','upper'))
            or len(region['center'])!=51 or region['center'][:27]!=saved['fixed_center']
            or any(not a<=b<=c<=d for a,b,c,d in zip(region['lower'],saved['lower'],saved['upper'],region['upper']))
            or any(len(region[k])!=3 for k in ('coordinate_scale','origin'))
            or any(len(saved[k])!=3 for k in ('nominal','jacobian'))
            or any(len(env[k])!=3 for k in ('lower','upper','certificates'))):
        raise ValueError('all source columns, expansion coordinates and three axes required')
    args=(saved['lower'],saved['upper'],region['inequality_design'],region['inequality_upper'])
    arithmetic=F(region['arithmetic_allowance']);widths=[]
    if arithmetic<0:raise ValueError('nonnegative arithmetic allowance required')
    for axis,scale in enumerate(region['coordinate_scale']):
        if not math.isfinite(scale) or scale<=0:raise ValueError('positive finite coordinate scales required')
        blocks=(saved['jacobian'][axis],bound['previous_coefficients'][axis],
            bound['acceleration_coefficients'][axis],bound['transform_coefficients'][axis])
        if tuple(map(len,blocks))!=(27,6,9,9):raise ValueError('all four coefficient blocks required')
        row=[scale*v for block in blocks for v in block];cert=env['certificates'][axis]
        high=support(*args,row,cert['upper_multipliers'])
        low=support(*args,[-v for v in row],cert['lower_multipliers'])
        if high!=F(cert['upper']) or low!=F(cert['negated_lower']):raise ValueError('exact joint support certificate changed')
        shift=(F(saved['nominal'][axis])-F(region['origin'][axis]))*F(scale)
        shift-=sum((F(v)*F(c) for v,c in zip(row,region['center'],strict=True)),F(0))
        remainder=F(bound['unshared_remainder'][axis])*F(scale)
        if remainder<0:raise ValueError('nonnegative reconstruction allowance required')
        radius=remainder+arithmetic
        left=endpoint(shift-low-radius,False);right=endpoint(shift+high+radius,True)
        if left!=env['lower'][axis] or right!=env['upper'][axis] or left>right:
            raise ValueError('exact outward joint endpoint changed')
        widths.append(endpoint(F(right)-F(left),True))
    return dict(passed=True,parameter_count=51,exact_supports_checked=6,width_m=widths,
        native_evaluations=0,observational_coverage_qualified=False,scientific_decision='abstain')


def audit_case(result,training,future):
    region=training['region'];bound=future['bound'];envelope=future['envelope'];scale=region['coordinate_scale']
    if (result['parameter_count']!=42 or region['parameter_count']!=42 or future['parameter_count']!=42
            or region['binding']!=future['reference']['binding'] or envelope['shared_binding']!=region['binding']
            or bound['acceleration_binding']!=region['binding'] or bound['source_id']!=region['source_id']
            or future['time_s']!=envelope.get('time_s',future['time_s']) or region['future_truth_used'] or envelope['future_truth_used']):
        raise ValueError('saved prediction identity, full column count or no-future-input contract changed')
    if (future['lower']!=result['contraction']['lower'] or future['upper']!=result['contraction']['upper']
            or region['center'][:27]!=future['fixed_center']):raise ValueError('saved domain/expansion changed')
    ratios=[]
    for a,b,c,d in zip(region['lower'],region['upper'],future['lower'],future['upper'],strict=True):
        if not a<=c<=d<=b:raise ValueError('contracted box escapes original domain')
        ratios.append(float((F(d)-F(c))/(F(b)-F(a))) if b!=a else 1.)
    if len(ratios)!=42:raise ValueError('physical or common-error columns missing')
    rows=[]
    for axis in range(3):
        raw=future['jacobian'][axis]+bound['previous_coefficients'][axis]+bound['acceleration_coefficients'][axis]
        objective=[v*scale[axis] for v in raw]
        if len(objective)!=42:raise ValueError('future objective must keep 42 columns')
        certificate=envelope['certificates'][axis]
        high=support(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'],objective,certificate['upper_multipliers'])
        low=support(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'],[-v for v in objective],certificate['lower_multipliers'])
        if high!=F(certificate['upper']) or low!=F(certificate['negated_lower']):raise ValueError('saved exact support certificate changed')
        shift=(F(future['nominal'][axis])-F(region['origin'][axis]))*F(scale[axis])-sum((F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
        remainder=F(bound['unshared_remainder'][axis])*F(scale[axis]);arithmetic=F(region['arithmetic_allowance'])
        left=endpoint(shift-low-remainder-arithmetic,False);right=endpoint(shift+high+remainder+arithmetic,True)
        if left!=envelope['lower'][axis] or right!=envelope['upper'][axis]:raise ValueError('saved future endpoints do not follow certificates')
        if left!=result['future_lower_m'][axis] or right!=result['future_upper_m'][axis]:raise ValueError('saved result endpoints changed')
        width=right-left
        rows.append(dict(axis=axis,width_m=width,affine_width_m=float(high+low),unshared_width_m=float(2*remainder),
            arithmetic_width_m=float(2*arithmetic),position_width_m=2*bound['position_unshared_remainder'][axis]*scale[axis],
            lever_width_m=2*bound['lever_unshared_remainder'][axis]*scale[axis],
            unshared_fraction=float(2*remainder)/width if width>0 else None))
    return dict(passed=True,identity=result['identity'],model=result['task']['model'],profile=result['task']['profile'],
        sector=result['task']['sector'],exact_supports_checked=6,parameter_width_ratios=ratios,
        narrowed_physical_columns=[i for i,r in enumerate(ratios[:27]) if r<1.],
        narrowed_auxiliary_columns=[i+27 for i,r in enumerate(ratios[27:]) if r<1.],axes=rows,
        original_reads=0,optimizer_starts=0,native_evaluations=0,observational_coverage_qualified=False,scientific_decision='abstain')


def evaluate(task,context):
    # The single frozen bundle contains one already-sealed case and its evidence.
    bundle=json.loads(context.input_path().read_text())
    if bundle['result']['identity']!=task['identity']:raise ValueError('saved audit task/input mismatch')
    return audit_case(**bundle)
