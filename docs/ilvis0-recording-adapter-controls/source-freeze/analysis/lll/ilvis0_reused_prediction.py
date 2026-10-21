# SPDX-License-Identifier: AGPL-3.0-or-later
"""Rebuild training/prediction constraints from compatible saved reports only."""
from copy import deepcopy
from fractions import Fraction as F
from lll.ilvis0_saved_prediction_audit import endpoint
from lll.ilvis0_directional_prediction import build_future,audit_future,audit_training


def allowances(epochs,provider_counts):
    if (type(epochs) is not int or not 1<=epochs<=6 or len(provider_counts)!=epochs+1
            or any(type(v) is not int or not 1<=v<=16 for v in provider_counts)):
        raise ValueError('complete finite provider list for every query required')
    return dict(setups=1,proofs=1,parent_supports=6,provenance_reads=4,provider_reads=sum(provider_counts),
        report_merges=epochs+1,training_audits=6*epochs,contractions=1,
        proposals=6,supports=24,truth_audits=1)


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_direct_interface import training_rows
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_conditioned_subdomain import SubdomainAcceleration
    from lll import ilvis0_transform_native as native
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_training_box import contract
    bundle=read(context.input_path());saved=bundle['future'];training=bundle['training'];old=bundle['result']
    spec=task['payload'];case=read(context.input_path(spec['case_key']));n=len(case['dt']);epochs=len(training['times_s'])
    limits=allowances(epochs,[len(v) for v in spec['providers']])
    if (spec['limits']!=limits or n!=spec['packets'] or not old['passed'] or old['excluded']
            or old['identity']!=spec['source_identity'] or saved['parameter_count']!=78 or not 1<=epochs<=6
            or (case['configuration']['model'],case['configuration']['profile'])!=(old['task']['model'],old['task']['profile'])):
        raise ValueError('full fixed saved parent, original inputs and finite work limits required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1));box=sector(old['task']['sector'])
    config=case['configuration'];reference=native.make_reference(config,case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    if reference.report()!=saved['reference'] or reference.report()!=training['reference']:
        raise ValueError('complete original source/reference changed')
    lo=saved['lower'][:27];hi=saved['upper'][:27];budget.reserve(dict(proofs=1))
    condition=read(context.input_path(spec["condition_key"]))
    restricted=deepcopy(training);restricted["region"].update(lower=saved["lower"],upper=saved["upper"])
    if restricted!=condition["child_training"]:raise ValueError("frozen child training region changed")
    parent=ConditionedAcceleration(condition["parent_input"],condition["parent_certificate"],
        reserve=lambda count:budget.reserve(dict(parent_supports=count)))
    proof=SubdomainAcceleration(parent,condition["parent_input"],restricted,lo,hi);proof.match_training(restricted)
    context.save("restricted-proof.json",proof.report())
    from lll.ilvis0_bound_report_reuse import Provider,merge_reports
    import hashlib,json
    environment=hashlib.sha256(json.dumps(context.manifest['environment'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
    if spec['provider_environment_sha256']!=environment:raise ValueError('provider/runtime environment mismatch')
    if len(spec['provider_sources'])!=2:raise ValueError('two explicit qualified provider families required')
    receipts={}
    for source in spec['provider_sources']:
        budget.reserve(dict(provenance_reads=2))
        manifest=read(context.input_path(source['manifest_key']))
        receipt=read(context.input_path(source['receipt_key']))
        if (source['name'] in receipts or manifest['environment']!=context.manifest['environment']
                or not isinstance(receipt.get('artifacts'),dict)):
            raise ValueError('provider family/environment provenance mismatch')
        receipts[source['name']]=receipt['artifacts']
    reports=[];bounds=0
    queries=list(zip(training['times_s'],training['nominal']))+[(saved['time_s'],saved['nominal'])]
    for (time,center),descriptors in zip(queries,spec['providers'],strict=True):
        providers=[]
        for item in descriptors:
            budget.reserve(dict(provider_reads=1))
            record=context.manifest['inputs'][item['key']]
            if (record['sha256']!=item['sha256']
                    or receipts.get(item['source'],{}).get(item['qualified_path'])!=item['sha256']):
                raise ValueError('frozen/published provider hash mismatch')
            providers.append(Provider.from_file(item['name'],context.input_path(item['key']),
                sha256=item['sha256'],environment_sha256=environment))
        budget.reserve(dict(report_merges=1));context.charge(bound_calls=1,bound_steps=0);bounds+=1
        report=merge_reports(providers)
        r=reference.parent
        expected=dict(time_s=time,center=plain(center),source_id=r.source_id,reference_binding=reference.binding,
            shared_binding=r.binding,acceleration_binding=reference.acceleration.binding,
            transform_binding=reference.transform.binding,normalized_center=r.center.tolist(),
            lower=lo,upper=hi,bound_lower=np.minimum(lo,r.center).tolist(),bound_upper=np.maximum(hi,r.center).tolist(),
            previous_caps=r.caps.tolist(),acceleration_caps=reference.acceleration.caps.tolist(),
            retained_acceleration_remainder=reference.acceleration.remainder,
            transform_reference=reference.transform.report(),conditioning=proof.report())
        different=[key for key,value in expected.items() if report.get(key)!=value]
        if different:raise ValueError('provider/current source mismatch: '+', '.join(different))
        context.save(f'bound-{bounds:02d}.json',report);reports.append(report)
    new_rows=training_rows(training,reports[:-1]);region=deepcopy(training['region'])
    region.update(lower=deepcopy(saved['lower']),upper=deepcopy(saved['upper']),
        inequality_design=region['inequality_design']+new_rows['design'],
        inequality_upper=region['inequality_upper']+new_rows['upper'])
    if len(region['inequality_upper'])>1024:raise ValueError('finite row ceiling exceeded')
    budget.reserve(dict(training_audits=6*epochs));checked=audit_training(training,saved,reports[:-1],region)
    context.save('training-audit.json',checked);context.save('training.json',dict(training,region=region))
    budget.reserve(dict(contractions=1))
    minimum=[endpoint(sum((F(v)*F(a if v>=0 else b) for v,a,b in zip(row,region['lower'],region['upper'],strict=True) if v),F(0)),False)
        for row in region['inequality_design']]
    contraction=plain(contract(region['lower'],region['upper'],region['inequality_design'],minimum,region['inequality_upper'],maximum_passes=8))
    context.save('contraction.json',contraction)
    common=dict(identity=task['identity'],task=old['task'],parameter_count=78,physical_parameter_count=27,
        bound_evaluations=bounds,reserved_bound_steps=0,native_evaluations=0,original_reads=0,
        optimizer_starts=0,truth_in_sector=old['truth_in_sector'],contraction=contraction,
        observational_coverage_qualified=False,scientific_decision='abstain')
    future=None
    if not contraction['empty']:
        ordinals=[]
        def reserve(ordinal):
            if ordinal!=len(ordinals)+1 or ordinal>6:raise ValueError('six ordered future proposals required')
            budget.reserve(dict(proposals=1,supports=3));ordinals.append(ordinal)
        future=build_future(region,saved,reports[-1],contraction['lower'],contraction['upper'],reserve=reserve)
        context.save('future.json',future);budget.reserve(dict(supports=6))
        check=audit_future(region,saved,reports[-1],future);context.save('independent-audit.json',check)
    budget.reserve(dict(truth_audits=1));retained=not old['truth_in_sector']
    if old['truth_in_sector'] and future is not None:
        from lll.ilvis0_rotation_products import lift
        point=lift(bundle['product_cuts'],case['truth']+old['known_shared_error'])
        retained=all(F(a)<=v<=F(b) for a,v,b in zip(future['lower'],point,future['upper'],strict=True))
        retained=retained and max(sum((F(a)*v for a,v in zip(row,point,strict=True) if a),F(0))-F(b)
            for row,b in zip(region['inequality_design'],region['inequality_upper'],strict=True))<=0
        retained=retained and all(a<=v<=b for a,v,b in zip(future['envelope']['lower'],old['future_truth_m'],future['envelope']['upper'],strict=True))
    context.save('truth-audit.json',dict(known_truth_retained=retained,truth_in_sector=old['truth_in_sector'],evaluated_after_bounds=True))
    result=dict(common,passed=retained,excluded=contraction['empty'],known_truth_retained=retained,work=budget.counts)
    if future is not None:result.update(future_lower_m=future['envelope']['lower'],future_upper_m=future['envelope']['upper'])
    return result
