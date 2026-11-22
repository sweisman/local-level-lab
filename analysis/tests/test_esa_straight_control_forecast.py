from types import SimpleNamespace

import pytest


def test_straight_forecasts_preserve_full_turn_study_matrix_and_limits():
    from lll import esa_repeat_turn_execution as turn, esa_straight_control_forecast as study

    planned = study.tasks()
    assert len(planned) == len({case['identity'] for case in planned}) == len(turn.tasks()) == 16
    for index in study.WINDOWS:
        assert {(case['payload']['law'], case['payload']['start']) for case in planned
                if case['payload']['first_index'] == index} == {
                    (law, start) for law in turn.LAWS for start in (0, 1)
                }
    assert all(case['limits'] == turn.LIMITS for case in planned)


def test_straight_forecast_rejects_outcome_inputs_before_any_read():
    from lll import esa_straight_control_forecast as study
    from lll.esa_repeat_turn_execution_v2 import CONTINUATION_INPUTS

    def denied(*args):
        pytest.fail('forecast opened an unexpected input')

    task = study.tasks()[0]
    for extra in ({'later_positions'}, {'continuation-plan'}, CONTINUATION_INPUTS | {'scoring'}):
        context = SimpleNamespace(
            manifest=dict(scope=study.SCOPE, inputs=dict.fromkeys(study.input_keys() | extra)),
            input_path=denied,
        )
        with pytest.raises(ValueError, match='training and forecast clock'):
            study.evaluate(task, context)


def test_straight_forecast_requires_closed_material(tmp_path):
    from lll import esa_straight_control_forecast as study

    with pytest.raises(ValueError, match='closed straight-control material'):
        study.material_bundle(tmp_path)
