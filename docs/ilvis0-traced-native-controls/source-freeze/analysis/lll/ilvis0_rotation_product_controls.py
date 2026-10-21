# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check new product planes on sealed independent physical-control probes."""


def evaluate(task,context):
    from fractions import Fraction as F
    import numpy as np
    from lll.ilvis0_sharded_native import read
    from lll.ilvis0_shared_reference_terms import ReferenceErrors
    from lll.ilvis0_common_force_transform import ForceTransform
    from lll.ilvis0_rotation_products import build,lift,slacks
    from lll.ilvis0_control_shards import _check_continue
    bundle=read(context.input_path());source=bundle['result'];spec=task['payload']
    if (spec['maximum_probes']!=64 or spec['maximum_planes']!=129
            or not source['passed'] or len(source['probes'])!=64):
        raise ValueError('passing sealed 64-probe source and finite plane limits required')
    config=dict(bundle['case']['configuration']);config['limits']=np.array(config['limits'],float)
    center=np.full(27,.1);lower=-np.ones(27);upper=np.ones(27);family=spec['family']
    if family=='sector':lower[2]=0.;upper[2]=.25;center[2]=.125
    elif family=='fixed':lower=center.copy();upper=center.copy()
    elif family=='gain-boundary':config['limits'][18:21]=.9
    elif family!='full':raise ValueError('unknown source control family')
    reference=ReferenceErrors(config,lower,upper,center,source_id=source['identity'])
    transform=ForceTransform(reference)
    if source['cuts']['transform_binding']!=transform.binding:raise ValueError('sealed physical source/reference mismatch')
    context.save('reservation.json',dict(plane_constructions=129,physical_probes_reused=64,
        exact_inequalities=8256,coordinate_bounds_checked=4992,new_physical_oracles=0))
    cuts=build(transform.report(),initial_r=reference.initial_r.tolist(),limits=reference.limits.tolist(),
        physical_center=reference.center.tolist(),lower=lower.tolist()+[-1.]*24,upper=upper.tolist()+[1.]*24,
        reference_binding=reference.binding,source_id=reference.source_id,numerical_allowance=1e-8)
    if len(cuts['design'])!=129:raise ValueError('declared plane-construction allowance changed')
    worst=None;bound_worst=None;probes=[]
    for probe in source['probes']:
        _check_continue(context.root,context.manifest)
        point=probe['point']+probe['common_error'];extended=lift(cuts,point)
        slack=max(slacks(cuts,extended))
        bound_slack=max([F(a)-x for a,x in zip(cuts['lower'],extended)]+
            [x-F(b) for x,b in zip(extended,cuts['upper'])])
        worst=slack if worst is None else max(worst,slack)
        bound_worst=bound_slack if bound_worst is None else max(bound_worst,bound_slack)
        probes.append(dict(point=probe['point'],common_error=probe['common_error'],
            maximum_exact_slack=str(slack),maximum_exact_bound_slack=str(bound_slack)))
    context.save('cuts.json',cuts)
    return dict(identity=task['identity'],family=family,passed=worst<=0 and bound_worst<=0,
        source_identity=source['identity'],physical_probes_reused=64,exact_inequalities=8256,
        coordinate_bounds_checked=4992,maximum_exact_slack=str(worst),
        maximum_exact_bound_slack=str(bound_worst),probes=probes,parameter_count=78,
        original_parameter_count=51,physical_parameter_count=27,new_physical_parameters=0,
        new_physical_oracle_evaluations=0,native_evaluations=0,original_reads=0,optimizer_starts=0,
        physical_realizability_established=False,observational_coverage_qualified=False,scientific_decision='abstain')
