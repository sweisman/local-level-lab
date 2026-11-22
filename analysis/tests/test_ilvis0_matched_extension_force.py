import pytest

from lll.ilvis0_matched_extension_force import evaluate_gain, limits_for


def test_extension_force_charges_full_declared_support_and_envelope_allowance():
    assert limits_for(1123) == dict(native_calls=0, packet_visits=0, bound_calls=1123, bound_steps=216739)


def test_extension_force_gain_uses_only_training_and_retains_later_violations():
    rows = [dict(model='sphere_still', side='training', measured_lower_mps2=10., required_upper_mps2=10.),
            dict(model='sphere_still', side='later', measured_lower_mps2=10.1, required_upper_mps2=10.)]
    score = evaluate_gain(rows)['sphere_still']
    assert score['training_gain'] == 0.
    assert score['later_violations'] == 1
    assert score['maximum_later_excess_mps2'] == pytest.approx(.1)
