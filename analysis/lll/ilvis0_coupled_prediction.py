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


def extend_static_region(training_region,cuts,map_report,*,lower,upper):
    """Attach checked static-map cuts before product lifting, keeping all rows.

    The map's source-level interval qualification remains a separate premise;
    this adapter independently checks its exported algebra and identity. It
    neither fits measurements nor declares an empty or qualified physical region.
    """
    old=training_region
    if (old.get('parameter_count')!=51 or old.get('physical_parameter_count')!=27
            or old.get('future_truth_used') is not False
            or any(len(old.get(k,[]))!=51 for k in ('lower','upper','center'))
            or len(lower)!=27 or len(upper)!=27
            or old.get('binding')!=cuts.get('reference_binding')
            or old.get('source_id')!=cuts.get('source_id')):
        raise ValueError('complete training-only 51-column source-bound region required')
    design=old.get('inequality_design',[]);bounds=old.get('inequality_upper',[])
    values=list(lower)+list(upper)+old['lower']+old['upper']+old['center']+bounds
    values += [v for row in design for v in row]
    if (len(design)!=len(bounds) or any(len(row)!=51 for row in design)
            or len(design)+48>1024 or any(not math.isfinite(v) for v in values)
            or any(a>b for a,b in zip(old['lower'],old['upper'],strict=True))
            or any(not a<=c<=d<=b for a,b,c,d in zip(old['lower'][:27],old['upper'][:27],lower,upper,strict=True))):
        raise ValueError('finite contained physical domain and every original inequality required')
    audit=audit_cuts(cuts,map_report,list(lower),list(upper))
    region=deepcopy(old)
    region['lower'][:27]=list(lower);region['upper'][:27]=list(upper)
    region['inequality_design'].extend(deepcopy(cuts['design']))
    region['inequality_upper'].extend(cuts['upper'])
    region['coupled_map_binding']=cuts['binding'];region['coupling_rows_checked']=audit['rows']
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
    if task.get('payload',{}).get('analysis')=='static_training':
        return evaluate_static_training(task,context)
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


def static_training_limits():
    return dict(reference_setups=1,map_setups=1,intervals=2,coupling_audits=1,
        static_oracles=3,static_jacobians=3,probe_checks=4176,lp_proposals=60,exact_supports=180)


def summarize_static_training(results):
    """Aggregate a fixed complete cover without treating failures as exclusions."""
    if len(results)!=54:raise ValueError('all fifty-four frozen outcomes required')
    groups={}
    for row in results:groups.setdefault(row['case_identity'],[]).append(row)
    if len(groups)!=6:raise ValueError('six original case identities required')
    cases=[];candidates=set()
    for identity,rows in sorted(groups.items()):
        if len(rows)!=9 or {r['part'] for r in rows}!=set(range(-1,8)):
            raise ValueError('full-domain comparator and all eight distinct yaw parts required')
        baseline={(r['model'],r['profile'],r['prior_acceleration_change']) for r in rows}
        if len(baseline)!=1:raise ValueError('unchanged candidate and prior allowance required')
        model,profile,prior=baseline.pop();candidates.add((model,profile))
        if not math.isfinite(prior) or prior<0:raise ValueError('finite nonnegative prior required')
        for row in rows:
            if row['passed'] and (not math.isfinite(row['acceleration_change']) or row['acceleration_change']<0):
                raise ValueError('finite nonnegative successful acceleration bound required')
        full=next(r for r in rows if r['part']==-1);parts=[r for r in rows if r['part']>=0]
        complete=all(r['passed'] for r in parts)
        worst=max(r['acceleration_change'] for r in parts) if complete else None
        cases.append(dict(case_identity=identity,model=model,profile=profile,
            prior_acceleration_change=prior,full_acceleration_change=full['acceleration_change'] if full['passed'] else None,
            complete_cover=complete,cover_acceleration_change=worst,
            cover_improves_prior=complete and worst<prior,failed_parts=[r['part'] for r in rows if not r['passed']]))
    if candidates!={(m,p) for m in range(3) for p in (False,True)}:
        raise ValueError('all three candidates and both processing cases required')
    return dict(completed=54,passed=sum(bool(r['passed']) for r in results),cases=cases,
        complete_covers=sum(r['complete_cover'] for r in cases),prediction_method_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')


def analyze_static_training(material,*,part,reserve,save):
    """Saved-training diagnostic, using a complete source map and fixed yaw cover."""
    import numpy as np
    from types import SimpleNamespace
    from lll.ilvis0_coupled_map import StaticMap,restore_static_reference
    from lll.ilvis0_coupled_map_controls import analytic_jacobian,check_probe
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_affine_support import project_coordinates
    from lll.ilvis0_acceleration_projection import project
    if type(part) is not int or not -1<=part<8:raise ValueError('full domain or one of eight fixed yaw parts required')
    old=material['training_region'];prior=material['prior_acceleration_change']
    if not math.isfinite(prior) or prior<0:raise ValueError('finite nonnegative saved acceleration allowance required')
    lower=list(old['lower'][:27]);upper=list(old['upper'][:27])
    if part>=0:
        box=sector(part)
        lower=[max(a,float(b)) for a,b in zip(lower,box['lower'],strict=True)]
        upper=[min(a,float(b)) for a,b in zip(upper,box['upper'],strict=True)]
    if any(a>b for a,b in zip(lower,upper,strict=True)):
        raise ValueError('unsupported empty cover part; no part may be silently discarded')
    reserve(reference_setups=1)
    reference=restore_static_reference(material['configuration'],material['first_delta_v'],material['first_dt'],
        lower=material['lower'],upper=material['upper'],center=material['center'],
        expected_report=material['reference_report'])
    reserve(map_setups=1)
    model=StaticMap(reference,expected_report=material['reference_report'],numerical_allowance=3e-10)
    intervals=[]
    def bounded(a,b):
        value=model.bound(a,b);intervals.append(value);return value
    cuts=build(SimpleNamespace(bound=bounded,report=model.report),lower,upper,
        reserve=lambda:reserve(intervals=1))
    save('coupling.json',cuts);save('source-map.json',model.report())
    reserve(coupling_audits=1)
    region=extend_static_region(old,cuts,model.report(),lower=lower,upper=upper)
    points=[lower,upper,[float((F(a)+F(b))/2) for a,b in zip(lower,upper,strict=True)]]
    probes=[]
    for point in points:
        reserve(static_oracles=1,static_jacobians=1,probe_checks=1392)
        actual=reference.normalized_values_at(point);jac=analytic_jacobian(reference,point)
        checked=check_probe(intervals[0],cuts,point,actual,jac,derivative_tolerance=3e-8)
        probes.append(dict(point=point,values=actual.tolist(),analytic_jacobian=jac.tolist(),**checked))
    save('source-probes.json',probes)
    if not all(p['passed'] for p in probes):raise ValueError('static source probe failed; dependent projections withheld')
    reserve_projection=lambda p,s:reserve(lp_proposals=p,exact_supports=s)
    coordinates=project_coordinates(region['lower'],region['upper'],region['inequality_design'],
        region['inequality_upper'],axes=list(range(27)),reserve=reserve_projection)
    save('coordinate-projection.json',coordinates)
    acceleration=project(training=dict(region=region),reference=material['reference_report'],
        lower=region['lower'],upper=region['upper'],reserve=reserve_projection)
    save('acceleration-projection.json',acceleration)
    unchanged=(region['inequality_design'][:len(old['inequality_design'])]==old['inequality_design']
        and region['inequality_upper'][:len(old['inequality_upper'])]==old['inequality_upper'])
    return dict(passed=unchanged,scientific_decision='abstain',case_identity=material['identity'],part=part,
        model=material['configuration']['model'],profile=material['configuration']['profile'],
        parameter_count=51,physical_parameter_count=27,original_rows_retained=len(old['inequality_design']),
        coupling_rows_checked=48,source_map_binding=model.binding,reference_binding=reference.binding,
        acceleration_change=acceleration['norm_change'],prior_acceleration_change=prior,
        narrowed_coordinates=[r['parameter_index'] for r in coordinates['coordinates'] if r['width_ratio']<.999999],
        source_probes_passed=True,native_evaluations=0,bound_evaluations=0,original_reads=0,optimizer_starts=0,
        source_map_qualified=False,observational_coverage_qualified=False)


def evaluate_static_training(task,context):
    from lll.studies.journal import Journal
    from lll.studies.artifacts import digest
    from lll.ilvis0_control_shards import _check_continue
    spec=task['payload'];material=json.loads(context.input_path().read_text())
    if (spec.get('limits')!=static_training_limits() or spec.get('case_identity')!=material['identity']
            or len(material['training_region']['inequality_design'])!=30):
        raise ValueError('unchanged long-history identity, thirty training rows and finite limits required')
    identity=task['identity'];path=context.directory/'allowance.sqlite'
    journal=Journal(path,freeze=digest((context.root/'manifest.json').read_bytes()),
        limits={identity:static_training_limits()})
    journal.start(identity)
    def reserve(**increase):
        _check_continue(context.root,context.manifest)
        for resource,amount in increase.items():journal.reserve(identity,resource,amount)
    try:
        result=analyze_static_training(material,part=spec['part'],reserve=reserve,save=context.save)
        counts={k:journal.count(identity,k) for k in static_training_limits()}
        if result['passed'] and counts!=static_training_limits():raise ValueError('incomplete static diagnostic accounting')
        context.save('accounting.json',counts)
        return dict(result,identity=identity,work=counts)
    finally:
        journal.verify();context.note_file(path)
