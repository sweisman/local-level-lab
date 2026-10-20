# SPDX-License-Identifier: AGPL-3.0-or-later
"""Oracle-assisted diagnosis of shared approximation-error blocks.

Known simulated values are supplied deliberately. These conditional ranges
are not an available prediction method or aircraft uncertainty intervals.
"""
BLOCKS=dict(reference_terms=tuple(range(27,33)),acceleration_clock=tuple(range(33,39)),
    acceleration_remainder=tuple(range(39,42)),force_matrix=tuple(range(42,51)))


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_feasible_witness import Region
    from lll.ilvis0_consistent_prediction import rebuild_future
    from lll.ilvis0_transform_audit import audit_case
    from lll.ilvis0_control_shards import _check_continue
    spec=task['payload'];block=spec['block']
    if block not in BLOCKS or spec['maximum_proposals']!=6:raise ValueError('one declared block and six proposals required')
    bundle=read(context.input_path());old=bundle['result'];saved=bundle['future'];training=bundle['training']
    if old['identity']!=spec['source_identity'] or not old['truth_in_sector']:
        raise ValueError('one sealed known-truth sector required')
    audit_case(old,training,saved)
    region=training['region'];left=list(saved['lower']);right=list(saved['upper']);anchor=bundle['anchor']
    exact=Region(left,right,region['inequality_design'],region['inequality_upper'])
    if len(left)!=51 or len(anchor)!=51 or max(exact.slacks(anchor))>0:
        raise ValueError('saved anchor must be exactly feasible in all 51 coordinates')
    for index in BLOCKS[block]:left[index]=right[index]=anchor[index]
    context.save('condition.json',dict(oracle_assisted=True,block=block,indices=list(BLOCKS[block]),
        known_values=[anchor[j] for j in BLOCKS[block]],source_identity=old['identity'],parameter_count=51))
    context.save('training.json',dict(training,oracle_assisted=True,conditional_lower=left,conditional_upper=right))
    reservations=[]
    def reserve(ordinal):
        _check_continue(context.root,context.manifest)
        if ordinal!=len(reservations)+1 or ordinal>6:raise ValueError('six sequential support proposals required')
        context.save(f'proposal-{ordinal:02d}.json',dict(ordinal=ordinal,maximum_seconds=1.,maximum_exact_supports=3))
        reservations.append(ordinal)
    env=rebuild_future(region,saved,left,right,reserve=reserve)
    future=dict(saved,lower=left,upper=right,envelope=env,oracle_assisted=True)
    context.save('future.json',future)
    contained=all(a<=v<=b for a,v,b in zip(env['lower'],old['future_truth_m'],env['upper']))
    source_width=[b-a for a,b in zip(old['future_lower_m'],old['future_upper_m'])]
    width=[b-a for a,b in zip(env['lower'],env['upper'])]
    result=dict(identity=task['identity'],source_identity=old['identity'],task=old['task'],fixed_block=block,
        parameter_count=51,passed=contained,excluded=False,truth_in_sector=True,known_truth_retained=True,
        contraction=dict(lower=left,upper=right),future_truth_evaluated_after_bounds=True,
        future_truth_m=old['future_truth_m'],future_lower_m=env['lower'],future_upper_m=env['upper'],
        source_width_m=source_width,conditional_width_m=width,
        width_ratio=[a/b if b else 1. for a,b in zip(width,source_width)],lp_proposals_reserved=len(reservations),
        oracle_assisted=True,prediction_method_qualified=False,scientific_decision='abstain',
        observational_coverage_qualified=False,native_evaluations=0,original_reads=0,optimizer_starts=0)
    if contained:
        check=audit_case(result,training,future);context.save('independent-audit.json',check)
        result['exact_supports_checked']=check['exact_supports_checked']
    return result
