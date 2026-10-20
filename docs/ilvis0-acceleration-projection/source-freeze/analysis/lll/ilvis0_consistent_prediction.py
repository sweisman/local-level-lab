# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only prediction after qualified calibration-consistency cuts."""


def rebuild_future(region,saved,lower,upper,*,reserve):
    from fractions import Fraction as F
    from lll import ilvis0_affine_support as support
    from lll.ilvis0_saved_prediction_audit import endpoint
    scale=region['coordinate_scale'];bound=saved['bound'];certificates=[];left=[];right=[]
    for axis in range(3):
        blocks=[saved['jacobian'][axis],bound['previous_coefficients'][axis],
            bound['acceleration_coefficients'][axis],bound['transform_coefficients'][axis]]
        if [len(v) for v in blocks]!=[27,6,9,9]:raise ValueError('all 51 saved coefficients required')
        row=[v*scale[axis] for block in blocks for v in block];answers=[]
        old=saved['envelope']['certificates'][axis]
        for direction,label in ((1,'upper_multipliers'),(-1,'lower_multipliers')):
            ordinal=2*axis+(1 if direction==1 else 2);reserve(ordinal)
            objective=[direction*v for v in row]
            proposal=support.propose(lower,upper,region['inequality_design'],region['inequality_upper'],objective)
            padded=list(old[label])+[0.]*(len(region['inequality_upper'])-len(old[label]))
            previous=support.upper(lower,upper,region['inequality_design'],region['inequality_upper'],objective,padded)
            answers.append(min((proposal,previous),key=lambda v:v['exact_upper']))
        high,low=answers
        shift=(F(saved['nominal'][axis])-F(region['origin'][axis]))*F(scale[axis])-sum(
            (F(v)*F(c) for v,c in zip(row,region['center'],strict=True)),F(0))
        radius=F(bound['unshared_remainder'][axis])*F(scale[axis])+F(region['arithmetic_allowance'])
        left.append(endpoint(shift-low['exact_upper']-radius,False))
        right.append(endpoint(shift+high['exact_upper']+radius,True))
        if left[-1]<saved['envelope']['lower'][axis] or right[-1]>saved['envelope']['upper'][axis]:
            raise ValueError('necessary cuts must not enlarge preserved future ranges')
        certificates.append(dict(upper=str(high['exact_upper']),negated_lower=str(low['exact_upper']),
            upper_multipliers=high['multipliers'].tolist(),lower_multipliers=low['multipliers'].tolist()))
    return dict(saved['envelope'],lower=left,upper=right,certificates=certificates,future_truth_used=False)


def evaluate(task,context):
    import copy
    from fractions import Fraction as F
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_calibration_consistency import build,exact_slacks
    from lll.ilvis0_training_box import contract
    from lll.ilvis0_saved_prediction_audit import endpoint
    from lll.ilvis0_transform_audit import audit_case
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());spec=task['payload'];case=read(context.input_path(spec['case_key']))
    old=bundle['result'];saved=bundle['future'];region=copy.deepcopy(bundle['training']['region'])
    if old['identity']!=task['identity'] or spec['maximum_proposals']!=6:
        raise ValueError('saved identity or six-proposal allowance changed')
    cfg=case['configuration'];box=sector(old['task']['sector'])
    ref=make_reference(cfg,case['theta'],case['dv'],case['dt'],lower=box['lower'],upper=box['upper'],center=box['center'])
    if (ref.binding!=region['binding'] or ref.parent.source_id!=region['source_id']
            or ref.report()!=saved['reference']):raise ValueError('saved source/reference changed')
    cut=build(ref.acceleration,ref.transform)
    region['inequality_design']+=cut.design.tolist();region['inequality_upper']+=cut.upper.tolist()
    left=saved['lower'];right=saved['upper']
    minimum=[endpoint(sum((F(v)*F(a if v>=0 else b) for v,a,b in zip(row,left,right)),F(0)),False)
        for row in region['inequality_design']]
    contraction=contract(left,right,region['inequality_design'],minimum,region['inequality_upper'],maximum_passes=8)
    context.save('cuts.json',cut.report())
    context.save('training.json',dict(bundle['training'],region=region,consistency_binding=cut.binding))
    common=dict(identity=task['identity'],task=old['task'],parameter_count=51,truth_in_sector=old['truth_in_sector'],
        contraction=plain(contraction),native_evaluations=0,bound_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if contraction['empty']:
        return dict(common,passed=not old['truth_in_sector'],excluded=True,
            known_truth_retained=not old['truth_in_sector'],lp_proposals_reserved=0,exact_supports_checked=0)
    left=contraction['lower'].tolist();right=contraction['upper'].tolist();reserved=[]
    def reserve(ordinal):
        _check_continue(context.root,context.manifest)
        if ordinal!=len(reserved)+1 or ordinal>6:raise ValueError('six sequential support proposals required')
        context.save(f'proposal-{ordinal:02d}.json',dict(ordinal=ordinal,maximum_exact_certificates=3,maximum_seconds=1.))
        reserved.append(ordinal)
    env=rebuild_future(region,saved,left,right,reserve=reserve)
    future=dict(saved,lower=left,upper=right,envelope=env)
    context.save('future.json',future)
    # Known physical truth and future outcomes are accessed only after saving
    # the training constraints and revised prediction. No new oracle is called.
    retained=True;contained=True;cut_retained=True
    if old['truth_in_sector']:
        truth=np.r_[case['truth'],old['known_shared_error']]
        retained=bool(np.all(np.array(left)<=truth) and np.all(truth<=right))
        cut_retained=max(exact_slacks(cut,truth))<=0
        contained=all(a<=v<=b for a,v,b in zip(env['lower'],old['future_truth_m'],env['upper']))
    result=dict(common,passed=retained and contained and cut_retained,excluded=False,known_truth_retained=retained,
        known_cuts_retained=cut_retained,known_shared_error=old['known_shared_error'],
        future_truth_evaluated_after_bounds=True,future_truth_m=old['future_truth_m'],
        future_lower_m=env['lower'],future_upper_m=env['upper'],lp_proposals_reserved=len(reserved),
        previous_width_m=[b-a for a,b in zip(old['future_lower_m'],old['future_upper_m'])],
        new_width_m=[b-a for a,b in zip(env['lower'],env['upper'])])
    if result['passed']:
        check=audit_case(result,dict(region=region),future)
        context.save('independent-audit.json',check);result['exact_supports_checked']=check['exact_supports_checked']
    return plain(result)
