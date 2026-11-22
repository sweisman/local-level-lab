"""Independent SciPy optimizer must honor the caller's native accounting."""

import numpy as np
import pytest

from lll.ilvis0_independent_scipy_adapter import fit_candidate


class Bounds:
    active=('x','y')

    def decode(self,point):
        if np.any(abs(np.asarray(point))>1):
            raise ValueError('infeasible')
        return dict(zip(self.active,point,strict=True))


class Counted:
    bounds=Bounds()

    def __init__(self):
        self.calls=0

    def residual_tangent(self,point,model):
        self.calls+=1
        x,y=point
        return (np.array([x-.2,y+.1,x+y-.1]),
                np.array([[1.,0.],[0.,1.],[1.,1.]]),0)


def test_independent_scipy_method_recovers_known_optimum_and_counts_calls():
    problem=Counted()
    fit=fit_candidate(problem,'control',start=np.array([.8,-.8]),
        maximum_evaluations=30,
        physical_step=lambda delta:delta.reshape(1,3))
    assert fit['converged']
    assert fit['normalized_parameters']==pytest.approx([.2,-.1],abs=1e-9)
    assert fit['residual_sum_squares']<1e-18
    assert fit['evaluations']==problem.calls<=30
    assert fit['optimizer_family']=='scipy_trf'


def test_uncounted_problem_is_rejected_before_optimizer():
    class Other(Counted):
        pass
    with pytest.raises(ValueError,match='counted training adapter'):
        fit_candidate(Other(),'control',start=np.zeros(2),
            maximum_evaluations=30,
            physical_step=lambda delta:delta.reshape(1,3))


def test_centered_solver_uses_current_counted_proxy_and_preserves_finite_cap():
    class Counted:
        bounds = Bounds()
        tangent_calls = 0
        value_calls = 0

        def residual_tangent(self, point, model):
            self.tangent_calls += 1
            x, y = point
            return (np.array([102. + .05*(x-.2)**2, 20*(y-.1-.08*(x-.2)**2), .002*(x-.2)]),
                    np.array([[.1*(x-.2), 0.], [-3.2*(x-.2), 20.], [.002, 0.]]), 0)

    problem = Counted()
    fit = fit_candidate(problem, 'control', start=np.array([.8, -.8]),
        maximum_evaluations=8, method='centered_lbfgsb',
        physical_step=lambda d: d.reshape(1,3))
    assert fit['optimizer_family'] == 'centered_lbfgsb'
    assert fit['evaluations'] == problem.tangent_calls <= 8
    assert np.isfinite(fit['normalized_parameters']).all()
    assert not fit['converged']
