"""A whole-path allowance must be allocated before any candidate is scored."""

from types import SimpleNamespace

import pytest


def test_joint_allowance_is_split_across_all_future_coordinates(monkeypatch):
    from lll.simultaneous_dual_target_wrapper import evaluate
    observed={}
    def fake_dual(physical,receiver,problem,point,forecast,**kw):
        observed['future_alpha']=kw['future_alpha']
        for name,target in (('bounded-physical.json','physical_position'),
                            ('bounded-receiver.json','receiver_measurement')):
            kw['save'](name,dict(prediction_target=target,
                                 marginal_coverage_lower_bound=1-.025-kw['future_alpha'],
                                 later_observations_used=False,
                                 scientific_decision='abstain'))
        return {'prediction_target':'physical_position'}
    monkeypatch.setattr('lll.dual_target_forecast_wrapper.evaluate',fake_dual)
    saved={}
    result=evaluate(object(),object(),SimpleNamespace(gps_times=[1,2]),None,None,
                    theta=None,dv=None,dt=None,times=[1,2,3,4],
                    reserve=lambda **work:None,
                    save=lambda name,value:saved.setdefault(name,value))
    assert result['prediction_target']=='physical_position'
    assert observed['future_alpha']==pytest.approx(.025/6)
    for name in ('bounded-physical.json','bounded-receiver.json'):
        assert saved[name]['nominal_joint_coverage_lower_bound']==pytest.approx(.95)
        assert saved[name]['joint_future_coordinate_count']==6
        assert saved[name]['assumptions_qualified_for_aircraft'] is False


def test_joint_wrapper_rejects_false_marginal_claim(monkeypatch):
    from lll.simultaneous_dual_target_wrapper import evaluate
    def fake_dual(*args,**kw):
        kw['save']('bounded-physical.json',dict(prediction_target='physical_position',
                                               marginal_coverage_lower_bound=.5,
                                               later_observations_used=False))
        return {}
    monkeypatch.setattr('lll.dual_target_forecast_wrapper.evaluate',fake_dual)
    with pytest.raises(ValueError,match='declared marginal'):
        evaluate(object(),object(),SimpleNamespace(gps_times=[1,2]),None,None,
                 theta=None,dv=None,dt=None,times=[1,2,3,4],
                 reserve=lambda **work:None,save=lambda *args:None)
