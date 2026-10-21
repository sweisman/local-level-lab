# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged execution of fixed direct-remainder mathematical controls."""
def evaluate(task,context):
    from fractions import Fraction as F
    import importlib.metadata
    import importlib.util
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    if not __debug__:raise ValueError('known-answer assertions must be enabled')
    spec=task['payload']
    if importlib.metadata.version('pytest')!=spec['pytest']:raise ValueError('test environment changed')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(spec['auxiliary_limits'],persist)
    budget.reserve({k:v for k,v in spec['auxiliary_limits'].items() if v})
    for ordinal in range(spec['bounds']):
        context.charge(bound_calls=1,bound_steps=spec['steps'] if ordinal==0 else 0)
    path=context.root/'source-freeze/analysis/tests/test_ilvis0_source_remainder.py'
    module_spec=importlib.util.spec_from_file_location('_frozen_source_remainder_checks',path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    arguments=spec.get('arguments',[])
    if spec.get('rational_arguments'):arguments=list(map(F,arguments))
    getattr(module,spec['function'])(*arguments)
    if budget.counts!=spec['auxiliary_limits']:raise ValueError('known-answer reservations changed')
    return dict(identity=task['identity'],passed=True,function=spec['function'],work=budget.counts,
        original_reads=0,optimizer_starts=0,native_evaluations=0,
        reference_bridge_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
