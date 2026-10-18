# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def candidate():
    from lll import ilvis0_boundary_followup
    return ilvis0_boundary_followup


class Surface:
    def __init__(self, kind='minimum'):
        self.kind = kind
        self.calls = []
        self.knots = [-1., 0., 1e-5, 1.]

    def evaluate(self, u, *, fresh=False):
        assert fresh
        self.calls.append(np.array(u).copy())
        x, t = u
        if self.kind == 'monotone':
            value, derivative = -.001*t, -.001
        else:
            value = .001*abs(t-1e-5)
            derivative = -.001 if t <= 1e-5 else .001
        target = .7 if self.kind == 'unfinished_nuisance' else 0.
        return (np.array([1.+value, .005*(x-target), 40.]),
                np.array([[0., derivative], [.005, 0.], [0., 0.]]), 0)

    def geometry(self, point):
        return dict(point=point, knots=self.knots, side_geometry_supported=True)


def physical(delta):
    return np.column_stack((np.asarray(delta)*2, np.zeros((len(delta), 2))))


def run(surface, **kwargs):
    return candidate().check([0., 0.], surface.evaluate, physical,
                             time_index=1, geometry_at=surface.geometry, **kwargs)


def test_neighbor_is_checked_before_known_cusp_can_pass():
    surface = Surface()
    result = run(surface)
    assert result['passed']
    assert len(result['checks']) == 2
    assert result['checks'][0]['passed'] is False
    assert result['checks'][1]['passed'] is True
    assert result['normalized_parameters'][1] == 1e-5
    assert result['evaluations'] == len(surface.calls) <= 30
    assert not result['scientific_eligible']


def test_local_monotone_surface_cannot_pass_at_an_unchecked_neighbor():
    surface = Surface('monotone')
    surface.knots = [-1., 0., 1e-5, 2e-5, 3e-5, 4e-5, 1.]
    result = run(surface)
    assert not result['passed']
    assert result['reason'] == 'boundary_check_limit'
    assert len(result['checks']) == 3
    assert len(surface.calls) <= 30


def test_nuisance_movement_cannot_be_excused_by_neighbor_flag():
    result = run(Surface('unfinished_nuisance'))
    assert not result['passed']
    assert len(result['checks']) == 1


def test_unsupported_geometry_abstains_before_native_calls():
    surface = Surface()
    surface.geometry = lambda point: dict(point=point, knots=surface.knots,
                                          side_geometry_supported=False)
    result = run(surface)
    assert not result['passed'] and result['evaluations'] == 0
    assert not surface.calls


def test_relocation_must_not_silently_snap_to_another_knot():
    surface = Surface()
    surface.geometry = lambda point: dict(point=1e-5, knots=surface.knots,
                                          side_geometry_supported=True)
    result = run(surface)
    assert not result['passed'] and not surface.calls


@pytest.mark.parametrize('allowance', [0, 2, 29, 31])
def test_finite_scope_is_not_expandable(allowance):
    surface = Surface()
    with pytest.raises(ValueError):
        run(surface, maximum_evaluations=allowance)
    assert not surface.calls


def test_unchanged_limits_are_explicit():
    from lll import ilvis0_boundary_stop
    assert candidate().POLICY['stopping'] == ilvis0_boundary_stop.POLICY


def test_zero_evaluation_reporting_preserves_an_abstention():
    result = dict(passed=False, evaluations=0, reason='no_transition_in_window')
    assert candidate().selected_evaluation([0., 0.], result, {}) is None


def test_missing_evaluation_cannot_hide_a_claimed_pass():
    with pytest.raises(ValueError):
        candidate().selected_evaluation([0., 0.], dict(passed=True, evaluations=0), {})


def test_evaluated_result_requires_its_actual_selected_point():
    with pytest.raises(ValueError):
        candidate().selected_evaluation([0., 0.], dict(passed=False, evaluations=2), {})


def test_center_movement_uses_the_new_fresh_value_not_an_earlier_cached_probe():
    surface = Surface()
    original = surface.evaluate
    center_calls = 0

    def evaluate(u, *, fresh=False):
        nonlocal center_calls
        r, j, b = original(u, fresh=fresh)
        if u[1] == 1e-5:
            center_calls += 1
        # The initial check touches this neighbor once. Its subsequent two
        # center evaluations agree with each other but changed since that probe.
        if center_calls >= 2:
            r[-1] += .02
        return r, j, b

    surface.evaluate = evaluate
    result = run(surface)
    assert not result['passed']
    assert result['reason'] == 'cumulative_relocation_not_stable'


def test_original_cusp_needs_no_neighbor_continuation():
    surface = Surface()
    result = candidate().check([0., 1e-5], surface.evaluate, physical,
                              time_index=1, geometry_at=surface.geometry)
    assert result['passed'] and len(result['checks']) == 1


def test_valid_native_result_is_preserved_without_fabricating_an_artifact():
    value = (np.array([1.]), np.array([[2.]]), 0)
    cache = {(0.,): value}
    assert candidate().selected_evaluation([0.], dict(passed=False, evaluations=2), cache) is value
