# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent bounded methods must recover known objectives and keep the gate."""

import numpy as np
import pytest

from lll.independent_bounded_solver import solve


class Bounds:
    active = ('x', 'y')

    def decode(self, point):
        if np.any(abs(point) > 1):
            raise ValueError('infeasible point')
        return dict(zip(self.active, point, strict=True))


class KnownProblem:
    bounds = Bounds()

    def residual_tangent(self, point, model):
        assert model == 'control'
        x, y = point
        return (np.array([x-.2, y+.1, x+y-.1]),
                np.array([[1., 0.], [0., 1.], [1., 1.]]), 0)


@pytest.mark.parametrize('method', ('trf', 'dogbox'))
def test_independent_bounded_strategy_recovers_known_optimum(method):
    charged = []
    result = solve(KnownProblem(), 'control', start=np.array([.8, -.8]),
                   method=method, maximum_calls=30,
                   reserve=lambda **work:charged.append(work),
                   physical_step=lambda delta:delta.reshape(1, 3))
    assert result['scipy_success']
    assert result['original_gate_passed']
    assert result['cost'] < 1e-18
    assert result['point'] == pytest.approx([.2, -.1], abs=1e-9)
    assert len(charged) == result['native_calls_actual'] <= 30


def test_independent_strategy_rejects_changed_method_or_allowance():
    with pytest.raises(ValueError, match='declared bounded method'):
        solve(KnownProblem(), 'control', start=[0., 0.], method='lm',
              maximum_calls=30, reserve=lambda **work:None,
              physical_step=lambda delta:delta.reshape(1, 3))
