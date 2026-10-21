# SPDX-License-Identifier: AGPL-3.0-or-later
"""Training-conditioned direct-source remainder bounds in the complete joint schema."""
from copy import deepcopy
from fractions import Fraction as F
from lll.ilvis0_saved_prediction_audit import endpoint
from lll.ilvis0_directional_prediction import build_future,audit_future,audit_training


def allowances(packets,epochs):
    queries=epochs+1
    return dict(setups=1,proofs=1,parent_supports=6,training_audits=6*epochs,contractions=1,
        proposals=6,supports=24,truth_audits=1,source_setups=queries,source_steps=queries*packets,
        source_body_bounds=queries*packets,source_derivative_setups=queries,source_derivative_steps=queries*packets,source_point_setups=queries,source_point_steps=queries*packets,source_direct_steps=queries*packets)


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_direct_interface import bridge,training_rows
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_conditioned_subdomain import SubdomainAcceleration
    from lll import ilvis0_direct_native as native
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_training_box import contract
    bundle=read(context.input_path());saved=bundle['future'];training=bundle['training'];old=bundle['result']
    spec=task['payload'];case=read(context.input_path(spec['case_key']));n=len(case['dt']);epochs=len(training['times_s'])
    limits=allowances(n,epochs)
    if (spec['limits']!=limits or n!=spec['packets'] or not old['passed'] or old['excluded']
            or old['identity']!=task['identity'] or saved['parameter_count']!=78 or not 1<=epochs<=6
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
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    directory=context.root/"shards"/f"{context.shard:03d}"/"kernels";directory.mkdir(parents=True,exist_ok=True)
    sources=context.root/"source-freeze/analysis/lll"
    arithmetic=configure_backend(directory,source_directory=sources)
    source_kernel,source_compilation=load_stream(directory,source_directory=sources)
    derivative_kernel,derivative_compilation=load_kernel(directory,source_directory=sources)
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    point_kernel,point_compilation=load_point(directory,source_directory=sources)
    if any(metadata["compiler"]!=spec["compiler"] for metadata in (arithmetic,source_compilation,derivative_compilation,point_compilation)):
        raise ValueError("frozen compiler changed")
    context.save("compilation.json",dict(arithmetic=arithmetic,source=source_compilation,derivatives=derivative_compilation,point=point_compilation))
    reports=[];bounds=0;reference_steps=body_bounds=derivative_steps=direct_steps=0
    queries=list(zip(training['times_s'],training['nominal']))+[(saved['time_s'],saved['nominal'])]
    for time,center in queries:
        budget.reserve(dict(source_setups=1,source_steps=n,source_body_bounds=n,source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n))
        context.charge(bound_calls=1,bound_steps=9*n);bounds+=1
        raw=native.enclose(config,case['theta'],case['dv'],case['dt'],time=time,lower=lo,upper=hi,
            reference=reference,conditioning=proof,maximum_seconds=spec['maximum_bound_seconds'],source_kernel=source_kernel,derivative_kernel=derivative_kernel,point_kernel=point_kernel)
        reference_steps+=raw.metadata['source_reference_steps'];body_bounds+=raw.metadata['rounded_source_prefixes'];derivative_steps+=raw.metadata['source_derivative_steps'];direct_steps+=raw.metadata['source_direct_steps']
        converted=bridge(raw,reference,proof,center,training['region']['coordinate_scale'])
        report=converted.report();context.save(f'bound-{bounds:02d}.json',report);reports.append(report)
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
        bound_evaluations=bounds,reserved_bound_steps=9*n*bounds,source_reference_steps=reference_steps,source_body_bounds=body_bounds,source_derivative_steps=derivative_steps,source_direct_steps=direct_steps,native_evaluations=0,original_reads=0,
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
