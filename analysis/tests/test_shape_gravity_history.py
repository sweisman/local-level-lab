# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ilvis0_control_shards import _tasks
from lll.shape_gravity_history import GRIDS, MODELS, declared_case, generated, tasks


def test_history_adapter_accepts_manifest_tasks_and_rejects_changed_scope():
    frozen = _tasks(tasks(), 1)
    for task in frozen:
        assert declared_case(task) == task['payload']
        increased = task['limits']['bound_steps'] + 1
        enlarged = dict(task, limits=dict(task['limits'], bound_steps=increased))
        with pytest.raises(ValueError, match='fixed generated model, grid and limits'):
            declared_case(enlarged)


@pytest.mark.parametrize('period', GRIDS)
def test_outward_reference_rebuilds_the_rejected_zero_center(period):
    import numpy as np
    from lll.ilvis0_coupled_map import restore_static_reference
    from lll.ilvis0_initial_source_bridge_v2 import certify
    from lll.ilvis0_transform_native import make_reference

    config, theta, dv, dt, _ = generated(MODELS[0], period)
    region = dict(center=np.zeros(27), lower=np.full(27, -.1), upper=np.full(27, .1))
    legacy = make_reference(config, theta, dv, dt, **region)
    assert not certify(legacy, region['lower'], region['upper'])['nonlinear_cap_sufficient']
    reference = make_reference(config, theta, dv, dt, outward_initial_force=True, **region)
    proof = certify(reference, region['lower'], region['upper'])
    assert proof['nonlinear_cap_sufficient'] and not proof['nonlinear_cap_expanded']
    assert reference.binding != legacy.binding
    assert reference.parent.binding == legacy.parent.binding
    np.testing.assert_array_equal(reference.acceleration.center, legacy.acceleration.center)
    np.testing.assert_array_equal(reference.acceleration.jacobian, legacy.acceleration.jacobian)
    normalized = reference.normalized_values_at(region['upper'])
    assert np.max(np.abs(normalized)) <= 1.
    restored = restore_static_reference(config, dv[0], dt[0],
                                        expected_report=reference.report(), **region)
    assert restored.binding == reference.binding
