"""Withheld receiver scoring after a frozen two-law forecast."""

import pytest


def _case():
    rows = [dict(time_s=100. + i, latitude_deg=45. + i*1e-5,
                 longitude_deg=2. + i*1e-5, height_m=1000.)
            for i in range(5)]
    coordinates = [[0.7853981633974483 + i*1.7453292519943296e-7,
                    0.03490658503988659 + i*1.7453292519943296e-7,
                    1000.] for i in range(5)]
    candidate = dict(forecast=dict(coordinates=coordinates),
                     fit=dict(converged=True, stopping_rule_verified=True))
    interval = dict(supported=True, lower=[[-1., -1., 0.]]*2,
                    upper=[[1., 1., 2000.]]*2,
                    prediction_target='receiver_measurement')
    result = dict(candidates={'increment': candidate, 'point': candidate},
                  simultaneous_law_family={
                      'physical_position': dict(supported=True),
                      'receiver_measurement': interval},
                  withheld_truth=rows)
    return result, rows, [float(i) for i in range(5)]


def test_observed_score_uses_receiver_only_and_never_physical_truth():
    from lll.prediction_observed_scoring import score_recording
    result, rows, times = _case()
    saved = {}
    value = score_recording(result, training_rows=rows[:3],
                            times=times, time_origin_s=100.,
                            save=lambda name, item: saved.setdefault(name, item))
    assert value['training_epochs'] == 3
    assert value['prediction_epochs'] == 2
    assert value['physical_position_truth_available'] is False
    assert value['scientific_decision'] == 'abstain'
    assert value['receiver_interval_score']['epochs'] == 2
    assert set(value['candidate_receiver_sections']) == {'increment', 'point'}
    assert saved['withheld-receiver-score.json'] == value


def test_observed_score_rejects_changed_training_prefix():
    from lll.prediction_observed_scoring import score_recording
    result, rows, times = _case()
    altered = [dict(row) for row in rows[:3]]
    altered[1]['height_m'] += 1.
    with pytest.raises(ValueError, match='earlier receiver'):
        score_recording(result, training_rows=altered, times=times,
                        time_origin_s=100., save=lambda *args: None)


def test_observed_score_abstains_when_interval_unsupported():
    from lll.prediction_observed_scoring import score_recording
    result, rows, times = _case()
    result['simultaneous_law_family']['receiver_measurement'] = dict(
        supported=False, reason='candidate_fit_unqualified')
    value = score_recording(result, training_rows=rows[:3], times=times,
                            time_origin_s=100., save=lambda *args: None)
    assert value['receiver_interval_score'] is None
    assert value['interval_reason'] == 'candidate_fit_unqualified'
    assert value['scientific_decision'] == 'abstain'
