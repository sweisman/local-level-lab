# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def profile():
    from lll import ilvis0_z_profile
    return ilvis0_z_profile


class Bounds:
    active = ('gyro_gain_z', 'position_x', 'gyro_bias_z', 'velocity_x')
    limits = dict(gyro_gain_z=.02, position_x=100., gyro_bias_z=1., velocity_x=20.)
    def decode(self, point):
        point = np.asarray(point)
        if point.shape != (4,) or not np.all(np.isfinite(point)) or np.any(abs(point)>1):
            raise ValueError('invalid full coordinates')
        return {n: float(u*self.limits[n]) for n, u in zip(self.active, point)}


class Problem:
    bounds = Bounds()
    def residual_tangent(self, point, model):
        jac = np.array([[2., 1., 3., 0.], [0., 0., 1., 2.], [1., 0., 0., 0.]])
        return jac@point-np.array([.4, -.3, .2]), jac, 0


@pytest.mark.parametrize('gain,bias', [(-1., -1.), (0., 0.), (1., 1.), (-1., 1.)])
def test_fixed_coordinates_survive_expansion_and_physical_decoding(gain, bias):
    p = profile().FixedProblem(Problem(), {'gyro_gain_z': gain, 'gyro_bias_z': bias})
    point = np.array([.3, -.4])
    np.testing.assert_array_equal(p.expand(point), [gain, .3, bias, -.4])
    decoded = p.bounds.decode(point)
    assert decoded['gyro_gain_z'] == pytest.approx(.02*gain)
    assert decoded['gyro_bias_z'] == bias
    assert p.bounds.active == ('position_x', 'velocity_x')
    r, j, _ = p.residual_tangent(point, 'test')
    expected, full, _ = Problem().residual_tangent(p.expand(point), 'test')
    np.testing.assert_array_equal(r, expected)
    np.testing.assert_array_equal(j, full[:, [1, 3]])


@pytest.mark.parametrize('fixed', [{}, {'missing': 0.}, {'gyro_gain_z': 1.1}, {'gyro_bias_z': np.nan}])
def test_invalid_fixed_coordinates_rejected(fixed):
    with pytest.raises(ValueError): profile().FixedProblem(Problem(), fixed)


def test_diagnostics_use_free_feasible_gradient_and_no_new_pass():
    p = profile().FixedProblem(Problem(), {'gyro_gain_z': 1., 'gyro_bias_z': 1.})
    point = np.array([-1., 0.])
    r, j, _ = p.residual_tangent(point, 'test')
    out = p.diagnostics(point, 'test')
    np.testing.assert_allclose(out['gradient'], j.T@r)
    assert out['projected_gradient'][0] == 0
    assert out['free_coordinate_order'] == list(p.bounds.active)
    assert len(out['full_gradient']) == 4
    vt = np.array(out['right_singular_vectors'])
    np.testing.assert_allclose(vt@vt.T, np.eye(2), atol=1e-12)
    with pytest.raises(ValueError, match='final tangent'):
        p.diagnostics(np.zeros(2), 'test')


def test_frozen_solver_recovers_known_free_optimum_without_moving_fixed_axes():
    from lll.ilvis0_shape import fit_shape_candidate
    p = profile().FixedProblem(Problem(), {'gyro_gain_z': .2, 'gyro_bias_z': 0.})
    result = fit_shape_candidate(p, 'test', maximum_evaluations=30)
    assert result['converged']
    assert result['parameters']['gyro_gain_z'] == .004
    assert result['parameters']['gyro_bias_z'] == 0
    np.testing.assert_allclose(result['normalized_parameters'], [0., -.15], atol=1e-8)
    assert result['residual_sum_squares'] < 1e-20
    diagnostic = p.diagnostics(result['normalized_parameters'], 'test')
    assert diagnostic['saved_stationarity'] == pytest.approx(result['exact_projected_gradient_relative'])
