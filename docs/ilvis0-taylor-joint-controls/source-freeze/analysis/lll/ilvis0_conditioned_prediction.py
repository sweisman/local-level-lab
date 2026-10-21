# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete prediction using source-bound training acceleration constraints."""
from copy import deepcopy


def refine(training,saved,new_bound,*,reserve):
    from lll.ilvis0_consistent_prediction import rebuild_future
    original=saved['bound'];region=training['region']
    keys=('center','previous_coefficients','acceleration_coefficients','transform_coefficients',
        'reference_binding','shared_binding','acceleration_binding','transform_binding','source_id','time_s')
    if any(new_bound[k]!=original[k] for k in keys):
        raise ValueError('conditioned native expansion or source changed')
    condition=new_bound['conditioning']
    if (condition['applies_only_to_training_region'] is not True
            or condition['reference_binding']!=saved['reference']['binding']
            or condition['region_binding']!=region['binding']):
        raise ValueError('training-conditioned bound required')
    selected=deepcopy(new_bound);choices=[]
    for i in range(3):
        choose_new=new_bound['unshared_remainder'][i]<=original['unshared_remainder'][i]
        source=new_bound if choose_new else original;choices.append(choose_new)
        for key in ('unshared_remainder','position_unshared_remainder','lever_unshared_remainder'):
            if source[key][i]<0:raise ValueError('nonnegative retained allowances required')
            selected[key][i]=source[key][i]
    selected['conditioned_remainder_selected']=choices
    updated=dict(saved,bound=selected)
    envelope=rebuild_future(region,updated,saved['lower'],saved['upper'],reserve=reserve)
    return dict(updated,envelope=envelope)


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_acceleration_projection import project,Allowance
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_transform_audit import audit_case
    from lll.ilvis0_feasible_witness import Region
    from lll.ilvis0_control_shards import _check_continue
    from lll import ilvis0_conditioned_transform_native as candidate
    bundle=read(context.input_path());spec=task['payload'];old=bundle['result'];saved=bundle['future']
    training=bundle['training'];region=training['region']
    if (task['identity']!=old['identity'] or not old['passed'] or old['excluded']
            or spec['maximum_proposals']!=12 or spec['maximum_exact_supports']!=48):
        raise ValueError('complete saved identity and finite proposal/support limits required')
    events=[]
    def persist(record):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:02d}.json',record);events.append(record)
    allowance=Allowance(12,48,persist)
    projection_input=dict(training=training,reference=saved['reference'],lower=saved['lower'],upper=saved['upper'])
    projection=project(**projection_input,reserve=allowance.reserve)
    context.save('acceleration-projection.json',projection)
    condition=ConditionedAcceleration(projection_input,projection,reserve=lambda n:allowance.reserve(0,n))
    case=read(context.input_path(spec['case_key']));config=case['configuration']
    theta=case['theta'];dv=case['dv'];dt=case['dt'];n=len(dt)
    if n!=spec['packets']:raise ValueError('declared packet allowance differs from input')
    box=sector(old['task']['sector'])
    ref=candidate.make_reference(config,theta,dv,dt,lower=box['lower'],upper=box['upper'],center=box['center'])
    condition.match(ref.report(),saved['lower'][:27],saved['upper'][:27])
    context.charge(bound_calls=1,bound_steps=2*n)
    bound=candidate.enclose(config,theta,dv,dt,time=saved['time_s'],lower=saved['lower'][:27],upper=saved['upper'][:27],
        reference=ref,conditioning=condition,maximum_seconds=spec['maximum_bound_seconds'])
    context.save('conditioned-bound.json',plain(bound.report()))
    ordinals=[]
    def reserve(ordinal):
        if ordinal!=len(ordinals)+1 or ordinal>6:raise ValueError('six sequential future proposals required')
        allowance.reserve(1,3);ordinals.append(ordinal)
    future=refine(training,saved,plain(bound.report()),reserve=reserve)
    context.save('training.json',training);context.save('future.json',future)
    # Saved outcomes are checked only after the new prediction is fixed.
    retained=contained=True
    if old['truth_in_sector']:
        point=case['truth']+old['known_shared_error']
        retained=max(Region(saved['lower'],saved['upper'],region['inequality_design'],region['inequality_upper']).slacks(point))<=0
        contained=all(a<=v<=b for a,v,b in zip(future['envelope']['lower'],old['future_truth_m'],future['envelope']['upper']))
    result=dict(identity=task['identity'],task=old['task'],parameter_count=51,truth_in_sector=old['truth_in_sector'],
        contraction=old['contraction'],passed=retained and contained,excluded=False,
        known_truth_retained=retained,known_shared_error=old['known_shared_error'],
        future_truth_evaluated_after_bounds=True,future_truth_m=old['future_truth_m'],
        future_lower_m=future['envelope']['lower'],future_upper_m=future['envelope']['upper'],
        previous_width_m=[b-a for a,b in zip(old['future_lower_m'],old['future_upper_m'])],
        new_width_m=[b-a for a,b in zip(future['envelope']['lower'],future['envelope']['upper'])],
        native_evaluations=0,bound_evaluations=1,reserved_bound_steps=2*n,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if result['passed']:
        allowance.reserve(0,6)
        check=audit_case(result,training,future);context.save('independent-audit.json',check)
        result['exact_supports_checked']=check['exact_supports_checked']
    return plain(dict(result,lp_proposals_reserved=allowance.proposals,exact_supports_reserved=allowance.supports,
        projected_acceleration_radius=projection['norm_change']))
