# SPDX-License-Identifier: AGPL-3.0-or-later
"""Cheap scope/acceptance checks; the long native matrix is separately frozen."""
import copy
from fractions import Fraction as F

import pytest


def test_recipe_preserves_full_domain_and_training_cutoff():
    from lll.ilvis0_long_staged import recipe, validate_recipe
    value = recipe()
    validate_recipe(value)
    assert value['training_s'] == [2., 10., 30., 180., 290.]
    assert value['stage_sizes'] == [3, 2]
    assert value['future_s'] == 438.
    assert value['lower'] == [-1.] * 27 and value['upper'] == [1.] * 27
    assert value['packets'] == 96000 and value['clock_limit_s'] == 1.


@pytest.mark.parametrize('key,value', [
    ('training_s', [2., 10., 30., 180., 300.]),
    ('future_s', 400.), ('clock_limit_s', 0.),
    ('lower', [-.5] * 27), ('stage_sizes', [5]),
    ('noise_allowance_m', .001), ('width_target_m', [200., 200., 500.]),
])
def test_recipe_rejects_changed_horizon_domain_or_acceptance(key, value):
    from lll.ilvis0_long_staged import recipe, validate_recipe
    altered = copy.deepcopy(recipe()); altered[key] = value
    with pytest.raises(ValueError):
        validate_recipe(altered)


def test_truth_audit_uses_exact_inequalities_and_cannot_turn_width_failure_into_pass():
    from lll.ilvis0_long_staged import audit_truth
    region = dict(lower=[-1., -1.], upper=[1., 1.],
                  inequality_design=[[1., 0.], [-1., 0.]], inequality_upper=[.5, .5])
    future = dict(lower=[-100., -1., -1.], upper=[100., 1., 1.])
    audit = audit_truth([region], [.25, 0.], future, [F(0)] * 3, [20., 20., 50.])
    assert audit['known_truth_retained'] and audit['future_truth_contained']
    assert not audit['useful'] and audit['width_m'] == [200., 2., 2.]
    with pytest.raises(ValueError, match='training'):
        audit_truth([region], [.75, 0.], future, [F(0)] * 3, [20., 20., 50.])
    with pytest.raises(ValueError, match='future'):
        audit_truth([region], [.25, 0.], future, [F(101), F(0), F(0)], [20., 20., 50.])


def test_truth_audit_checks_all_stages_and_outward_width():
    from lll.ilvis0_long_staged import audit_truth
    a = dict(lower=[-1.], upper=[1.], inequality_design=[[1.]], inequality_upper=[.5])
    b = dict(lower=[-1.], upper=[1.], inequality_design=[[1.]], inequality_upper=[.1])
    future = dict(lower=[-.1, -1., -2.], upper=[.2, 1., 2.])
    result = audit_truth([a], [0.], future, [F(0)] * 3, [20., 20., 50.])
    assert F(result['width_m'][0]) >= F(.2) - F(-.1)
    with pytest.raises(ValueError, match='training'):
        audit_truth([a, b], [.25], future, [F(0)] * 3, [20., 20., 50.])


def test_frozen_loader_can_construct_long_runtime_without_package_context(tmp_path):
    import importlib.util
    from pathlib import Path
    from types import SimpleNamespace
    path = Path(__file__).parents[1] / 'lll/ilvis0_long_staged.py'
    spec = importlib.util.spec_from_file_location('_standalone_long', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    context = SimpleNamespace(root=tmp_path, manifest={}, save=lambda *args: None)
    runtime = module.Runtime(context, {'limits': module.limits()})
    assert runtime.native_calls == runtime.bounds == 0


def test_no_future_measurement_is_an_input_to_staged_prediction():
    import inspect
    from lll.ilvis0_staged_native import predict
    assert 'future_observations' not in inspect.signature(predict).parameters
    assert 'future_time' in inspect.signature(predict).parameters
