# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved future support with all 51 original and 27 arithmetic coordinates."""
from copy import deepcopy
from fractions import Fraction as F


def extend(training,saved,cuts):
    old=training['region']
    if (old['parameter_count']!=51 or cuts['parameter_count']!=78
            or cuts['original_parameter_count']!=51 or cuts['new_physical_parameters']!=0
            or cuts['reference_binding']!=saved['reference']['parent']['binding'] or cuts['source_id']!=old['source_id']
            or cuts['transform_binding']!=saved['reference']['transform']['binding']
            or cuts['lower'][:51]!=saved['lower'] or cuts['upper'][:51]!=saved['upper']):
        raise ValueError('source-bound complete extension of the original domain required')
    region=deepcopy(old)
    region.update(parameter_count=78,original_parameter_count=51,new_physical_parameters=0,
        lower=deepcopy(cuts['lower']),upper=deepcopy(cuts['upper']),center=old['center']+[0.]*27,
        inequality_design=[row+[0.]*27 for row in old['inequality_design']]+deepcopy(cuts['design']),
        inequality_upper=old['inequality_upper']+cuts['inequality_upper'],rotation_product_binding=cuts['binding'])
    return region


def _row(saved,scale,axis):
    b=saved['bound'];blocks=[saved['jacobian'][axis],b['previous_coefficients'][axis],
        b['acceleration_coefficients'][axis],b['transform_coefficients'][axis]]
    if [len(v) for v in blocks]!=[27,6,9,9]:raise ValueError('all original coefficient columns required')
    return [v*scale for block in blocks for v in block]+[0.]*27


def rebuild(region,saved,lower,upper,*,reserve):
    from lll import ilvis0_affine_support as support
    from lll.ilvis0_saved_prediction_audit import endpoint
    if region['parameter_count']!=78 or len(lower)!=78 or len(upper)!=78:
        raise ValueError('complete extended prediction domain required')
    result=deepcopy(saved);certificates=[];left=[];right=[]
    for axis,scale in enumerate(region['coordinate_scale']):
        row=_row(saved,scale,axis);answers=[];old=saved['envelope']['certificates'][axis]
        for sign,key in ((1,'upper_multipliers'),(-1,'lower_multipliers')):
            reserve(2*axis+(1 if sign==1 else 2))
            objective=[sign*v for v in row]
            proposed=support.propose(lower,upper,region['inequality_design'],region['inequality_upper'],objective)
            padding=len(region['inequality_upper'])-len(old[key])
            if padding<0:raise ValueError('original constraints cannot disappear')
            previous=support.upper(lower,upper,region['inequality_design'],region['inequality_upper'],
                objective,old[key]+[0.]*padding)
            answers.append(min((proposed,previous),key=lambda c:c['exact_upper']))
        high,low=answers
        shift=(F(saved['nominal'][axis])-F(region['origin'][axis]))*F(scale)-sum(
            (F(v)*F(c) for v,c in zip(row,region['center'],strict=True)),F(0))
        radius=F(saved['bound']['unshared_remainder'][axis])*F(scale)+F(region['arithmetic_allowance'])
        left.append(endpoint(shift-low['exact_upper']-radius,False));right.append(endpoint(shift+high['exact_upper']+radius,True))
        if left[-1]<saved['envelope']['lower'][axis] or right[-1]>saved['envelope']['upper'][axis]:
            raise ValueError('necessary joint constraints must not enlarge the original range')
        certificates.append(dict(upper=str(high['exact_upper']),negated_lower=str(low['exact_upper']),
            upper_multipliers=high['multipliers'].tolist(),lower_multipliers=low['multipliers'].tolist()))
    result.update(parameter_count=78,original_parameter_count=51,lower=list(lower),upper=list(upper))
    result['envelope'].update(parameter_count=78,original_parameter_count=51,lower=left,upper=right,
        certificates=certificates,rotation_product_binding=region['rotation_product_binding'],future_truth_used=False)
    return result


def audit(original_training,original_future,region,future,cuts):
    """Independent exact support verification with unchanged-source checks."""
    from lll.ilvis0_saved_prediction_audit import support,endpoint
    old=original_training['region'];env=future['envelope']
    if (region['parameter_count']!=78 or future['parameter_count']!=78 or env['parameter_count']!=78
            or region['original_parameter_count']!=51 or future['original_parameter_count']!=51
            or region['center']!=old['center']+[0.]*27 or region['future_truth_used'] or env['future_truth_used']
            or region['binding']!=old['binding'] or region['source_id']!=old['source_id']
            or any(region[k]!=old[k] for k in ('coordinate_scale','origin','arithmetic_allowance'))
            or region['lower']!=cuts['lower'] or region['upper']!=cuts['upper']
            or region['rotation_product_binding']!=cuts['binding'] or env['rotation_product_binding']!=cuts['binding']
            or cuts['reference_binding']!=original_future['reference']['parent']['binding']
            or cuts['transform_binding']!=original_future['reference']['transform']['binding']
            or region['inequality_design']!=[row+[0.]*27 for row in old['inequality_design']]+cuts['design']
            or region['inequality_upper']!=old['inequality_upper']+cuts['inequality_upper']):
        raise ValueError('complete unchanged-source lifted region required')
    if any(future[k]!=original_future[k] for k in ('reference','bound','nominal','jacobian','fixed_center','time_s')):
        raise ValueError('original native expression or error allowance changed')
    if (len(future['lower'])!=78 or len(future['upper'])!=78
            or any(not a<=b<=c<=d for a,b,c,d in zip(cuts['lower'],future['lower'],future['upper'],cuts['upper'],strict=True))):
        raise ValueError('complete source-bound extended domain required')
    rows=[]
    for axis,scale in enumerate(region['coordinate_scale']):
        # Extract independently from the preserved blocks rather than calling
        # the proposal builder's row-construction helper.
        b=original_future['bound']
        blocks=(original_future['jacobian'][axis],b['previous_coefficients'][axis],
            b['acceleration_coefficients'][axis],b['transform_coefficients'][axis])
        if tuple(map(len,blocks))!=(27,6,9,9):raise ValueError('original coefficient block missing')
        objective=[scale*v for block in blocks for v in block]+[0.]*27;cert=env['certificates'][axis]
        args=(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'])
        high=support(*args,objective,cert['upper_multipliers']);low=support(*args,[-v for v in objective],cert['lower_multipliers'])
        if high!=F(cert['upper']) or low!=F(cert['negated_lower']):raise ValueError('exact extended support mismatch')
        shift=(F(original_future['nominal'][axis])-F(region['origin'][axis]))*F(scale)-sum(
            (F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
        remainder=F(original_future['bound']['unshared_remainder'][axis])*F(scale)
        arithmetic=F(region['arithmetic_allowance'])
        if remainder<0 or arithmetic<0:raise ValueError('negative retained error allowance')
        left=endpoint(shift-low-remainder-arithmetic,False);right=endpoint(shift+high+remainder+arithmetic,True)
        if left!=env['lower'][axis] or right!=env['upper'][axis]:raise ValueError('outward extended endpoints changed')
        rows.append(dict(axis=axis,width_m=right-left,affine_width_m=float(high+low),
            unshared_width_m=float(2*remainder),arithmetic_width_m=float(2*arithmetic)))
    return dict(passed=True,parameter_count=78,original_parameter_count=51,physical_parameter_count=27,
        exact_supports_checked=6,axes=rows,native_evaluations=0,original_reads=0,
        observational_coverage_qualified=False,scientific_decision='abstain')


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_rotation_products import build,lift
    from lll.ilvis0_training_box import contract
    from lll.ilvis0_saved_prediction_audit import endpoint
    from lll.ilvis0_acceleration_projection import Allowance
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());old=bundle['result'];saved=bundle['future'];training=bundle['training']
    spec=task['payload'];case=read(context.input_path(spec['case_key']))
    if (old['identity']!=task['identity'] or not old['passed'] or old['excluded']
            or spec['maximum_proposals']!=6 or spec['maximum_exact_supports']!=24):
        raise ValueError('complete saved identity and fixed support allowance required')
    box=sector(old['task']['sector'])
    reference=ReferenceErrors(case['configuration'],box['lower'],box['upper'],box['center'],
        source_id=training['region']['source_id'])
    transform=ForceTransform(reference)
    if (reference.binding!=saved['reference']['parent']['binding']
            or transform.report()!=saved['reference']['transform']):raise ValueError('saved matrix source/reference changed')
    cuts=build(transform.report(),initial_r=reference.initial_r.tolist(),limits=reference.limits.tolist(),
        physical_center=reference.center.tolist(),lower=saved['lower'],upper=saved['upper'],
        reference_binding=reference.binding,source_id=reference.source_id,numerical_allowance=1e-8)
    region=extend(training,saved,cuts)
    minimum=[endpoint(sum((F(v)*F(a if v>=0 else b) for v,a,b in zip(row,region['lower'],region['upper'])),F(0)),False)
        for row in region['inequality_design']]
    contraction=plain(contract(region['lower'],region['upper'],region['inequality_design'],minimum,
        region['inequality_upper'],maximum_passes=8))
    context.save('cuts.json',cuts);context.save('training.json',dict(training,region=region))
    common=dict(identity=task['identity'],task=old['task'],parameter_count=78,original_parameter_count=51,
        physical_parameter_count=27,new_physical_parameters=0,truth_in_sector=old['truth_in_sector'],
        contraction=contraction,native_evaluations=0,bound_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if contraction['empty']:
        return dict(common,passed=not old['truth_in_sector'],excluded=True,
            known_truth_retained=not old['truth_in_sector'],lp_proposals_reserved=0,
            exact_supports_reserved=0,exact_supports_checked=0)
    events=[]
    def persist(record):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:02d}.json',record);events.append(record)
    allowance=Allowance(6,24,persist);ordinals=[]
    def reserve(ordinal):
        if ordinal!=len(ordinals)+1 or ordinal>6:raise ValueError('six ordered proposals required')
        allowance.reserve(1,3);ordinals.append(ordinal)
    future=rebuild(region,saved,contraction['lower'],contraction['upper'],reserve=reserve)
    context.save('future.json',future)
    allowance.reserve(0,6);checked=audit(training,saved,region,future,cuts)
    context.save('independent-audit.json',checked)
    retained=contained=True
    if old['truth_in_sector']:
        point=lift(cuts,case['truth']+old['known_shared_error'])
        retained=all(F(a)<=x<=F(b) for a,x,b in zip(future['lower'],point,future['upper']))
        retained=retained and max(sum((F(a)*x for a,x in zip(row,point)),F(0))-F(b)
            for row,b in zip(region['inequality_design'],region['inequality_upper']))<=0
        contained=all(a<=x<=b for a,x,b in zip(future['envelope']['lower'],old['future_truth_m'],future['envelope']['upper']))
    return dict(common,passed=retained and contained,excluded=False,known_truth_retained=retained,
        future_truth_evaluated_after_bounds=True,future_truth_m=old['future_truth_m'],
        future_lower_m=future['envelope']['lower'],future_upper_m=future['envelope']['upper'],
        known_shared_error=old['known_shared_error'],lp_proposals_reserved=allowance.proposals,
        exact_supports_reserved=allowance.supports,exact_supports_checked=checked['exact_supports_checked'],
        previous_width_m=[b-a for a,b in zip(old['future_lower_m'],old['future_upper_m'])],
        new_width_m=[b-a for a,b in zip(future['envelope']['lower'],future['envelope']['upper'])])
