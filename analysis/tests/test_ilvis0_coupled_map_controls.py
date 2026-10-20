# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from lll import ilvis0_coupled_map_controls as controls
from lll.ilvis0_interval_calibration import Jet,couple
from test_ilvis0_coupled_map import reference


def test_independent_analytic_jacobian_agrees_with_the_source_oracle_differences():
    ref=reference();point=np.full(27,.3);jac=controls.analytic_jacobian(ref,point)
    assert jac.shape==(24,27)
    for j in range(27):
        delta=np.zeros(27);delta[j]=2e-5
        finite=(ref.normalized_values_at(point+delta)-ref.normalized_values_at(point-delta))/(4e-5)
        np.testing.assert_allclose(jac[:,j],finite,atol=3e-5,rtol=0.)


def test_probe_checks_account_for_all_values_derivatives_and_coupled_rows():
    bounds=[Jet.constant(0.)]*24;zero=[0.]*27
    cuts=couple(bounds,bounds,[-1.]*27,[1.]*27,zero)
    check=controls.check_probe(bounds,cuts,zero,np.zeros(24),np.zeros((24,27)),derivative_tolerance=3e-8)
    assert check['passed'] and check['scalar_inequalities']==1392
    wrong=np.zeros((24,27));wrong[1,4]=1.
    assert not controls.check_probe(bounds,cuts,zero,np.zeros(24),wrong,derivative_tolerance=3e-8)['passed']
    actual=np.zeros(24);actual[0]=1.
    assert not controls.check_probe(bounds,cuts,zero,actual,np.zeros((24,27)),derivative_tolerance=3e-8)['passed']


def test_work_reservations_are_durable_before_counter_changes_and_overruns():
    events=[];budget=controls.Allowance(dict(setups=1,intervals=2,oracles=1,jacobians=1,checks=1392),events.append)
    budget.reserve(dict(setups=1));budget.reserve(dict(oracles=1,jacobians=1,checks=1392))
    assert events[-1]['counts']['checks']==1392
    with pytest.raises(ValueError):budget.reserve(dict(checks=1))
    def fail(_):raise OSError('cannot persist')
    blocked=controls.Allowance(dict(setups=1),fail)
    with pytest.raises(OSError):blocked.reserve(dict(setups=1))
    assert blocked.counts==dict(setups=0)


def test_frozen_adapter_exercises_fixed_zero_caps_without_native_calls(tmp_path,monkeypatch):
    import json,gzip
    from types import SimpleNamespace
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_sharded_native import plain
    from lll import ilvis0_control_shards as runner
    case=dict(configuration=configuration(),theta=np.zeros((3,3)),dv=np.tile([0.,0.,-.04905],(3,1)),dt=np.full(3,.005))
    path=tmp_path/'case.json';path.write_text(json.dumps(plain(case)));saved={};noted=[]
    context=SimpleNamespace(root=tmp_path,manifest={},directory=tmp_path/'artifacts',input_path=lambda:path,
        save=lambda k,v:saved.update({k:v}),note_file=noted.append)
    monkeypatch.setattr(runner,'_check_continue',lambda *_:None)
    limits=dict(setups=1,intervals=2,oracles=1,jacobians=1,checks=1392)
    task=dict(identity='fixed-fixture',payload=dict(model=0,profile=True,family='fixed',maximum_probes=1,limits=limits))
    result=controls.evaluate(task,context)
    assert result['passed'] and result['work']==limits
    assert result['checked_value_inequalities']==48 and result['checked_derivative_inequalities']==1296
    assert result['checked_coupled_inequalities']==48
    assert len(json.loads(gzip.decompress(noted[0].read_bytes())))==1
    assert result['native_evaluations']==result['original_reads']==0


@pytest.mark.parametrize('family',['full','sector','fixed','gain-boundary'])
def test_declared_domain_can_construct_the_complete_source_reference(family):
    from test_ilvis0_native_box_bounds import configuration
    from lll.ilvis0_transform_native import make_reference
    config=configuration()
    result=make_reference(config,np.zeros((3,3)),np.tile([0.,0.,-.04905],(3,1)),np.full(3,.005),**controls.domain(family))
    assert result.report()['enclosure_parameter_count']==51
