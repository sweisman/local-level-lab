# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite performance screen on the actual complete-comparison child domains."""
from copy import deepcopy


def evaluate(task,context):
    import time
    from lll.ilvis0_sharded_native import read,plain
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_conditioned_acceleration import ConditionedAcceleration
    from lll.ilvis0_conditioned_subdomain import SubdomainAcceleration
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_direct_interface import bridge
    from lll.ilvis0_direct_interface import matched_bounds
    from lll import ilvis0_direct_native as native
    spec=task['payload'];bundle=read(context.input_path());saved=bundle['future'];old=bundle['result']
    case=read(context.input_path(spec['case_key']));condition=read(context.input_path(spec['condition_key']))
    n=len(case['dt']);limits=dict(setups=1,proofs=1,parent_supports=6,source_setups=1,
        source_steps=n,source_body_bounds=n,source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n)
    if (n!=1600 or limits!=spec['limits'] or old['task']['sector']!=0 or not old['passed']
            or (case['configuration']['model'],case['configuration']['profile'])!=(old['task']['model'],old['task']['profile'])):
        raise ValueError('six complete original sector-zero child sources required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1,proofs=1))
    box=sector(0);reference=native.make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    restricted=deepcopy(bundle['training']);restricted['region'].update(lower=saved['lower'],upper=saved['upper'])
    if reference.report()!=saved['reference'] or restricted!=condition['child_training']:
        raise ValueError('source/reference/training domain changed')
    parent=ConditionedAcceleration(condition['parent_input'],condition['parent_certificate'],
        reserve=lambda count:budget.reserve(dict(parent_supports=count)))
    proof=SubdomainAcceleration(parent,condition['parent_input'],restricted,saved['lower'][:27],saved['upper'][:27])
    proof.match_training(restricted);context.save('restricted-proof.json',proof.report())
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    source,source_meta=load_stream(directory,source_directory=sources)
    derivative,derivative_meta=load_kernel(directory,source_directory=sources)
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    point,point_meta=load_point(directory,source_directory=sources)
    compilation=dict(arithmetic=arithmetic,source=source_meta,derivative=derivative_meta,point=point_meta)
    if any(v['compiler']!=spec['compiler'] for v in compilation.values()):raise ValueError('compiler changed')
    context.save('compilation.json',compilation)
    budget.reserve(dict(source_setups=1,source_steps=n,source_body_bounds=n,source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n))
    context.charge(bound_calls=1,bound_steps=9*n);started=time.monotonic()
    raw=native.enclose(case['configuration'],case['theta'],case['dv'],case['dt'],time=saved['time_s'],
        lower=saved['lower'][:27],upper=saved['upper'][:27],reference=reference,conditioning=proof,
        source_kernel=source,derivative_kernel=derivative,point_kernel=point,maximum_seconds=spec['maximum_bound_seconds'])
    elapsed=time.monotonic()-started;report=bridge(raw,reference,proof,saved['nominal'],restricted['region']['coordinate_scale']).report()
    context.save('bound.json',plain(report));matched=None
    if spec['baseline_key'] is not None:
        matched=matched_bounds(read(context.input_path(spec['baseline_key'])),report)
        context.save('predecessor-match.json',matched)
    if any(report[k]>n for k in ('source_reference_steps','rounded_source_prefixes','source_derivative_steps','source_direct_steps')):
        raise ValueError('source work exceeds its allowance')
    return dict(identity=task['identity'],passed=matched is None or matched['passed'],
        model=old['task']['model'],profile=old['task']['profile'],bound_elapsed_s=elapsed,
        predecessor_available=matched is not None,matched=matched,work=budget.counts,
        source_steps=report['source_reference_steps'],source_body_bounds=report['rounded_source_prefixes'],
        derivative_steps=report['source_derivative_steps'],point_steps=report['source_direct_steps'],bound_evaluations=1,native_evaluations=0,
        original_reads=0,optimizer_starts=0,observational_coverage_qualified=False,scientific_decision='abstain')
