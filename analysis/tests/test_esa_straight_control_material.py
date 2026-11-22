from types import SimpleNamespace

import pytest


def test_straight_material_scope_rejects_a_later_position_input_before_access():
    from lll import esa_straight_control_material as study

    def access(*args):
        pytest.fail('out-of-scope input was opened')

    context = SimpleNamespace(
        manifest=dict(scope=study.SCOPE, inputs=dict.fromkeys(study.input_keys() | {'scoring'})),
        input_path=access,
    )
    with pytest.raises(ValueError, match='training and clock'):
        study.evaluate(study.task(), context)
    assert all(value == 0 for value in study.task()['limits'].values())


def test_straight_material_requires_exact_saved_clock_bytes():
    from lll import esa_straight_control_material as study

    context = SimpleNamespace(
        manifest=dict(scope=study.SCOPE, inputs=dict.fromkeys(study.input_keys())),
        input_path=lambda name: SimpleNamespace(read_bytes=lambda: b'{}'),
    )
    with pytest.raises(ValueError, match='verified straight-control clock'):
        study.evaluate(study.task(), context)
