# SPDX-License-Identifier: AGPL-3.0-or-later
"""Closed physical subboxes with the original source, expressions and radii."""
from copy import deepcopy
from fractions import Fraction as F


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_physical_partition import audit as audit_partition
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_coupled_map import StaticMap
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_coupled_prediction import build,audit_cuts,extend,audit_future
    from lll.ilvis0_product_prediction import rebuild
    from lll.ilvis0_training_box import contract
    from lll.ilvis0_rotation_products import lift
    from lll.ilvis0_saved_prediction_audit import endpoint
    bundle=read(context.input_path());old=bundle['result'];training=bundle['training'];saved=bundle['future']
    spec=task['payload'];case=read(context.input_path(spec['case_key']));index=spec['child_index']
    limits=dict(partition_audits=1,setups=1,intervals=2,coupling_audits=1,
        contractions=1,proposals=6,supports=24,truth_audits=1)
    if (spec['limits']!=limits or old['identity']!=spec['parent_identity']
            or task['identity']!=old['identity']+f'-xy-{index}' or not old['passed'] or old['excluded']
            or old['parameter_count']!=78 or case['configuration']['model']!=old['task']['model']
            or case['configuration']['profile']!=old['task']['profile']):
        raise ValueError('complete original parent, registered child and finite allowance required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(partition_audits=1))
    partition=bundle['partition'];cover=audit_partition(partition,saved['lower'][:27],saved['upper'][:27],axes=(0,1))
    if (type(index)!=int or not 0<=index<len(partition['children'])
            or spec['parent_children']!=cover['children']):raise ValueError('one registered covered child required')
    context.save('partition-audit.json',cover);child=partition['children'][index]
    narrowed=deepcopy(saved);narrowed['lower'][:27]=child['lower'];narrowed['upper'][:27]=child['upper']
    box=sector(old['task']['sector']);budget.reserve(dict(setups=1))
    # Reconstruct the original reference, not a new reference/radius for the child.
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    model=StaticMap(reference,expected_report=saved['reference'],numerical_allowance=3e-10)
    cuts=build(model,child['lower'],child['upper'],reserve=lambda:budget.reserve(dict(intervals=1)))
    context.save('coupling.json',cuts);context.save('source-map.json',model.report())
    budget.reserve(dict(coupling_audits=1))
    proof=audit_cuts(cuts,model.report(),child['lower'],child['upper']);context.save('coupling-audit.json',proof)
    region=extend(training,narrowed,cuts);context.save('training.json',dict(training,region=region))
    budget.reserve(dict(contractions=1))
    minimum=[endpoint(sum((F(v)*F(a if v>=0 else b) for v,a,b in zip(row,region['lower'],region['upper'],strict=True) if v),F(0)),False)
        for row in region['inequality_design']]
    contraction=plain(contract(region['lower'],region['upper'],region['inequality_design'],minimum,
        region['inequality_upper'],maximum_passes=8));context.save('contraction.json',contraction)
    common=dict(identity=task['identity'],parent_identity=old['identity'],child_index=index,parent_children=cover['children'],
        task=old['task'],parameter_count=78,original_parameter_count=51,physical_parameter_count=27,
        new_physical_parameters=0,truth_in_sector=old['truth_in_sector'],contraction=contraction,
        coupling_rows_checked=48,coupled_map_binding=cuts['binding'],source_map_binding=model.binding,
        native_evaluations=0,bound_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
    future=None
    if not contraction['empty']:
        ordinals=[]
        def reserve(ordinal):
            if ordinal!=len(ordinals)+1 or ordinal>6:raise ValueError('six ordered signed supports required')
            budget.reserve(dict(proposals=1,supports=3));ordinals.append(ordinal)
        future=rebuild(region,narrowed,contraction['lower'],contraction['upper'],reserve=reserve)
        future['envelope']['coupled_map_binding']=cuts['binding'];context.save('future.json',future)
        budget.reserve(dict(supports=6))
        checked=audit_future(training,narrowed,region,future,cuts,cut_audit=proof)
        context.save('independent-audit.json',checked)
    # Membership is inspected only after the child's range or empty proof is fixed.
    budget.reserve(dict(truth_audits=1))
    within=bool(old['truth_in_sector']) and all(F(a)<=F(v)<=F(b)
        for a,v,b in zip(child['lower'],case['truth'],child['upper'],strict=True))
    retained=not within
    if within and future is not None:
        point=lift(bundle['product_cuts'],case['truth']+old['known_shared_error'])
        retained=all(F(a)<=v<=F(b) for a,v,b in zip(future['lower'],point,future['upper'],strict=True))
        retained=retained and max(sum((F(a)*v for a,v in zip(row,point,strict=True) if a),F(0))-F(b)
            for row,b in zip(region['inequality_design'],region['inequality_upper'],strict=True))<=0
        retained=retained and all(a<=v<=b for a,v,b in zip(future['envelope']['lower'],old['future_truth_m'],future['envelope']['upper'],strict=True))
    context.save('truth-audit.json',dict(truth_in_child=within,known_truth_retained=retained,
        generated_membership_evaluated_after_bounds=True,shared_boundaries_retained=True))
    result=dict(common,passed=retained,excluded=contraction['empty'],truth_in_child=within,
        known_truth_retained=retained,work=budget.counts,generated_membership_evaluated_after_bounds=True,
        lp_proposals_reserved=budget.counts['proposals'],exact_supports_reserved=budget.counts['supports'],
        exact_supports_checked=0 if future is None else 6)
    if future is not None:
        result.update(future_lower_m=future['envelope']['lower'],future_upper_m=future['envelope']['upper'],
            future_truth_m=old['future_truth_m'],known_shared_error=old['known_shared_error'],
            previous_width_m=[b-a for a,b in zip(old['future_lower_m'],old['future_upper_m'])])
    return result
