# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare unchanged and midpoint-only bounds on identical complete domains."""
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
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    from lll.ilvis0_direct_interface import bridge
    from lll import ilvis0_direct_native as previous,ilvis0_midpoint_native as candidate
    spec=task['payload'];bundle=read(context.input_path());saved=bundle['future'];old=bundle['result']
    case=read(context.input_path(spec['case_key']));condition=read(context.input_path(spec['condition_key']))
    n=len(case['dt']);per_bound=dict(source_setups=1,source_steps=n,source_body_bounds=n,
        source_derivative_setups=1,source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n)
    limits=dict(setups=1,proofs=1,parent_supports=6,**{k:2*v for k,v in per_bound.items()})
    expected_order=['predecessor','candidate'] if (spec['model']+int(spec['profile']))%2==0 else ['candidate','predecessor']
    if (n!=1600 or limits!=spec['limits'] or old['task']['sector']!=0 or not old['passed'] or old['excluded']
            or expected_order!=spec['order'] or saved['time_s']!=7.2
            or (case['configuration']['model'],case['configuration']['profile'])!=(spec['model'],spec['profile'])):
        raise ValueError('six unchanged complete sector-zero child domains and balanced order required')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(limits,persist);budget.reserve(dict(setups=1,proofs=1))
    box=sector(0);reference=previous.make_reference(case['configuration'],case['theta'],case['dv'],case['dt'],
        **{k:box[k] for k in ('lower','upper','center')})
    restricted=deepcopy(bundle['training']);restricted['region'].update(lower=saved['lower'],upper=saved['upper'])
    if reference.report()!=saved['reference'] or restricted!=condition['child_training']:
        raise ValueError('source/reference/child domain changed')
    parent=ConditionedAcceleration(condition['parent_input'],condition['parent_certificate'],
        reserve=lambda count:budget.reserve(dict(parent_supports=count)))
    proof=SubdomainAcceleration(parent,condition['parent_input'],restricted,saved['lower'][:27],saved['upper'][:27])
    proof.match_training(restricted);context.save('restricted-proof.json',proof.report())
    directory=context.root/'shards'/f'{context.shard:03d}'/'kernels';directory.mkdir(parents=True,exist_ok=True)
    sources=context.root/'source-freeze/analysis/lll'
    arithmetic=configure_backend(directory,source_directory=sources)
    source,source_meta=load_stream(directory,source_directory=sources)
    derivative,derivative_meta=load_kernel(directory,source_directory=sources)
    point,point_meta=load_point(directory,source_directory=sources)
    compilation=dict(arithmetic=arithmetic,source=source_meta,derivative=derivative_meta,point=point_meta)
    if any(v['compiler']!=spec['compiler'] for v in compilation.values()):raise ValueError('compiler changed')
    context.save('compilation.json',compilation);reports={};durations={};converted={}
    for label in spec['order']:
        budget.reserve(per_bound);context.charge(bound_calls=1,bound_steps=9*n)
        module=previous if label=='predecessor' else candidate
        started=time.monotonic()
        try:
            raw=module.enclose(case['configuration'],case['theta'],case['dv'],case['dt'],time=7.2,
                lower=saved['lower'][:27],upper=saved['upper'][:27],reference=reference,conditioning=proof,
                source_kernel=source,derivative_kernel=derivative,point_kernel=point,
                maximum_seconds=spec['maximum_bound_seconds'])
        except Exception as caught:
            context.save('timing-'+label+'.json',dict(completed=False,elapsed_s=time.monotonic()-started,
                error_type=type(caught).__name__,reason=str(caught)))
            raise
        durations[label]=time.monotonic()-started
        reports[label]=plain(raw.report())
        converted[label]=bridge(raw,reference,proof,saved['nominal'],restricted['region']['coordinate_scale']).report()
        context.save('raw-'+label+'.json',reports[label]);context.save('bound-'+label+'.json',converted[label])
        context.save('timing-'+label+'.json',dict(completed=True,elapsed_s=durations[label]))
        if any(reports[label][k]>n for k in ('source_reference_steps','rounded_source_prefixes',
                'source_derivative_steps','source_direct_steps')):raise ValueError('unreserved source work')
    exact=reports['candidate']==reports['predecessor'] and converted['candidate']==converted['predecessor']
    return dict(identity=task['identity'],passed=exact,exact_report_match=exact,model=spec['model'],profile=spec['profile'],
        order=spec['order'],predecessor_s=durations['predecessor'],candidate_s=durations['candidate'],
        candidate_ratio=durations['candidate']/durations['predecessor'],work=budget.counts,
        bound_evaluations=2,native_evaluations=0,original_reads=0,optimizer_starts=0,
        observational_coverage_qualified=False,scientific_decision='abstain')
