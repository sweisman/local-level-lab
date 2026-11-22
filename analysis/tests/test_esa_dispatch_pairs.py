from types import SimpleNamespace

import pytest


def test_dispatch_pairs_keep_all_observed_settings_and_finite_native_work():
    from lll import esa_dispatch_pairs as study

    items = study.tasks(native_packets=359729, training_prefix_packets=239750)
    assert len(items) == len({item['identity'] for item in items}) == 16
    assert {item['payload']['model'] for item in items} == {'sphere_rotating', 'sphere_still'}
    assert {item['payload']['profile'] for item in items} == {False, True}
    assert {item['payload']['start'] for item in items} == {0, 1}
    assert {item['payload']['policy_id'] for item in items} == {'reported-short-v1', 'reported-persistent-v1'}
    assert all(item['limits']['native_calls'] == 402 for item in items)
    assert all(item['limits']['packet_visits'] == 2*(200*239750*800 + 359729*1200) for item in items)
    with pytest.raises(ValueError, match='bounded stream'):
        study.tasks(native_packets=1, training_prefix_packets=2)


def test_dispatch_pair_rejects_forecast_positions_before_access():
    from lll import esa_dispatch_pairs as study

    def read(*args):
        pytest.fail('out-of-scope manifest read data')

    task = study.tasks(native_packets=359729, training_prefix_packets=239750)[0]
    context = SimpleNamespace(manifest=dict(scope=study.SCOPE,
        inputs=dict.fromkeys(study.INPUTS | {'scoring'})), input_path=read)
    with pytest.raises(ValueError, match='later positions'):
        study.evaluate(task, context)


def test_dispatch_group_requires_both_pairs_and_checks_cross_start_forecast_spread(monkeypatch):
    from lll import airquantumgrav_scoring, esa_dispatch_pairs as study

    class Coordinates(list):
        def tolist(self):
            return list(self)

    def in_metres(candidate, reference):
        return Coordinates([[a-b for a, b in zip(point, anchor, strict=True)]
                            for point, anchor in zip(candidate, reference, strict=True)])

    monkeypatch.setattr(airquantumgrav_scoring, 'receiver_errors', in_metres)
    times = list(range(1200))
    pairs = {}
    for start in (0, 1):
        costs = (1. + start*5e-9, 1. + (1-start)*5e-9)
        pair = dict(passed=True, fits={}, forecasts={})
        for method, cost in zip(study.METHODS, costs, strict=True):
            pair['fits'][method] = dict(model='sphere_rotating', profile=True,
                                       policy_id=study.POLICIES[0], start=start, passed=True,
                                       converged=True, training_cost=cost)
            pair['forecasts'][method] = dict(times_s=times, coordinates=[[.004*start, 0., 0.]]*1200,
                training_epochs=800, prediction_epochs=400, prediction_receiver_positions_used=False)
        pairs[start] = pair

    assert study.assess_group({0: pairs[0]}, times=times, materials='a'*64)['state'] == 'incomplete'
    accepted = study.assess_group(pairs, times=times, materials='a'*64)
    assert accepted['state'] == 'equivalent'
    assert accepted['rule']['reference_primary'] == 0
    assert accepted['rule']['candidate_primary'] == 1
    pairs[1]['forecasts']['selective']['coordinates'] = [[.012, 0., 0.]]*1200
    rejected = study.assess_group(pairs, times=times, materials='a'*64)
    assert rejected['state'] == 'different'
    assert rejected['rule']['candidate_within_maximum_m'] == .012
