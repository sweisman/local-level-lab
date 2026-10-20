# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the qualified transport enclosure on the actual saved source domain."""


def compare_bounds(old,new,scale):
    import numpy as np
    metric=np.asarray(scale,float);before=np.asarray(old['unshared_remainder'],float);after=np.asarray(new['unshared_remainder'],float)
    if (metric.shape!=(3,) or before.shape!=(3,) or after.shape!=(3,)
            or not all(np.all(np.isfinite(v)) for v in (metric,before,after))
            or np.any(metric<=0) or np.any(before<0) or np.any(after<0)):
        raise ValueError('finite nonnegative three-axis error bounds and positive scale required')
    bindings=('source_id','reference_binding','shared_binding','acceleration_binding','transform_binding','time_s','conditioning')
    compatible=all(k in old and k in new and old[k]==new[k] for k in bindings)
    centers=np.array_equal(old['center'],new['center']);columns=True
    for key,width in (('previous_coefficients',6),('acceleration_coefficients',9),('transform_coefficients',9)):
        a=np.asarray(old[key],float);b=np.asarray(new[key],float)
        columns=columns and a.shape==(3,width) and b.shape==a.shape and np.array_equal(a,b)
    passed=bool(compatible and centers and columns)
    return dict(passed=passed,bindings_unchanged=compatible,center_unchanged=centers,columns_unchanged=bool(columns),
        baseline_remainder_m=(before*metric).tolist(),fresh_remainder_m=(after*metric).tolist(),
        retained_remainder_m=(np.minimum(before,after)*metric).tolist() if passed else None,
        improved_axes=[bool(a<b) for a,b in zip(after,before,strict=True)],
        fresh_to_baseline_ratio=[float(a/b) if b else None for a,b in zip(after,before,strict=True)])


def evaluate(task,context):
    import numpy as np
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_orientation_cover import sector
    from lll import ilvis0_cached_native as candidate
    bundle=read(context.input_path());case=read(context.input_path(task['payload']['case_key']))
    parent=read(context.input_path(task['payload']['conditioning_key']));future=bundle['future'];old=future['bound'];spec=task['payload']
    n=len(case['dt']);limits=dict(setups=1,exact_supports=6)
    if n!=1600 or spec['limits']!=limits or not bundle['result']['passed']:raise ValueError('six fixed qualified sources required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1))
    conditioning=ConditionedAcceleration(parent['projection_input'],parent['projection'],
        reserve=lambda count:budget.reserve(dict(exact_supports=count)))
    if conditioning.binding!=old['conditioning']['input_binding']:raise ValueError('saved conditioning identity changed')
    box=sector(4);reference=candidate.make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    if reference.report()!=future['reference']:raise ValueError('saved native source reference changed')
    left=old['lower'];right=old['upper']
    conditioning.match(reference.report(),left,right)
    context.save('conditioning.json',conditioning.report())
    context.charge(bound_calls=1,bound_steps=2*n)
    report=candidate.enclose(case['configuration'],case['theta'],case['dv'],case['dt'],time=future['time_s'],
        lower=left,upper=right,reference=reference,conditioning=conditioning,maximum_seconds=spec['maximum_bound_seconds'])
    current=report.report();context.save('bound.json',plain(current))
    scale=parent['projection_input']['training']['region']['coordinate_scale']
    result=compare_bounds(old,current,scale)
    return dict(result,identity=task['identity'],model=bundle['result']['model'],profile=bundle['result']['profile'],
        work=budget.counts,parameter_count=51,native_evaluations=0,bound_evaluations=1,
        reserved_bound_steps=2*n,source_norm_interval_installed=False,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
