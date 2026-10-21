# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fresh directional-bound prediction; old results remain separate evidence."""
from copy import deepcopy
from fractions import Fraction as F
from lll.ilvis0_saved_prediction_audit import endpoint


def build_future(region,saved,bound,lower,upper,*,reserve):
    from lll import ilvis0_affine_support as support
    from lll.ilvis0_product_prediction import _row
    if region['parameter_count']!=78 or len(lower)!=78 or len(upper)!=78:
        raise ValueError('all original 78 enclosure coordinates required')
    result=deepcopy(saved);result['bound']=deepcopy(bound);certificates=[];left=[];right=[]
    for axis,scale in enumerate(region['coordinate_scale']):
        row=_row(result,scale,axis)
        if row!=_row(saved,scale,axis):raise ValueError('native/common coefficient basis changed')
        answers=[];old=saved['envelope']['certificates'][axis]
        for sign,key in ((1,'upper_multipliers'),(-1,'lower_multipliers')):
            reserve(2*axis+(1 if sign==1 else 2));objective=[sign*v for v in row]
            proposed=support.propose(lower,upper,region['inequality_design'],region['inequality_upper'],objective)
            padding=len(region['inequality_upper'])-len(old[key])
            if padding<0:raise ValueError('inherited constraints cannot disappear')
            previous=support.upper(lower,upper,region['inequality_design'],region['inequality_upper'],objective,old[key]+[0.]*padding)
            answers.append(min((proposed,previous),key=lambda c:c['exact_upper']))
        high,low=answers
        shift=(F(saved['nominal'][axis])-F(region['origin'][axis]))*F(scale)-sum(
            (F(v)*F(c) for v,c in zip(row,region['center'],strict=True)),F(0))
        remainder=F(bound['unshared_remainder'][axis])*F(scale)+F(region['arithmetic_allowance'])
        if remainder<0:raise ValueError('nonnegative retained remainder required')
        left.append(endpoint(shift-low['exact_upper']-remainder,False));right.append(endpoint(shift+high['exact_upper']+remainder,True))
        certificates.append(dict(upper=str(high['exact_upper']),negated_lower=str(low['exact_upper']),
            upper_multipliers=high['multipliers'].tolist(),lower_multipliers=low['multipliers'].tolist()))
    result.update(lower=list(lower),upper=list(upper))
    result['envelope'].update(lower=left,upper=right,certificates=certificates,
        directional_reference_binding=bound.get('reference_binding'),fresh_range_may_be_wider=True)
    return result


def audit_future(region,saved,bound,future):
    from lll.ilvis0_saved_prediction_audit import support
    if (region['parameter_count']!=78 or len(future['lower'])!=78 or len(future['upper'])!=78
            or future['bound']!=bound or future['reference']!=saved['reference']
            or future['nominal']!=saved['nominal'] or future['jacobian']!=saved['jacobian']
            or future['fixed_center']!=saved['fixed_center'] or future['time_s']!=saved['time_s']
            or future['envelope']['future_truth_used']):
        raise ValueError('complete unchanged-source fresh prediction required')
    if any(not a<=b<=c<=d for a,b,c,d in zip(region['lower'],future['lower'],future['upper'],region['upper'],strict=True)):
        raise ValueError('contracted physical/common box escapes the training region')
    axes=[]
    for axis,scale in enumerate(region['coordinate_scale']):
        blocks=(saved['jacobian'][axis],bound['previous_coefficients'][axis],bound['acceleration_coefficients'][axis],bound['transform_coefficients'][axis])
        old=saved['bound'];old_blocks=(saved['jacobian'][axis],old['previous_coefficients'][axis],old['acceleration_coefficients'][axis],old['transform_coefficients'][axis])
        if tuple(map(len,blocks))!=(27,6,9,9) or blocks!=old_blocks:raise ValueError('complete original coefficient blocks required')
        objective=[v*scale for block in blocks for v in block]+[0.]*27
        cert=future['envelope']['certificates'][axis];args=(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'])
        high=support(*args,objective,cert['upper_multipliers']);low=support(*args,[-v for v in objective],cert['lower_multipliers'])
        if high!=F(cert['upper']) or low!=F(cert['negated_lower']):raise ValueError('fresh exact certificate changed')
        shift=(F(saved['nominal'][axis])-F(region['origin'][axis]))*F(scale)-sum(
            (F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
        radius=F(bound['unshared_remainder'][axis])*F(scale)+F(region['arithmetic_allowance'])
        if radius<0:raise ValueError('negative fresh allowance')
        left=endpoint(shift-low-radius,False);right=endpoint(shift+high+radius,True)
        if left!=future['envelope']['lower'][axis] or right!=future['envelope']['upper'][axis]:
            raise ValueError('fresh outward endpoint changed')
        axes.append(dict(axis=axis,width_m=right-left))
    return dict(passed=True,exact_supports_checked=6,axes=axes,parameter_count=78,
        native_evaluations=0,original_reads=0,observational_coverage_qualified=False,scientific_decision='abstain')


def audit_training(training,saved,reports,region):
    old=training['region'];n=len(training['times_s']);count=3*n
    if (old['parameter_count']!=78 or region['parameter_count']!=78 or len(reports)!=n
            or region['lower']!=saved['lower'] or region['upper']!=saved['upper']
            or any(region.get(k)!=v for k,v in old.items() if k not in ('lower','upper','inequality_design','inequality_upper'))
            or region['inequality_design'][:len(old['inequality_design'])]!=old['inequality_design']
            or region['inequality_upper'][:len(old['inequality_upper'])]!=old['inequality_upper']):
        raise ValueError('all inherited training constraints and metadata must remain')
    matrix=[];left=[];right=[]
    for epoch,report in enumerate(reports):
        if report['time_s']!=training['times_s'][epoch] or report['center']!=training['nominal'][epoch]:
            raise ValueError('new training source epoch or center changed')
        for axis,unit in enumerate(old['coordinate_scale']):
            blocks=(training['jacobian'][epoch][axis],report['previous_coefficients'][axis],
                report['acceleration_coefficients'][axis],report['transform_coefficients'][axis])
            if tuple(map(len,blocks))!=(27,6,9,9):raise ValueError('missing new training coefficient block')
            row=[v*unit for block in blocks for v in block]+[0.]*27
            if row[:51]!=old['design'][epoch*3+axis]:raise ValueError('new training basis differs')
            shift=sum((F(v)*F(c) for v,c in zip(row,old['center'],strict=True)),F(0))
            observed=(F(training['observations'][epoch][axis])-F(training['nominal'][epoch][axis]))*F(unit)
            if report['unshared_remainder'][axis]<0 or old['arithmetic_allowance']<0:raise ValueError('negative training allowance')
            radius=F(report['unshared_remainder'][axis])*F(unit)+F(.001)+F(old['arithmetic_allowance'])
            matrix.append(row);left.append(endpoint(shift+observed-radius,False));right.append(endpoint(shift+observed+radius,True))
    expected=matrix+[[-v for v in row] for row in matrix]
    if (region['inequality_design'][len(old['inequality_design']):]!=expected
            or region['inequality_upper'][len(old['inequality_upper']):]!=right+[-v for v in left]
            or len(expected)!=2*count):raise ValueError('independent exact training-row reconstruction failed')
    return dict(passed=True,rows_checked=2*count,parameter_count=78,exact_supports_checked=0,native_evaluations=0)


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_directional_interface import bridge,training_rows
    from lll.ilvis0_directional_acceleration import DirectionalAcceleration
    from lll import ilvis0_directional_native as native
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_training_box import contract
    bundle=read(context.input_path());saved=bundle['future'];training=bundle['training'];old=bundle['result']
    spec=task['payload'];case=read(context.input_path(spec['case_key']));n=len(case['dt']);epochs=len(training['times_s'])
    limits=dict(setups=1,proofs=1,training_audits=6*epochs,contractions=1,proposals=6,supports=24,truth_audits=1)
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
    proof=DirectionalAcceleration(reference,lo,hi);context.save('directional-proof.json',proof.report())
    reports=[];bounds=0
    queries=list(zip(training['times_s'],training['nominal']))+[(saved['time_s'],saved['nominal'])]
    for time,center in queries:
        context.charge(bound_calls=1,bound_steps=2*n);bounds+=1
        raw=native.enclose(config,case['theta'],case['dv'],case['dt'],time=time,lower=lo,upper=hi,
            reference=reference,conditioning=proof,maximum_seconds=spec['maximum_bound_seconds'])
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
        bound_evaluations=bounds,reserved_bound_steps=2*n*bounds,native_evaluations=0,original_reads=0,
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
