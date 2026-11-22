# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known answers qualify a separate candidate without changing archived evidence."""
import importlib
import importlib.util
import pytest

CONTROLS=('interior','boundary','redundant','scaled','nonlinear','gain_offset',
          'curved_boundary','exponential','curved_redundant','nonlinear27')


def candidate():
    name='lll.ilvis0_solver_trust_v2'
    assert importlib.util.find_spec(name) is not None,'separate damped solver is missing'
    return importlib.import_module(name)


def meters(delta):
    import numpy as np
    return np.column_stack((delta,np.zeros((len(delta),2))))


@pytest.mark.parametrize('name',CONTROLS)
@pytest.mark.parametrize('index',range(4))
def test_known_objective_prediction_and_feasible_parameters(name,index):
    solver=candidate()
    import numpy as np
    from lll.ilvis0_boundary_controls import problem_for,starts
    problem,optimum,expected,unique=problem_for(name)
    fit=solver.fit_candidate(problem,'control',start=starts(len(optimum))[index],
                             maximum_evaluations=200,physical_step=meters)
    point=np.array(fit['normalized_parameters'])
    assert fit['converged'] and fit['stability_verified']
    assert fit['residual_sum_squares']==pytest.approx(expected,abs=1e-7,rel=0)
    assert np.linalg.norm(problem.residual(point)-problem.residual(optimum))<=1e-4
    if unique: assert point==pytest.approx(optimum,abs=1e-5)
    assert np.all(abs(point)<=1)
    assert problem.calls==fit['evaluations']<=200
    assert fit['scientific_decision']=='abstain' and not fit['scientific_eligible']


def test_exhausted_nonstationary_fit_cannot_pass():
    solver=candidate()
    from lll.ilvis0_boundary_controls import problem_for
    problem,_,_,_=problem_for('exponential')
    fit=solver.fit_candidate(problem,'control',start=[-.8,-.8],maximum_evaluations=6,physical_step=meters)
    assert not fit['converged']
    assert problem.calls==fit['evaluations']<=6


@pytest.mark.parametrize('truth',[(.15,-.2),(.98,-.98),(1.,-1.)])
@pytest.mark.parametrize('start',[(0.,0.),(-.7,.6)])
def test_independent_raw_increment_motion_controls(kernels,truth,start):
    solver=candidate()
    import numpy as np
    from test_ilvis0_precision_solver import straight_problem
    problem=straight_problem(kernels,truth)
    fit=solver.fit_candidate(problem,'flat_still',start=np.array(start),maximum_evaluations=40)
    assert fit['converged']
    assert fit['normalized_parameters']==pytest.approx(truth,abs=2e-6)
    assert fit['residual_sum_squares']<1e-10
    assert fit['evaluations']<=40


@pytest.fixture(scope='module')
def kernels(tmp_path_factory):
    candidate()
    from lll import ilvis0_precision as precision,ilvis0_exploratory as explore
    directory=tmp_path_factory.mktemp('trust-motion-controls')
    return explore.load_kernel(directory)[0],precision.load_tangent(directory)[0]


def test_damping_cannot_make_a_failed_physical_gate_pass(monkeypatch):
    solver=candidate()
    import numpy as np
    from lll import ilvis0_solver_position as position
    from lll.ilvis0_boundary_controls import problem_for
    original=position.verify_stability
    seen=[]
    def reject(*args):
        value=original(*args);seen.append(value)
        return dict(value,passed=False,reason='controlled physical gate failure')
    monkeypatch.setattr(position,'verify_stability',reject)
    problem,_,_,_=problem_for('interior')
    fit=solver.fit_candidate(problem,'control',start=np.zeros(2),maximum_evaluations=40,physical_step=meters)
    assert seen and not fit['converged'] and not fit['scientific_eligible']


def test_value_trials_preserve_solver_path_and_skip_rejected_tangents():
    import numpy as np

    class Cubic:
        class bounds:
            active = ('x',)

            @staticmethod
            def decode(point):
                return {'x': float(point[0])}

        def __init__(self):
            self.tangent_calls = 0

        @staticmethod
        def residual(point):
            return np.array([point[0]**3 - .1])

        def residual_tangent(self, point, model):
            self.tangent_calls += 1
            return self.residual(point), np.array([[3*point[0]**2]]), 0

    ordinary, screened = Cubic(), Cubic()
    fit = candidate().fit_candidate
    settings = dict(start=[.1], maximum_evaluations=24, physical_step=meters)
    reference = fit(ordinary, 'control', **settings)
    assert any(not row['accepted'] for row in reference['step_history'])
    received = []

    def trial(point, model):
        received.append(point.copy())
        return screened.residual(point), 0

    proposed = fit(screened, 'control', **settings, trial_residual=trial)
    assert received and reference == proposed
    assert screened.tangent_calls < ordinary.tangent_calls == reference['evaluations']
    with pytest.raises(ValueError, match='trial differs from full tangent'):
        fit(Cubic(), 'control', **settings,
            trial_residual=lambda point, model: (.5 * screened.residual(point), 0))
