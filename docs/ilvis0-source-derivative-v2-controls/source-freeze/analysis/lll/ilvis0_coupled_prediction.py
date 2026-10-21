# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved prediction supports constrained by a complete static calibration map."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
import math


def _binding(value):
    return hashlib.sha256(json.dumps({k:v for k,v in value.items() if k!='binding'},
        sort_keys=True,allow_nan=False).encode()).hexdigest()


def build(model,lower,upper,*,reserve):
    from lll.ilvis0_interval_calibration import couple
    if len(lower)!=27 or len(upper)!=27:raise ValueError('complete physical box required')
    lo=list(map(float,lower));hi=list(map(float,upper));center=[float((F(a)+F(b))/2) for a,b in zip(lo,hi)]
    reserve();bounds=model.bound(lo,hi)
    reserve();origin=model.bound(center,center)
    rows=couple(bounds,origin,lo,hi,center);report=model.report()
    cuts=dict(version='ilvis0-complete-static-map-prediction-v1',parameter_count=51,
        physical_lower=lo,physical_upper=hi,center=center,design=rows['design'],upper=rows['upper'],
        source_id=report['source_id'],reference_binding=report['reference_binding'],map_binding=report['binding'],
        proof=dict(derivatives=[[[g.lo,g.hi] for g in v.derivative] for v in bounds],
            center_values=[[v.value.lo,v.value.hi] for v in origin]))
    cuts['binding']=_binding(cuts)
    return cuts


def audit_cuts(cuts,map_report,lower,upper):
    """Independent exact reconstruction; no interval-map or support calls."""
    from lll.ilvis0_saved_prediction_audit import endpoint
    if (cuts['binding']!=_binding(cuts) or cuts['map_binding']!=map_report['binding']
            or cuts['reference_binding']!=map_report['reference_binding'] or cuts['source_id']!=map_report['source_id']
            or cuts['physical_lower']!=list(lower) or cuts['physical_upper']!=list(upper)
            or cuts['parameter_count']!=51 or len(lower)!=27 or len(upper)!=27):
        raise ValueError('unchanged source-bound complete coupling proof required')
    lo=list(map(F,lower));hi=list(map(F,upper));center=list(map(F,cuts['center']))
    midpoint=[float((a+b)/2) for a,b in zip(lo,hi)]
    if cuts['center']!=midpoint or any(not a<=c<=b for a,c,b in zip(lo,center,hi)):
        raise ValueError('fixed physical midpoint required')
    derivative=cuts['proof']['derivatives'];origin=cuts['proof']['center_values']
    if (len(derivative)!=24 or any(len(row)!=27 or any(len(g)!=2 for g in row) for row in derivative)
            or len(origin)!=24 or any(len(v)!=2 for v in origin)
            or len(cuts['design'])!=48 or len(cuts['upper'])!=48):
        raise ValueError('all map derivatives and center ranges required')
    distance=[max(c-a,b-c) for a,c,b in zip(lo,center,hi)]
    for index,(gradient,point) in enumerate(zip(derivative,origin,strict=True)):
        intervals=[tuple(map(F,g)) for g in gradient];at=list(map(F,point))
        if at[0]>at[1] or any(a>b for a,b in intervals):raise ValueError('ordered derivative and center intervals required')
        slope=[float((a+b)/2) for a,b in intervals]
        if not all(math.isfinite(v) for v in slope):raise ValueError('finite slope midpoint required')
        radius=sum((max(abs(F(v)-a),abs(b-F(v)))*d for v,(a,b),d in zip(slope,intervals,distance)),F(0))
        shift=sum((F(v)*c for v,c in zip(slope,center)),F(0))
        high=at[1]-shift+radius;negative_low=-at[0]+shift+radius
        row=[-v for v in slope]+[float(j==index) for j in range(24)]
        if (cuts['design'][2*index]!=row or cuts['design'][2*index+1]!=[-v for v in row]
                or cuts['upper'][2*index]!=endpoint(high,True)
                or cuts['upper'][2*index+1]!=endpoint(negative_low,True)):
            raise ValueError('exact coupling export changed')
    return dict(passed=True,rows=48,binding=cuts['binding'],source_id=cuts['source_id'],
        interval_map_evaluations=0,exact_supports=0)


def extend(training,saved,cuts):
    old=training['region']
    if (old['parameter_count']!=78 or saved['parameter_count']!=78
            or cuts['reference_binding']!=old['binding'] or cuts['reference_binding']!=saved['reference']['binding']
            or cuts['source_id']!=old['source_id'] or len(saved['lower'])!=78 or len(saved['upper'])!=78
            or cuts['physical_lower']!=saved['lower'][:27] or cuts['physical_upper']!=saved['upper'][:27]
            or cuts['binding']!=_binding(cuts)):
        raise ValueError('complete original source and contained coupling domain required')
    if any(not a<=b<=c<=d for a,b,c,d in zip(old['lower'],saved['lower'],saved['upper'],old['upper'],strict=True)):
        raise ValueError('previous contained prediction domain required')
    region=deepcopy(old)
    region.update(lower=deepcopy(saved['lower']),upper=deepcopy(saved['upper']),
        inequality_design=deepcopy(old['inequality_design'])+[row+[0.]*27 for row in cuts['design']],
        inequality_upper=old['inequality_upper']+cuts['upper'],coupled_map_binding=cuts['binding'])
    if len(region['inequality_design'])>1024:raise ValueError('finite 1024-row contraction limit exceeded')
    return region


def audit_future(training,saved,region,future,cuts,*,cut_audit):
    from lll.ilvis0_saved_prediction_audit import support,endpoint
    expected=extend(training,saved,cuts)
    if (region!=expected or cut_audit.get('binding')!=cuts['binding'] or not cut_audit.get('passed')
            or cut_audit.get('rows')!=48 or future['parameter_count']!=78
            or future['envelope']['parameter_count']!=78 or future['envelope']['future_truth_used']
            or future['envelope']['coupled_map_binding']!=cuts['binding']):
        raise ValueError('unchanged complete source extension and preverified coupling required')
    mutable={'lower','upper','envelope'}
    if any(future.get(k)!=v for k,v in saved.items() if k not in mutable):
        raise ValueError('original future expression changed')
    env=saved['envelope'];new=future['envelope'];mutable_env={'lower','upper','certificates','coupled_map_binding'}
    if any(new.get(k)!=v for k,v in env.items() if k not in mutable_env):
        raise ValueError('original future error metadata changed')
    if (len(future['lower'])!=78 or len(future['upper'])!=78
            or any(not a<=b<=c<=d for a,b,c,d in zip(saved['lower'],future['lower'],future['upper'],saved['upper'],strict=True))):
        raise ValueError('complete contained future domain required')
    axes=[]
    for axis,scale in enumerate(region['coordinate_scale']):
        b=saved['bound'];blocks=[saved['jacobian'][axis],b['previous_coefficients'][axis],
            b['acceleration_coefficients'][axis],b['transform_coefficients'][axis]]
        if list(map(len,blocks))!=[27,6,9,9]:raise ValueError('every original coefficient column required')
        objective=[v*scale for block in blocks for v in block]+[0.]*27;certificate=new['certificates'][axis]
        args=(future['lower'],future['upper'],region['inequality_design'],region['inequality_upper'])
        high=support(*args,objective,certificate['upper_multipliers'])
        negative_low=support(*args,[-v for v in objective],certificate['lower_multipliers'])
        if high!=F(certificate['upper']) or negative_low!=F(certificate['negated_lower']):
            raise ValueError('new exact support mismatch')
        shift=(F(saved['nominal'][axis])-F(region['origin'][axis]))*F(scale)-sum(
            (F(v)*F(c) for v,c in zip(objective,region['center'],strict=True)),F(0))
        remainder=F(b['unshared_remainder'][axis])*F(scale);arithmetic=F(region['arithmetic_allowance'])
        if remainder<0 or arithmetic<0:raise ValueError('nonnegative retained allowances required')
        left=endpoint(shift-negative_low-remainder-arithmetic,False);right=endpoint(shift+high+remainder+arithmetic,True)
        if left!=new['lower'][axis] or right!=new['upper'][axis]:raise ValueError('outward future endpoints changed')
        if left<env['lower'][axis] or right>env['upper'][axis]:raise ValueError('necessary constraints widened the original range')
        axes.append(dict(axis=axis,width_m=right-left))
    return dict(passed=True,parameter_count=78,physical_parameter_count=27,exact_supports_checked=6,
        coupling_rows_preverified=48,axes=axes,observational_coverage_qualified=False,scientific_decision='abstain')


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_coupled_map import StaticMap
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_product_prediction import rebuild
    from lll.ilvis0_training_box import contract
    from lll.ilvis0_rotation_products import lift
    from lll.ilvis0_saved_prediction_audit import endpoint
    bundle=read(context.input_path());old=bundle['result'];training=bundle['training'];saved=bundle['future']
    spec=task['payload'];case=read(context.input_path(spec['case_key']))
    limits=dict(setups=1,intervals=2,coupling_audits=1,contractions=1,proposals=6,supports=24,truth_audits=1)
    if (spec['limits']!=limits or old['identity']!=task['identity'] or not old['passed'] or old['excluded']
            or old['parameter_count']!=78 or case['configuration']['model']!=old['task']['model']
            or case['configuration']['profile']!=old['task']['profile']):
        raise ValueError('complete original generated identity and finite allowance required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);box=sector(old['task']['sector'])
    budget.reserve(dict(setups=1))
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    model=StaticMap(reference,expected_report=saved['reference'],numerical_allowance=3e-10)
    cuts=build(model,saved['lower'][:27],saved['upper'][:27],reserve=lambda:budget.reserve(dict(intervals=1)))
    context.save('coupling.json',cuts);context.save('source-map.json',model.report())
    budget.reserve(dict(coupling_audits=1))
    proof=audit_cuts(cuts,model.report(),saved['lower'][:27],saved['upper'][:27])
    context.save('coupling-audit.json',proof)
    region=extend(training,saved,cuts)
    context.save('training.json',dict(training,region=region))
    budget.reserve(dict(contractions=1))
    minimum=[endpoint(sum((F(v)*F(a if v>=0 else b) for v,a,b in zip(row,region['lower'],region['upper'],strict=True) if v),F(0)),False)
        for row in region['inequality_design']]
    contraction=plain(contract(region['lower'],region['upper'],region['inequality_design'],minimum,
        region['inequality_upper'],maximum_passes=8))
    common=dict(identity=task['identity'],task=old['task'],parameter_count=78,original_parameter_count=51,
        physical_parameter_count=27,new_physical_parameters=0,truth_in_sector=old['truth_in_sector'],
        contraction=contraction,coupled_map_binding=cuts['binding'],source_map_binding=model.binding,
        coupling_rows_checked=48,native_evaluations=0,bound_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
    if contraction['empty']:
        return dict(common,passed=not old['truth_in_sector'],excluded=True,
            known_truth_retained=not old['truth_in_sector'],work=budget.counts,
            lp_proposals_reserved=0,exact_supports_reserved=0,exact_supports_checked=0)
    ordinals=[]
    def reserve(ordinal):
        if ordinal!=len(ordinals)+1 or ordinal>6:raise ValueError('six ordered signed supports required')
        budget.reserve(dict(proposals=1,supports=3));ordinals.append(ordinal)
    future=rebuild(region,saved,contraction['lower'],contraction['upper'],reserve=reserve)
    future['envelope']['coupled_map_binding']=cuts['binding'];context.save('future.json',future)
    budget.reserve(dict(supports=6))
    checked=audit_future(training,saved,region,future,cuts,cut_audit=proof)
    context.save('independent-audit.json',checked)
    retained=contained=True
    if old['truth_in_sector']:
        budget.reserve(dict(truth_audits=1))
        point=lift(bundle['product_cuts'],case['truth']+old['known_shared_error'])
        retained=all(F(a)<=v<=F(b) for a,v,b in zip(future['lower'],point,future['upper'],strict=True))
        retained=retained and max(sum((F(a)*v for a,v in zip(row,point,strict=True) if a),F(0))-F(b)
            for row,b in zip(region['inequality_design'],region['inequality_upper'],strict=True))<=0
        contained=all(a<=v<=b for a,v,b in zip(future['envelope']['lower'],old['future_truth_m'],future['envelope']['upper'],strict=True))
    return dict(common,passed=retained and contained,excluded=False,known_truth_retained=retained,
        future_truth_evaluated_after_bounds=True,future_truth_m=old['future_truth_m'],
        future_lower_m=future['envelope']['lower'],future_upper_m=future['envelope']['upper'],
        known_shared_error=old['known_shared_error'],work=budget.counts,
        lp_proposals_reserved=budget.counts['proposals'],exact_supports_reserved=budget.counts['supports'],
        exact_supports_checked=checked['exact_supports_checked'],
        previous_width_m=[b-a for a,b in zip(old['future_lower_m'],old['future_upper_m'])],
        new_width_m=[b-a for a,b in zip(future['envelope']['lower'],future['envelope']['upper'])])
