# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charge all fixture and target work in the frozen joint-adapter controls."""
FIXTURE_LIMITS=dict(fixture_setups=1,product_setups=1,initial_future_proposals=6,
    initial_future_supports=12,projection_proposals=6,projection_supports=18,
    product_proposals=6,product_supports=18)


class FixtureRuntime:
    def __init__(self,context):
        from lll.ilvis0_coupled_map_controls import Allowance
        from lll.ilvis0_control_shards import _check_continue
        self.context=context;self.root=context.root;self.manifest=context.manifest;self.shard=context.shard
        self.events=[];self.ordinals=[]
        def persist(event):
            _check_continue(context.root,context.manifest)
            context.save(f'fixture-reservation-{len(self.events)+1:03d}.json',event);self.events.append(event)
        self.budget=Allowance(FIXTURE_LIMITS,persist)
        self.budget.reserve(dict(fixture_setups=1))

    def save(self,name,value):self.context.save(name,value)
    def charge(self,**values):self.context.charge(**values)
    def before_native(self,n):self.charge(native_calls=1,packet_visits=n)
    def before_legacy_bound(self,n):self.charge(bound_calls=1,bound_steps=2*n)
    def before_initial_future(self):self.budget.reserve(dict(initial_future_proposals=6,initial_future_supports=12))
    def before_product_setup(self):self.budget.reserve(dict(product_setups=1))
    def reserve_projection(self,proposals,supports):
        self.budget.reserve(dict(projection_proposals=proposals,projection_supports=supports))
    def reserve_product(self,ordinal):
        if ordinal!=len(self.ordinals)+1 or ordinal>6:raise ValueError('six sequential setup product proposals required')
        self.budget.reserve(dict(product_proposals=1,product_supports=3));self.ordinals.append(ordinal)


def evaluate(task,context):
    import importlib.metadata
    import importlib.util
    import subprocess
    import sys
    import pytest
    if not __debug__:raise ValueError('known-answer assertions must remain enabled')
    spec=task['payload']
    if importlib.metadata.version('pytest')!=spec['pytest']:raise ValueError('test package changed')
    if subprocess.check_output(['c++','--version'],text=True).splitlines()[0]!=spec['compiler']:
        raise ValueError('compiler changed from the freeze')
    if spec['fixture_limits']!=FIXTURE_LIMITS:raise ValueError('fixed fixture allowance changed')
    runtime=FixtureRuntime(context);sources=context.root/'source-freeze/analysis/tests'
    sys.path.insert(0,str(sources));path=sources/'test_ilvis0_direct_prediction.py'
    module_spec=importlib.util.spec_from_file_location('_frozen_joint_known_answer',path)
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    directory=context.directory/'fixture';directory.mkdir(parents=True,exist_ok=True)
    with pytest.MonkeyPatch.context() as patch:
        module.test_training_conditioned_direct_adapter_preserves_truth_and_complete_audits(
            directory,patch,spec['model'],spec['profile'],runtime=runtime)
    if runtime.budget.counts!=runtime.budget.limits:raise ValueError('fixture work differs from its fixed recipe')
    for name in ('bundle.json','case.json','condition.json'):context.note_file(directory/name)
    context.save('fixture-accounting.json',runtime.budget.counts)
    return dict(identity=task['identity'],model=spec['model'],profile=spec['profile'],passed=True,
        physical_parameter_count=27,expression_parameter_count=51,enclosure_parameter_count=78,
        fixture_work=runtime.budget.counts,original_reads=0,optimizer_starts=0,
        known_answer_qualification=True,observational_coverage_qualified=False,scientific_decision='abstain')
