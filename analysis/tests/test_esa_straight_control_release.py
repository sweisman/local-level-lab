import pytest


def test_release_keeps_the_cheapest_start_even_if_its_forecast_is_missing():
    from lll import esa_straight_control_forecast as study, esa_straight_control_release as gate

    outcomes = {case['identity']: {'converged': False} for case in study.tasks()}
    first, second = (case['identity'] for case in study.tasks()[:2])
    outcomes[first] = {'converged': True, 'cost': 1.}
    outcomes[second] = {'converged': True, 'cost': 1., 'forecast_sha256': 'a'*64}
    selected = gate.primary_starts(outcomes)
    assert selected[0]['identity'] == first
    assert selected[0]['state'] == 'primary_forecast_missing'
    del outcomes[second]
    with pytest.raises(ValueError, match='all 16 terminal'):
        gate.primary_starts(outcomes)


def test_control_scoring_refuses_changed_release_before_opening_positions(monkeypatch, tmp_path):
    from lll import esa_straight_control_release as gate

    def unexpected(*args, **kwargs):
        pytest.fail('later receiver positions were accessed before release')

    monkeypatch.setattr(gate, 'release', lambda *args, **kwargs: ({'primary': []}, {}, {}))
    monkeypatch.setattr(gate, 'receiver_positions', unexpected)
    with pytest.raises(ValueError, match='exact saved release'):
        gate.score(tmp_path, expected_manifest_sha256='b'*64, saved_release=b'changed')


def test_turn_gain_is_a_paired_difference_and_keeps_missing_controls():
    from lll.esa_straight_control_release import matched_gains

    arms = ('native', 'steady', 'turn', 'both')
    forecasts = {identity: {'scores': {arm: {'negative_log_score': value} for arm, value in
                 zip(arms, values, strict=True)}} for identity, values in
                 [('turn', [20., 17., 15., 13.]), ('control', [20., 18., 19., 17.])]}
    gains = matched_gains([('turn', 'control'), ('turn', None)], forecasts)
    assert gains[0]['extra_turn_gain'] == {'without_steady': 4., 'with_steady': 3.}
    assert gains[1]['extra_turn_gain'] is None


def test_turn_timing_control_changes_only_angular_exposure():
    from lll.esa_straight_control_release import SCORE_VERSION, transplant_exposure
    from lll.studies.artifacts import encoded
    import json

    target = dict(policy=SCORE_VERSION, law='increment', times_s=list(range(1, 121)),
                  angular_exposure=[0.]*120, training_sha256='a'*64, mean_geodetic=[[1., 2., 3.]]*120)
    donor = dict(target, times_s=list(range(9, 129)), angular_exposure=[1.]*120,
                 training_sha256='b'*64, mean_geodetic=[[4., 5., 6.]]*120)
    transformed = json.loads(transplant_exposure(encoded(target), encoded(donor)))
    assert transformed == dict(target, angular_exposure=donor['angular_exposure'])
    with pytest.raises(ValueError, match='matched exposure'):
        transplant_exposure(encoded(target), encoded(dict(donor, law='point')))
