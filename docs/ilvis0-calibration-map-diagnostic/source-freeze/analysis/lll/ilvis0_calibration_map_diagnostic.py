# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-generated calibration-map diagnosis; never an inference adapter.

Exact feasible points in an outer linear region need not be realizable by one
physical calibration. Oracle evaluation here is explicitly diagnostic, uses
generated cases only, and supplies neither predictive coverage nor an optimum.
"""
from fractions import Fraction as F
import math
from lll.ilvis0_feasible_witness import Region


class Allowance:
    def __init__(self,limits,persist):
        if set(limits)!={'lp','maps','checks'} or any(type(v)!=int or v<0 for v in limits.values()):
            raise ValueError('finite named work allowance required')
        self.limits=dict(limits);self.counts=dict.fromkeys(limits,0);self.persist=persist

    def reserve(self,kind,amount):
        if kind not in self.counts or type(amount)!=int or amount<1:
            raise ValueError('positive named work reservation required')
        next_counts=self.counts|{kind:self.counts[kind]+amount}
        if next_counts[kind]>self.limits[kind]:raise ValueError('diagnostic work allowance exhausted')
        self.persist(dict(kind=kind,amount=amount,counts=next_counts.copy()))
        self.counts=next_counts


def reconcile(events,expected,limits):
    """Metadata-only audit of durable reservations, not an execution observer."""
    counts=dict.fromkeys(limits,0)
    for event in events:
        kind=event['kind'];amount=event['amount']
        if kind not in counts or type(amount)!=int or amount<1:raise ValueError('invalid work reservation')
        counts[kind]+=amount
        if counts[kind]>limits[kind] or counts!=event['counts']:
            raise ValueError('reservation allowance or cumulative sequence changed')
    if counts!=expected:raise ValueError('saved work and reservations disagree')
    return counts


class CountedRegion(Region):
    def __init__(self,lower,upper,design,bound,budget):
        super().__init__(lower,upper,design,bound)
        object.__setattr__(self,'budget',budget)

    def slacks(self,point):
        self.budget.reserve('checks',len(self.design)+2*len(self.lower))
        return super().slacks(point)


def independent_slacks(region,point,budget):
    """Separate direct exact check, including all lifted-coordinate bounds."""
    n=len(region.lower)
    if len(point)!=n:raise ValueError('all coordinates required')
    budget.reserve('checks',len(region.design)+2*n)
    x=tuple(F(v) for v in point)
    values=[sum((F(a)*v for a,v in zip(row,x,strict=True)),F(0))-F(b)
        for row,b in zip(region.design,region.bound,strict=True)]
    values += [v-F(b) for v,b in zip(x,region.upper,strict=True)]
    values += [F(a)-v for a,v in zip(region.lower,x,strict=True)]
    return tuple(values)


def require_reference(reference,saved):
    if reference.report()!=saved:raise ValueError('complete source-bound calibration map changed')


def physical_map(reference,point,budget,save):
    """Save exact/rounded physical coordinates before any source-map evaluation."""
    if len(point)!=78:raise ValueError('complete lifted witness required')
    original=tuple(F(v) for v in point[:27]);rounded=tuple(float(v) for v in original)
    if not all(math.isfinite(v) for v in rounded):raise ValueError('finite physical conversion required')
    conversion=dict(original_coordinates=list(map(str,original)),physical=list(rounded),
        rounding_difference=[str(F(v)-a) for a,v in zip(original,rounded)],supported=False)
    save('physical-conversion.json',conversion)
    budget.reserve('checks',108)
    lower=tuple(map(lambda v:F(float(v)),reference.parent.lower))
    upper=tuple(map(lambda v:F(float(v)),reference.parent.upper))
    if len(lower)!=27 or len(upper)!=27:raise ValueError('complete source physical domain required')
    if (not all(a<=v<=b for a,v,b in zip(lower,original,upper,strict=True))
            or not all(a<=F(v)<=b for a,v,b in zip(lower,rounded,upper,strict=True))):
        return conversion|dict(reason='exact or rounded physical coordinates outside source domain')
    budget.reserve('maps',1)
    errors=[float(v) for v in reference.normalized_values_at(rounded)]
    if len(errors)!=24 or not all(math.isfinite(v) for v in errors):
        raise ValueError('all 24 finite source-map error components required')
    result=conversion|dict(supported=True,errors=errors)
    save('physical-map.json',result)
    return result


def lift_without_domain_repair(cuts,point):
    """Evaluate the products even outside the outer box; do not clip violations."""
    from lll.ilvis0_rotation_products import PAIRS
    if len(point)!=51 or len(cuts['matrix_affine'])!=9 or len(cuts['gain_limits'])!=3:
        raise ValueError('complete original error map and matrix expression required')
    x=tuple(map(F,point));m=[]
    for row in cuts['matrix_affine']:
        if len(row['coefficients'])!=51:raise ValueError('complete matrix expression required')
        m.append(F(row['constant'])+sum((F(a)*v for a,v in zip(row['coefficients'],x,strict=True)),F(0)))
    gains=[F(a)*x[18+j] for j,a in enumerate(cuts['gain_limits'])]
    products=[m[3*i+j]*gains[j] for i in range(3) for j in range(3)]
    b=[a+v for a,v in zip(m,products)]
    return x+tuple(products)+tuple(b[3*i+j]*b[3*i+k] for i in range(3) for j,k in PAIRS)


def objectives(source,future):
    rows=[];b=future['bound']
    if len(source['coordinate_scale'])!=3:raise ValueError('three coordinate scales required')
    for axis,scale in enumerate(source['coordinate_scale']):
        blocks=[future['jacobian'][axis],b['previous_coefficients'][axis],
            b['acceleration_coefficients'][axis],b['transform_coefficients'][axis]]
        if list(map(len,blocks))!=[27,6,9,9]:raise ValueError('all original four coefficient blocks required')
        rows.append([F(v*scale) for block in blocks for v in block]+[F(0)]*27)
    return rows


def changes(source,future,before,after):
    if len(before)!=78 or len(after)!=78:raise ValueError('all lifted coordinates required')
    difference=[F(b)-F(a) for a,b in zip(before,after,strict=True)];rows=[]
    for axis,row in enumerate(objectives(source,future)):
        blocks={name:sum((a*v for a,v in zip(row[left:right],difference[left:right])),F(0))
            for name,left,right in (('physical',0,27),('velocity_clock',27,30),('lever',30,33),
                ('acceleration',33,42),('force_matrix',42,51))}
        rows.append(dict(axis=axis,blocks={k:str(v) for k,v in blocks.items()},
            total=str(sum(blocks.values(),F(0))),absolute_block_sum=str(sum(map(abs,blocks.values()),F(0)))))
    return rows


def propose(region,objective,budget):
    import numpy as np
    import warnings
    from scipy.optimize import linprog,OptimizeWarning
    if len(objective)!=len(region.lower):raise ValueError('all objective coordinates required')
    budget.reserve('lp',1)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore',message='Unrecognized options detected:.*threads',category=OptimizeWarning)
        answer=linprog(-np.asarray(objective,float),
            A_ub=np.asarray(region.design,float) if region.design else None,
            b_ub=np.asarray(region.bound,float) if region.bound else None,
            bounds=[(float(a),float(b)) for a,b in zip(region.lower,region.upper)],
            method='highs-ds',options=dict(threads=1,time_limit=1.))
    return dict(success=bool(answer.success),status=int(answer.status),message=str(answer.message)[:200],
        point=answer.x.tolist() if answer.success else None)


def evaluate(task,context):
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_transform_native import make_reference
    from lll.ilvis0_rotation_products import lift
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());old=bundle['result'];training=bundle['training'];future=bundle['future'];cuts=bundle['cuts']
    spec=task['payload'];case=read(context.input_path(spec['case_key']))
    limits=dict(lp=6,maps=7,checks=41000)
    if (task['identity']!=old['identity'] or not old['truth_in_sector'] or not old['passed']
            or old['excluded'] or spec['work_limits']!=limits or old['parameter_count']!=78
            or cuts['source_id']!=training['region']['source_id']
            or cuts['binding']!=training['region']['rotation_product_binding']):
        raise ValueError('source-bound known-generated sector and finite complete allowance required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);box=sector(old['task']['sector'])
    reference=make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        lower=box['lower'],upper=box['upper'],center=box['center'])
    require_reference(reference,future['reference'])
    source=training['region'];region=CountedRegion(future['lower'],future['upper'],
        source['inequality_design'],source['inequality_upper'],budget)
    anchor=lift(cuts,case['truth']+old['known_shared_error'])
    anchor_slacks=region.slacks(anchor)
    if max(anchor_slacks)>0:raise ValueError('sealed known anchor not exactly feasible')
    def save_with(prefix):return lambda name,value:context.save(prefix+'-'+name,value)
    control=physical_map(reference,anchor,budget,save_with('anchor'))
    if not control['supported']:raise ValueError('known control outside its physical reference')
    budget.reserve('checks',24)
    mismatch=max(abs(a-b) for a,b in zip(control['errors'],old['known_shared_error'],strict=True))
    if mismatch>3e-10:raise ValueError('known source-map scale/component agreement failed')
    context.save('anchor-control.json',dict(point=list(map(str,anchor)),maximum_exact_slack=str(max(anchor_slacks)),
        maximum_error_component_difference=mismatch,tolerance=3e-10))
    proposals=[]
    for axis,row in enumerate(objectives(source,future)):
        for sign in (1,-1):
            ordinal=len(proposals)+1;prefix=f'witness-{ordinal:02d}';objective=[sign*v for v in row]
            proposal=propose(region,objective,budget);context.save(prefix+'-proposal.json',proposal)
            record=dict(axis=axis,sign=sign,lp_success=proposal['success'],supported=False,
                physical_map_supported=False,reason=proposal['message'])
            if proposal['success']:
                witness=region.repair(proposal['point'],anchor)
                slacks=independent_slacks(region,witness['point'],budget)
                if max(slacks)>0:raise ArithmeticError('independent exact witness check failed')
                context.save(prefix+'-exact.json',dict(point=list(map(str,witness['point'])),
                    mixing_fraction=str(witness['mixing_fraction']),maximum_exact_slack=str(max(slacks))))
                mapped=physical_map(reference,witness['point'],budget,save_with(prefix))
                record.update(supported=True,mixing_fraction=str(witness['mixing_fraction']),
                    boundary_collapse=witness['mixing_fraction']==1,
                    objective=str(region.objective(objective,witness['point'])),
                    physical_map_supported=mapped['supported'],reason=mapped.get('reason'))
                if mapped['supported']:
                    point=lift_without_domain_repair(cuts,mapped['physical']+mapped['errors'])
                    mapped_slacks=independent_slacks(region,point,budget)
                    record.update(mapped_training_feasible=max(mapped_slacks)<=0,
                        maximum_mapped_slack=str(max(mapped_slacks)),mapped_violated_constraints=sum(v>0 for v in mapped_slacks),
                        changes=changes(source,future,witness['point'],point),
                        mapped_objective=str(region.objective(objective,point)))
                    context.save(prefix+'-mapped.json',dict(point=list(map(str,point)),**record))
            proposals.append(record)
    context.save('witness-summary.json',dict(proposals=proposals,work=budget.counts))
    return dict(identity=task['identity'],model=old['task']['model'],profile=old['task']['profile'],
        sector=old['task']['sector'],passed=True,anchor_control_difference=mismatch,
        supported_witnesses=sum(p['supported'] for p in proposals),
        mapped_witnesses=sum(p['physical_map_supported'] for p in proposals),
        mapped_training_feasible=sum(p.get('mapped_training_feasible',False) for p in proposals),
        boundary_collapses=sum(p.get('boundary_collapse',False) for p in proposals),
        proposals=proposals,work=budget.counts,parameter_count=78,physical_parameter_count=27,
        original_reads=0,native_evaluations=0,bound_evaluations=0,optimizer_starts=0,
        physical_global_optimum_established=False,observational_coverage_qualified=False,scientific_decision='abstain')
