# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged execution of frozen independent source component controls."""
def evaluate(task,context):
    import importlib.util
    import importlib.metadata
    import sys
    from lll.ilvis0_source_derivative_intervals import load_kernel,Kernel
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    if not __debug__:raise ValueError('known-answer assertions must be enabled')
    spec=task['payload']
    if importlib.metadata.version('pytest')!=spec['pytest']:raise ValueError('test package changed')
    sources=context.root/'source-freeze';directory=context.directory/'compiled';directory.mkdir(parents=True,exist_ok=True)
    kernel,metadata=load_kernel(directory,source_directory=sources/'analysis/lll')
    if metadata['compiler']!=spec['compiler']:raise ValueError('compiler changed')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(spec['auxiliary_limits'],persist)
    if spec['rational_references']:budget.reserve(dict(rational_references=spec['rational_references']))
    def initialize(*args):budget.reserve(dict(source_initializations=1));return kernel.initialize(*args)
    def append(*args):context.charge(bound_calls=1,bound_steps=4);return kernel.append(*args)
    def rotation(*args):context.charge(bound_calls=1,bound_steps=1);return kernel.rotation(*args)
    charged=Kernel(initialize,append,rotation,kernel.state_bytes)
    tests=sources/'analysis/tests';sys.path.insert(0,str(tests))
    path=tests/'test_ilvis0_source_derivative_intervals.py'
    module_spec=importlib.util.spec_from_file_location('_frozen_source_derivative_checks',path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    function=getattr(module,spec['function'])
    if 'angle' in spec:function(spec['angle'],charged)
    elif spec['function']=='test_mean_value_bound_accounts_for_arbitrary_supplied_rows_and_center':
        context.charge(bound_calls=1,bound_steps=0);function()
    else:function(charged)
    if budget.counts!=spec['auxiliary_limits']:raise ValueError('known-answer work differs from frozen reservations')
    context.save('compilation.json',metadata)
    return dict(passed=True,identity=task['identity'],function=spec['function'],work=budget.counts,
        state_bytes=kernel.state_bytes,parameter_count=27,reference_kind='independent rational and closed-form controls',
        original_reads=0,optimizer_starts=0,full_native_evaluations=0,
        training_transfer_qualified=False,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
