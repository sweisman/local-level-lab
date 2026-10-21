# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charged independent direct-source and numerical-reference bridge checks."""
def evaluate(task,context):
    import importlib.metadata
    import importlib.util
    import sys
    from lll.ilvis0_source_point_derivatives import load_kernel,Kernel
    from lll import ilvis0_direct_source as candidate
    from lll import ilvis0_rotation_roundoff as values,ilvis0_rotation_derivative as derivatives
    from lll.ilvis0_coupled_map_controls import Allowance
    from lll.ilvis0_control_shards import _check_continue
    if not __debug__:raise ValueError('known-answer assertions must be enabled')
    spec=task['payload']
    if importlib.metadata.version('pytest')!=spec['pytest']:raise ValueError('test environment changed')
    sources=context.root/'source-freeze'
    kernel,compilation=load_kernel(context.directory/'compiled',source_directory=sources/'analysis/lll')
    if compilation['compiler']!=spec['compiler']:raise ValueError('compiler changed')
    events=[]
    def persist(event):
        _check_continue(context.root,context.manifest)
        context.save(f'reservation-{len(events)+1:03d}.json',event);events.append(event)
    budget=Allowance(spec['auxiliary_limits'],persist)
    if spec['auxiliary_limits']['rejections']:budget.reserve(dict(rejections=spec['auxiliary_limits']['rejections']))
    def initialize(*args):
        budget.reserve(dict(initializations=1));return kernel.initialize(*args)
    def append(*args):
        context.charge(bound_calls=1,bound_steps=1);return kernel.append(*args)
    original_radius=candidate.radius
    def radius(*args,**kwargs):
        # Invalid calls are rejection checks, not executed bounds.
        frame,_,rows=args
        if kwargs.get('phase') in (0,1) and type(kwargs.get('phase')) is int and rows.shape==(2,2,3,27):
            context.charge(bound_calls=1,bound_steps=0)
        return original_radius(*args,**kwargs)
    originals=(values.enclose,derivatives.enclose,derivatives.values)
    def reference(function):
        def counted(*args,**kwargs):
            budget.reserve(dict(rational_references=1));return function(*args,**kwargs)
        return counted
    values.enclose=reference(originals[0]);derivatives.enclose=reference(originals[1]);derivatives.values=reference(originals[2])
    candidate.radius=radius
    try:
        tests=sources/'analysis/tests';sys.path.insert(0,str(tests))
        path=tests/'test_ilvis0_direct_source.py'
        module_spec=importlib.util.spec_from_file_location('_frozen_direct_source_controls',path)
        module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
        getattr(module,spec['function'])(Kernel(initialize,append,kernel.state_bytes),*spec.get('arguments',[]))
    finally:
        values.enclose,derivatives.enclose,derivatives.values=originals;candidate.radius=original_radius
    if budget.counts!=spec['auxiliary_limits']:raise ValueError('direct-source work differs from frozen recipe')
    context.save('compilation.json',compilation)
    return dict(identity=task['identity'],passed=True,function=spec['function'],work=budget.counts,
        state_bytes=kernel.state_bytes,parameter_count=27,original_reads=0,optimizer_starts=0,
        full_native_evaluations=0,native_propagation_qualified=False,
        observational_coverage_qualified=False,scientific_decision='abstain')
