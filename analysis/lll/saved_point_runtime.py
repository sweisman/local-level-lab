# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shared finite reconstruction, capture and accounting for saved-point probes."""
import math
from pathlib import Path


def allowance(r,maximum_evaluations):
    if type(maximum_evaluations) is not int or not 1<=maximum_evaluations<=200:
        raise ValueError('finite saved-point evaluation cap in [1,200] required')
    cut=2*r['queries']//3;last=r['query_start_s']+(cut-1)*r['query_step_s']
    prefix=math.ceil((last+r['limits']['time_offset'])*r['rate_hz'])+2
    reconstruction=prefix+cut
    return dict(native_calls=reconstruction+maximum_evaluations,
        packet_visits=reconstruction+maximum_evaluations*prefix*cut,bound_calls=0,bound_steps=0)


def bind_capture(provider,*,raw,expected_sha256,provider_sha256):
    from lll.studies.protocols import bind_function
    from lll import stopping_consistency_study as old
    return bind_function(raw,expected_sha256=expected_sha256,function='calculate_point',
        import_module='lll.stopping_consistency',import_name='probe',provider=provider,
        provider_source_sha256=provider_sha256,namespace=dict(math=math,Path=Path,
            Captured=old.Captured,verify_replay=old.verify_replay,no_nonlinear_fit=old.no_nonlinear_fit,
            __file__=old.__file__))


def run_point(task,context,record,r,*,maximum_evaluations,provider,provider_source,physical_conversion=False):
    from lll.coordinate_optimizer_study import kernels
    from lll.structured_noisy_training import limits
    from lll.studies.artifacts import digest
    from lll.studies.journal import Journal
    from lll.ilvis0_control_shards import _check_continue
    from lll.ilvis0_solver_position import physical_residual_step
    import json
    if (task['identity']!=record['identity'] or task['limits']!=allowance(r,maximum_evaluations)
            or not callable(provider) or provider_source not in context.manifest['sources']
            or type(physical_conversion) is not bool):raise ValueError('exact saved-point work and provider required')
    env=json.loads(context.input_path('environment').read_bytes())
    identity=task['identity'];freeze=digest((context.root/'manifest.json').read_bytes())
    law=record['payload']['case']['law']
    cj=Journal(context.directory/'construction.sqlite',freeze=freeze,limits={identity:limits(r,law)[1]});cj.start(identity)
    ej=Journal(context.directory/'evaluations.sqlite',freeze=freeze,
        limits={identity:dict(evaluations=maximum_evaluations)});ej.start(identity)
    check=lambda:_check_continue(context.root,context.manifest)
    def construction(**work):
        check()
        for key,value in work.items():cj.reserve(identity,key,value)
    def evaluation(**work):
        check()
        if work!={'evaluations':1}:raise ValueError('one complete residual/Jacobian charge required')
        ej.reserve(identity,'evaluations')
    name='analysis/lll/stopping_consistency_study.py';raw=(context.root/'source-freeze'/name).read_bytes()
    bound,proof=bind_capture(provider,raw=raw,expected_sha256=context.manifest['sources'][name],
        provider_sha256=context.manifest['sources'][provider_source]);context.save('capture-binding.json',proof)
    options=(lambda problem:dict(physical_step=lambda delta:physical_residual_step(problem,delta))) if physical_conversion else None
    budget=None
    try:
        noise,factory=kernels(context,env)
        with context.prepay_native(native_calls=task['limits']['native_calls'],packet_visits=task['limits']['packet_visits']) as budget:
            name='analysis/lll/airquantumgrav_prediction.py'
            result=bound(record,r,kernel_factory=factory,noise_kernel=noise,reserve=budget.reserve,
                reserve_construction=construction,reserve_evaluation=evaluation,save=context.save,check_continue=check,
                protocol_source=(context.root/'source-freeze'/name).read_bytes(),protocol_sha256=context.manifest['sources'][name],
                probe_options=options)
        cj.verify();ej.verify()
        if ej.count(identity,'evaluations')!=result['evaluations']:raise ValueError('diagnostic charges differ')
        return dict(result,stopping_check_executed=False)
    finally:
        if budget is not None:context.save('native-prepayment.json',budget.snapshot())
        context.note_file(cj.path);context.note_file(ej.path)
