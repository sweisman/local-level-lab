# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import numpy as np

from lll.ilvis0_staged_native import predict


def test_native_stages_keep_prior_constraints_and_then_predict_without_future_observations(tmp_path,model=0,profile=True,runtime=None):
    from test_ilvis0_native_box_bounds import configuration
    from test_ilvis0_regrouped_history import native
    from lll import ilvis0_direct_native as candidate
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_batched_transport import configure_backend
    from lll.ilvis0_source_stream import load_stream
    from lll.ilvis0_source_derivative_intervals import load_kernel
    from lll.ilvis0_source_point_derivatives import load_kernel as load_point
    config=configuration();config.update(model=model,profile=profile);n=32;dt=np.full(n,.005)
    theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    lo=np.full(27,-1.);hi=np.full(27,1.);center=np.zeros(27)
    if runtime:runtime.reserve(reference_setups=1)
    reference=candidate.make_reference(config,theta,dv,dt,lower=lo,upper=hi,center=center)
    if runtime:
        runtime.save('case.json',dict(configuration=config,theta=theta,dv=dv,dt=dt,center=center,lower=lo,upper=hi))
        runtime.save('reference.json',reference.report())
    directory=tmp_path/'kernels'; arithmetic=configure_backend(directory)
    source,source_meta=load_stream(directory); derivative,derivative_meta=load_kernel(directory)
    point,point_meta=load_point(directory); kernel,native_meta=load_tangent(directory)
    if runtime:runtime.save('compilation.json',dict(arithmetic=arithmetic,source=source_meta,
        derivative=derivative_meta,point=point_meta,native=native_meta))
    def model(time_s,parameters):
        if runtime:return runtime.native(kernel,config,theta,dv,dt,time_s,parameters)
        return native(kernel,config,theta,dv,dt,time_s,parameters)
    truth=np.zeros(27);truth[0]=.1;truth[6]=.05;truth[25]=.25
    times=[.015,.03,.06,.09];observations=np.array([model(t,truth)[0] for t in times])
    records={};charges={};bounds=[]
    def reserve(**values):
        if runtime:runtime.reserve(**values)
        for k,v in values.items():charges[k]=charges.get(k,0)+v
    def bound(time_s,proof):
        if runtime:runtime.before_bound(n)
        bounds.append((time_s,proof.report()))
        result=candidate.enclose(config,theta,dv,dt,time=time_s,lower=lo,upper=hi,reference=reference,
            conditioning=proof,source_kernel=source,derivative_kernel=derivative,point_kernel=point,maximum_seconds=30.)
        assert all(result.metadata[k]<=n for k in ('source_reference_steps','source_derivative_steps',
                                                   'source_direct_steps','rounded_source_prefixes'))
        return result
    def save(name,value):
        records[name]=value
        if runtime:runtime.save(name,value)
    result=predict(training_times=times,observations=observations,noise_allowance=np.full((4,3),.001),
        stage_sizes=[2,2],future_time=.13,reference=reference,lower=lo,upper=hi,
        coordinate_scale=[6371000.,6371000.*np.cos(config['initial_c'][0]),1.],origin=config['initial_c'],
        native=model,bound=bound,reserve=reserve,save=save)
    assert len(bounds)==5 and bounds[0][1]['uses_training_data'] is False
    assert all(p['applies_only_to_training_region'] for _,p in bounds[2:])
    assert result['region']['times_s']==times and len(result['region']['inequality_design'])==24
    assert result['physical_parameter_count']==27 and not result['future_observations_used']
    assert charges['lp_proposals']==18 and charges['exact_supports']==66
    assert result['independent_audit']['exact_supports_checked']==6
    if runtime:runtime.reserve(truth_audits=1)
    future_value,_=model(.13,truth)  # Constructed only after saving the prediction.
    scale=result['region']['coordinate_scale']; origin=result['region']['origin']
    expected=[(F(float(v))-F(float(o)))*F(float(s)) for v,o,s in zip(future_value,origin,scale)]
    assert all(F(a)<=v<=F(b) for a,v,b in zip(result['future']['lower'],expected,result['future']['upper']))
    assert records['stage-02-region.json']['inequality_design'][:12]==records['stage-01-region.json']['inequality_design']
    witness=[F(float(v)) for v in list(truth)+list(reference.normalized_values_at(truth))]
    slacks=[]
    for stage in (1,2):
        region=records[f'stage-{stage:02d}-region.json']
        assert all(F(a)<=v<=F(b) for a,v,b in zip(region['lower'],witness,region['upper']))
        slacks.extend(sum((F(a)*v for a,v in zip(row,witness)),F(0))-F(limit)
                      for row,limit in zip(region['inequality_design'],region['inequality_upper']))
    assert max(slacks)<=0
    if runtime:
        runtime.save('truth-audit.json',dict(known_truth_retained=True,evaluated_after_bounds=True,
            maximum_exact_slack=str(max(slacks)),future_truth_m=list(map(str,expected))))
