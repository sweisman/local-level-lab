# SPDX-License-Identifier: AGPL-3.0-or-later
"""Charge the complete generated staged-native control path."""
LIMITS=dict(reference_setups=1,physical_proofs=1,training_proofs=2,lp_proposals=18,exact_supports=66,
    source_setups=5,source_steps=160,source_body_bounds=160,source_derivative_setups=5,
    source_derivative_steps=160,source_point_setups=5,source_point_steps=160,source_direct_steps=160,truth_audits=1)


class Runtime:
    def __init__(self,context,spec):
        from .ilvis0_coupled_map_controls import Allowance
        from .ilvis0_control_shards import _check_continue
        self.context=context;self.spec=spec;self.events=0;self.native_calls=0;self.bounds=0;self.saved={}
        def persist(event):
            _check_continue(context.root,context.manifest);self.events+=1
            context.save(f'reservation-{self.events:03d}.json',event)
        self.budget=Allowance(LIMITS,persist)

    def reserve(self,**values):self.budget.reserve(values)

    def save(self,name,value):
        from .ilvis0_sharded_native import plain
        value=plain(value)
        if name=='compilation.json':
            for kind,metadata in value.items():
                if metadata['compiler']!=self.spec['compiler']:raise ValueError('compiler changed')
                if kind=='native':
                    if metadata['source_sha256']!=self.context.manifest['sources']['analysis/lll/ilvis0_tangent.cpp']:
                        raise ValueError('native source changed')
                else:
                    for source,digest in metadata['sources'].items():
                        if digest!=self.context.manifest['sources']['analysis/lll/'+source]:
                            raise ValueError('bound source changed')
        self.context.save(name,value);self.saved[name]=value

    def before_bound(self,n):
        if n!=32 or self.bounds>=5:raise ValueError('five 32-packet bounds per identity required')
        self.reserve(source_setups=1,source_steps=n,source_body_bounds=n,source_derivative_setups=1,
            source_derivative_steps=n,source_point_setups=1,source_point_steps=n,source_direct_steps=n)
        self.context.charge(bound_calls=1,bound_steps=9*n);self.bounds+=1

    def native(self,kernel,config,theta,dv,dt,time_s,parameters):
        import ctypes
        import numpy as np
        n=len(dt)
        if n!=32 or self.native_calls>=10:raise ValueError('ten 32-packet native queries per identity required')
        self.context.charge(native_calls=1,packet_visits=n);self.native_calls+=1
        out=np.empty((1,3));jac=np.empty((3,27));flag=ctypes.c_int()
        code=kernel(n,theta,dv,dt,1,np.array([time_s]),config['initial_c'],config['initial_v'],config['initial_r'],
            config['limits'],np.ascontiguousarray(parameters,float),config['model'],int(config['profile']),
            config['gravity'],config['radius'],out,jac,ctypes.byref(flag))
        record=dict(time_s=time_s,point=parameters,status=int(code),warning=flag.value)
        if not code:record.update(prediction=out[0],jacobian=jac)
        self.save(f'native-{self.native_calls:02d}.json',record)
        if code:raise ValueError('native staged control query failed')
        return out[0],jac


def evaluate(task,context):
    import importlib.metadata,importlib.util,sys
    if not __debug__:raise ValueError('known-answer assertions must remain enabled')
    spec=task['payload']
    if spec['limits']!=LIMITS or importlib.metadata.version('pytest')!=spec['pytest']:
        raise ValueError('fixed source-control recipe or test environment changed')
    if (spec['packets']!=32 or spec['dt_s']!=.005 or spec['stage_sizes']!=[2,2]
            or spec['training_s']!=[.015,.03,.06,.09] or spec['future_s']!=.13):
        raise ValueError('declared staged native geometry changed')
    runtime=Runtime(context,spec);tests=context.root/'source-freeze/analysis/tests';sys.path.insert(0,str(tests))
    module_spec=importlib.util.spec_from_file_location('_frozen_staged_known_answer',tests/'test_ilvis0_staged_native.py')
    module=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(module)
    directory=context.directory/'fixture';directory.mkdir(parents=True,exist_ok=True)
    module.test_native_stages_keep_prior_constraints_and_then_predict_without_future_observations(
        directory,model=spec['model'],profile=spec['profile'],runtime=runtime)
    if runtime.budget.counts!=LIMITS or runtime.native_calls!=10 or runtime.bounds!=5:
        raise ValueError('staged control work differs from the frozen recipe')
    region=runtime.saved['stage-02-region.json'];future=runtime.saved['future.json']
    runtime.save('accounting.json',runtime.budget.counts)
    return dict(identity=task['identity'],passed=True,model=spec['model'],profile=spec['profile'],
        work=runtime.budget.counts,native_evaluations=10,bound_evaluations=5,parameter_count=51,
        physical_parameter_count=27,training_epochs=4,stages=2,inequalities=len(region['inequality_upper']),
        future_width_m=[b-a for a,b in zip(future['lower'],future['upper'])],
        physical_acceleration_radius=runtime.saved['physical-proof.json']['norm_change'],
        stage_acceleration_radii=[runtime.saved[f'stage-{i:02d}-proof.json']['norm_change'] for i in (1,2)],
        known_truth_retained=True,original_reads=0,optimizer_starts=0,
        recording_length_usefulness_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')
