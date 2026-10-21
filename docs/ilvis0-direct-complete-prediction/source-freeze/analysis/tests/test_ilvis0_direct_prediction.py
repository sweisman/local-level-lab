from copy import deepcopy
import pytest

@pytest.mark.parametrize("model,profile",[(m,p) for m in range(3) for p in (False,True)])
def test_training_conditioned_direct_adapter_preserves_truth_and_complete_audits(tmp_path,monkeypatch,model,profile,runtime=None):
    import importlib.util,json
    from pathlib import Path
    from types import SimpleNamespace
    import numpy as np
    from lll import ilvis0_control_shards as runner,ilvis0_transform_native as native_bound
    from lll import ilvis0_transform_envelope as joint,ilvis0_product_prediction as product,ilvis0_rotation_products as products
    from lll.ilvis0_orientation_cover import sector
    from lll.ilvis0_shape import load_tangent
    from lll.ilvis0_sharded_native import plain
    from test_ilvis0_native_box_bounds import configuration
    from test_ilvis0_regrouped_history import native
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_direct_prediction.py'
    assert path.exists(),"training-conditioned direct-source adapter is missing"
    spec=importlib.util.spec_from_file_location('_isolated_directional_adapter',path)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    config=configuration();config.update(model=model,profile=profile)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    box=sector(4);center=box['center'];times=[.015,.03];time=.05
    reference=native_bound.make_reference(config,theta,dv,dt,**{k:box[k] for k in ('lower','upper','center')})
    kernel,kernel_info=load_tangent(tmp_path/'kernel')
    if runtime:runtime.save('setup/native-compilation.json',kernel_info)
    original_native=native;native_count=0
    def native(*args):
        nonlocal native_count
        if runtime:runtime.before_native(n)
        value,jacobian=original_native(*args);native_count+=1
        if runtime:runtime.save(f'setup/native-{native_count:02d}.json',plain(dict(point=args[-1],prediction=value,jacobian=jacobian)))
        return value,jacobian
    scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.])
    predictions=[native(kernel,config,theta,dv,dt,t,center) for t in times+[time]]
    values=np.array([p[0] for p in predictions]);jac=np.array([p[1] for p in predictions])
    reports=[]
    for t in times+[time]:
        if runtime:runtime.before_legacy_bound(n)
        report=native_bound.enclose(config,theta,dv,dt,time=t,lower=box['lower'],upper=box['upper'],reference=reference)
        reports.append(report)
        if runtime:runtime.save(f'setup/legacy-bound-{len(reports):02d}.json',report.report())
    truth=center.copy();truth[1]+=.01;truth[12]+=.02;truth[13]-=.02;truth[18]+=.02
    observed=np.array([native(kernel,config,theta,dv,dt,t,truth)[0] for t in times+[time]])
    region51=joint.training(times=times,observations=observed[:-1],native_values=values[:-1],native_jacobians=jac[:-1],
        reports=reports[:-1],reference=reference,physical_lower=box['lower'],physical_upper=box['upper'],
        coordinate_scale=scale,origin=config['initial_c'],noise_allowance=np.full((2,3),.001))
    if runtime:runtime.before_initial_future()
    envelope=joint.future(region51,time=time,native_value=values[-1],native_jacobian=jac[-1],report=reports[-1],reference=reference)
    future=plain(dict(parameter_count=51,lower=region51.lower,upper=region51.upper,time_s=time,
        reference=reference.report(),fixed_center=center,nominal=values[-1],jacobian=jac[-1],bound=reports[-1].report(),envelope=envelope))
    root_training=plain(dict(region=region51.report(),times_s=times,observations=observed[:-1],nominal=values[:-1],jacobian=jac[:-1],reference=reference.report()))
    parent_input=dict(training=root_training,reference=reference.report(),lower=future['lower'],upper=future['upper'])
    from lll.ilvis0_acceleration_projection import project
    parent_certificate=project(**parent_input,reserve=runtime.reserve_projection if runtime else lambda *_:None)
    if runtime:runtime.before_product_setup()
    cuts=products.build(reference.transform.report(),initial_r=reference.parent.initial_r.tolist(),limits=reference.parent.limits.tolist(),
        physical_center=center.tolist(),lower=future['lower'],upper=future['upper'],reference_binding=reference.parent.binding,
        source_id=reference.parent.source_id,numerical_allowance=1e-8)
    region78=product.extend(dict(region=plain(region51.report())),future,cuts)
    future=product.rebuild(region78,future,region78['lower'],region78['upper'],reserve=runtime.reserve_product if runtime else lambda _:None)
    training=plain(dict(region=region78,times_s=times,observations=observed[:-1],nominal=values[:-1],jacobian=jac[:-1],reference=reference.report()))
    future['lower'][6]=training['region']['lower'][6]=-.2
    future['upper'][6]=training['region']['upper'][6]=.2
    child=deepcopy(training);child['region'].update(lower=future['lower'],upper=future['upper'])
    condition_path=tmp_path/'condition.json';condition_path.write_text(json.dumps(dict(parent_input=parent_input,parent_certificate=parent_certificate,child_training=child)))
    identity='local-complete';old=plain(dict(identity=identity,parameter_count=78,passed=True,excluded=False,task=dict(model=model,profile=profile,sector=4),
        truth_in_sector=True,known_shared_error=reference.normalized_values_at(truth),future_truth_m=(observed[-1]-config['initial_c'])*scale))
    bundle_path=tmp_path/'bundle.json';bundle_path.write_text(json.dumps(dict(training=training,future=future,result=old,product_cuts=cuts)))
    case_path=tmp_path/'case.json';case_path.write_text(json.dumps(plain(dict(configuration=config,theta=theta,dv=dv,dt=dt,truth=truth))))
    artifacts={};charges=[]
    if runtime is None:monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    def save(name,value):
        artifacts[name]=value
        if runtime:runtime.save('adapter/'+name,plain(value))
    def charge(**values):
        if runtime:runtime.charge(**values)
        charges.append(values)
    import shutil,subprocess
    if runtime is None:
        frozen=tmp_path/'source-freeze/analysis/lll';frozen.mkdir(parents=True)
        for name in ('ilvis0_batched_bounds.cpp','ilvis0_compiled_bounds.cpp','ilvis0_source_stream.cpp','ilvis0_tangent.cpp','ilvis0_source_derivative_intervals.cpp','ilvis0_source_point_derivatives.cpp'):shutil.copyfile(path.parent/name,frozen/name)
    context=SimpleNamespace(root=runtime.root if runtime else tmp_path,manifest=runtime.manifest if runtime else {},shard=runtime.shard if runtime else 0,input_path=lambda key=None:case_path if key=='case' else condition_path if key=='condition' else bundle_path,
        save=save,charge=charge)
    limits=adapter.allowances(n,2)
    task=dict(identity=identity,payload=dict(case_key='case',condition_key='condition',packets=n,limits=limits,maximum_bound_seconds=30.,compiler=subprocess.check_output(['c++','--version'],text=True).splitlines()[0]))
    # A proposal may use the native-bound engine, but never a fresh native prediction.
    monkeypatch.setattr('lll.ilvis0_shape.load_tangent',lambda *_:pytest.fail('no new native prediction'))
    result=adapter.evaluate(task,context)
    assert result['passed'] and not result['excluded'] and result['known_truth_retained']
    assert result['work']==limits and len(charges)==3 and sum(c['bound_steps'] for c in charges)==27*n
    assert artifacts['training-audit.json']['rows_checked']==12
    assert artifacts['independent-audit.json']['exact_supports_checked']==6
    assert list(artifacts).index('future.json')<list(artifacts).index('truth-audit.json')
    assert result['native_evaluations']==result['original_reads']==result['optimizer_starts']==0
    if runtime:runtime.save('adapter-result.json',plain(result))
    from lll.ilvis0_directional_prediction import audit_training
    updated=deepcopy(artifacts['training.json']['region'])
    updated['inequality_upper'][-1]+=.1
    with pytest.raises(ValueError,match='reconstruction'):
        audit_training(training,future,[artifacts['bound-01.json'],artifacts['bound-02.json']],updated)
