# SPDX-License-Identifier: AGPL-3.0-or-later
"""The candidate verifier is checked through the unchanged bounded solver."""

import numpy as np
import pytest

from lll.ilvis0_boundary_controls import problem_for, starts
from lll.ilvis0_solver_trust_v2 import fit_candidate
from lll.one_sided_stopping import verify


@pytest.mark.parametrize('name', ('interior','boundary','redundant',
                                  'curved_boundary','nonlinear27'))
@pytest.mark.parametrize('start_index', (0,1))
def test_one_sided_gate_recovers_known_native_style_objective(name,start_index):
    problem,optimum,expected,_ = problem_for(name)
    meters = lambda delta:np.column_stack((delta,np.zeros((len(delta),2))))
    fit = fit_candidate(problem,'control',start=starts(len(optimum))[start_index],
        maximum_evaluations=100,physical_step=meters,
        stability_verifier=verify,verification_evaluations=9)
    assert fit['converged']
    assert fit['residual_sum_squares'] == pytest.approx(expected,abs=1e-7,rel=0)
    assert fit['stability_probe']['version'] == 'one-sided-observable-stability-v1'
    assert fit['scientific_decision'] == 'abstain'
    assert problem.calls == fit['evaluations'] <= 100
