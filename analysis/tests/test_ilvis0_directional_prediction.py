# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import pytest
from lll.ilvis0_directional_prediction import build_future,audit_future
from test_ilvis0_coupled_prediction import fixture


def test_fresh_bound_can_be_wider_without_being_hidden_or_clipped():
    training,saved,_,_=fixture();region=training['region'];bound=deepcopy(saved['bound'])
    bound['unshared_remainder']=[v+1. for v in bound['unshared_remainder']]
    future=build_future(region,saved,bound,region['lower'],region['upper'],reserve=lambda _:None)
    assert any(a<b for a,b in zip(future['envelope']['lower'],saved['envelope']['lower']))
    check=audit_future(region,saved,bound,future)
    assert check['passed'] and check['exact_supports_checked']==6


@pytest.mark.parametrize('change',['certificate','coefficient','remainder','column','endpoint'])
def test_independent_future_audit_rejects_changed_evidence(change):
    training,saved,_,_=fixture();region=training['region'];bound=deepcopy(saved['bound'])
    future=build_future(region,saved,bound,region['lower'],region['upper'],reserve=lambda _:None)
    if change=='certificate':future['envelope']['certificates'][0]['upper']='0'
    if change=='coefficient':future['bound']['previous_coefficients'][0][0]+=.1
    if change=='remainder':future['bound']['unshared_remainder'][0]+=.1
    if change=='column':future['lower']=future['lower'][:-1]
    if change=='endpoint':future['envelope']['upper'][0]+=.1
    with pytest.raises(ValueError):audit_future(region,saved,bound,future)


def test_frozen_style_adapter_runs_full_training_prediction_and_post_range_truth_audit(tmp_path,monkeypatch):
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
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_directional_prediction.py'
    spec=importlib.util.spec_from_file_location('_isolated_directional_adapter',path)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    config=configuration();config.update(model=0,profile=False)
    n=13;dt=np.full(n,.005);theta=np.tile([1e-5,-2e-5,3e-6],(n,1));dv=np.tile([0.,0.,-.04905],(n,1))
    box=sector(4);center=box['center'];times=[.015,.03];time=.05
    reference=native_bound.make_reference(config,theta,dv,dt,**{k:box[k] for k in ('lower','upper','center')})
    kernel=load_tangent(tmp_path/'kernel')[0];scale=np.array([6371000.,6371000.*np.cos(config['initial_c'][0]),1.])
    predictions=[native(kernel,config,theta,dv,dt,t,center) for t in times+[time]]
    values=np.array([p[0] for p in predictions]);jac=np.array([p[1] for p in predictions])
    reports=[native_bound.enclose(config,theta,dv,dt,time=t,lower=box['lower'],upper=box['upper'],reference=reference) for t in times+[time]]
    region51=joint.training(times=times,observations=values[:-1],native_values=values[:-1],native_jacobians=jac[:-1],
        reports=reports[:-1],reference=reference,physical_lower=box['lower'],physical_upper=box['upper'],
        coordinate_scale=scale,origin=config['initial_c'],noise_allowance=np.full((2,3),.001))
    envelope=joint.future(region51,time=time,native_value=values[-1],native_jacobian=jac[-1],report=reports[-1],reference=reference)
    future=plain(dict(parameter_count=51,lower=region51.lower,upper=region51.upper,time_s=time,
        reference=reference.report(),fixed_center=center,nominal=values[-1],jacobian=jac[-1],bound=reports[-1].report(),envelope=envelope))
    cuts=products.build(reference.transform.report(),initial_r=reference.parent.initial_r.tolist(),limits=reference.parent.limits.tolist(),
        physical_center=center.tolist(),lower=future['lower'],upper=future['upper'],reference_binding=reference.parent.binding,
        source_id=reference.parent.source_id,numerical_allowance=1e-8)
    region78=product.extend(dict(region=plain(region51.report())),future,cuts)
    future=product.rebuild(region78,future,region78['lower'],region78['upper'],reserve=lambda _:None)
    training=plain(dict(region=region78,times_s=times,observations=values[:-1],nominal=values[:-1],jacobian=jac[:-1],reference=reference.report()))
    identity='local-complete';old=plain(dict(identity=identity,passed=True,excluded=False,task=dict(model=0,profile=False,sector=4),
        truth_in_sector=True,known_shared_error=reference.normalized_values_at(center),future_truth_m=(values[-1]-config['initial_c'])*scale))
    bundle_path=tmp_path/'bundle.json';bundle_path.write_text(json.dumps(dict(training=training,future=future,result=old,product_cuts=cuts)))
    case_path=tmp_path/'case.json';case_path.write_text(json.dumps(plain(dict(configuration=config,theta=theta,dv=dv,dt=dt,truth=center))))
    artifacts={};charges=[];monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    context=SimpleNamespace(root=tmp_path,manifest={},input_path=lambda key=None:case_path if key else bundle_path,
        save=lambda name,value:artifacts.update({name:value}),charge=lambda **v:charges.append(v))
    limits=dict(setups=1,proofs=1,training_audits=12,contractions=1,proposals=6,supports=24,truth_audits=1)
    task=dict(identity=identity,payload=dict(case_key='case',packets=n,limits=limits,maximum_bound_seconds=30.))
    # A proposal may use the native-bound engine, but never a fresh native prediction.
    monkeypatch.setattr('lll.ilvis0_shape.load_tangent',lambda *_:pytest.fail('no new native prediction'))
    result=adapter.evaluate(task,context)
    assert result['passed'] and not result['excluded'] and result['known_truth_retained']
    assert result['work']==limits and len(charges)==3 and sum(c['bound_steps'] for c in charges)==6*n
    assert artifacts['training-audit.json']['rows_checked']==12
    assert artifacts['independent-audit.json']['exact_supports_checked']==6
    assert list(artifacts).index('future.json')<list(artifacts).index('truth-audit.json')
    assert result['native_evaluations']==result['original_reads']==result['optimizer_starts']==0
    from lll.ilvis0_directional_prediction import audit_training
    updated=deepcopy(artifacts['training.json']['region'])
    updated['inequality_upper'][-1]+=.1
    with pytest.raises(ValueError,match='reconstruction'):
        audit_training(training,future,[artifacts['bound-01.json'],artifacts['bound-02.json']],updated)
