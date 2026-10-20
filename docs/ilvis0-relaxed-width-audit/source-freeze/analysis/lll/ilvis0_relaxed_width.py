# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only lower witnesses for a declared linear prediction relaxation."""


def evaluate(task,context):
    from fractions import Fraction as F
    import warnings
    import numpy as np
    from scipy.optimize import linprog,OptimizeWarning
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_feasible_witness import Region
    from lll.ilvis0_transform_audit import audit_case
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());old=bundle['result'];training=bundle['training'];future=bundle['future']
    if task['identity']!=old['identity'] or task['payload']['maximum_proposals']!=6 or not old['truth_in_sector']:
        raise ValueError('one saved known-truth sector and six proposals required')
    audit=audit_case(old,training,future)
    source=training['region'];lo=future['lower'];hi=future['upper']
    region=Region(lo,hi,source['inequality_design'],source['inequality_upper'])
    if len(lo)!=51:raise ValueError('all 51 coordinates required')
    common=dict(identity=task['identity'],model=old['task']['model'],profile=old['task']['profile'],
        sector=old['task']['sector'],passed=True,parameter_count=51,exact_baseline_supports=audit['exact_supports_checked'],
        original_reads=0,native_evaluations=0,optimizer_starts=0,
        physical_realizability_established=False,observational_coverage_qualified=False,scientific_decision='abstain')
    anchor=bundle['anchor'];anchor_slacks=region.slacks(anchor)
    context.save('anchor.json',dict(point=anchor,maximum_exact_slack=str(max(anchor_slacks))))
    if max(anchor_slacks)>0:
        return dict(common,supported=False,lp_proposals=0,axes=[],reason='saved anchor is not exactly feasible')
    proposals=[];axes=[];unsupported=0
    for axis in range(3):
        bound=future['bound'];scale=source['coordinate_scale'][axis]
        blocks=[future['jacobian'][axis],bound['previous_coefficients'][axis],
            bound['acceleration_coefficients'][axis],bound['transform_coefficients'][axis]]
        objective=[v*scale for block in blocks for v in block];values=[]
        if len(objective)!=51:raise ValueError('complete saved coefficient blocks required')
        for direction in (1,-1):
            _check_continue(context.root,context.manifest)
            ordinal=len(proposals)+1
            context.save(f'proposal-{ordinal:02d}.json',dict(ordinal=ordinal,maximum_seconds=1.,lp_proposals=1))
            c=np.array(objective)*direction
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore',message='Unrecognized options detected:.*threads',category=OptimizeWarning)
                answer=linprog(-c,A_ub=np.asarray(region.design,float),b_ub=np.asarray(region.bound,float),
                    bounds=list(zip(lo,hi)),method='highs-ds',options=dict(threads=1,time_limit=1.))
            record=dict(axis=axis,direction=direction,solver_status=int(answer.status),
                solver_message=str(answer.message)[:200],supported=False)
            if answer.success:
                try:witness=region.repair(answer.x,anchor)
                except ValueError as error:record['reason']=str(error)
                else:
                    point=witness['point']
                    # Independent direct arithmetic checks the exported witness.
                    slacks=[sum((F(a)*x for a,x in zip(row,point,strict=True)),F(0))-F(b)
                        for row,b in zip(source['inequality_design'],source['inequality_upper'])]
                    slacks += [x-F(b) for x,b in zip(point,hi)]+[F(a)-x for a,x in zip(lo,point)]
                    value=sum((F(float(v))*x for v,x in zip(c,point,strict=True)),F(0))
                    if max(slacks)>0 or value!=region.objective(c,point):raise ValueError('independent exact witness check failed')
                    record.update(supported=True,proposal=[float(v) for v in answer.x],
                        point=[str(v) for v in point],objective=str(value),mixing_fraction=str(witness['mixing_fraction']),
                        maximum_proposal_violation=str(witness['maximum_proposal_violation']),
                        maximum_final_slack=str(max(slacks)),constraint_checks=witness['constraint_checks']+len(slacks))
                    values.append(value)
            if not record['supported']:unsupported+=1
            proposals.append(record)
        if len(values)!=2:continue
        lower=values[0]+values[1]
        cert=future['envelope']['certificates'][axis]
        upper=F(cert['upper'])+F(cert['negated_lower'])
        if lower<0 or lower>upper:raise ValueError('exact witnesses contradict saved support range')
        unshared=2*F(bound['unshared_remainder'][axis])*F(scale)
        arithmetic=2*F(source['arithmetic_allowance'])
        total_lower=lower+unshared+arithmetic;total_upper=upper+unshared+arithmetic
        target=F(bundle['target_width_m'][axis])
        axes.append(dict(axis=axis,affine_lower_width=str(lower),affine_upper_width=str(upper),
            affine_gap=str(upper-lower),unshared_width=str(unshared),arithmetic_width=str(arithmetic),
            relaxed_lower_width=str(total_lower),relaxed_upper_width=str(total_upper),target_width=str(target),
            lower_exceeds_target=total_lower>target,
            affine_lower_over_upper=float(lower/upper) if upper else 1.))
    context.save('witnesses.json',dict(proposals=proposals,axes=axes))
    return dict(common,supported=len(axes)==3,lp_proposals=len(proposals),axes=axes,
        unsupported_proposals=unsupported,reason=None if len(axes)==3 else 'some LP proposals were unsupported')
