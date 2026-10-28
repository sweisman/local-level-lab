# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def meters(delta):return np.c_[delta,delta*0,delta*0]


def test_custom_verifier_is_enforced_and_has_reserved_evaluations():
    from lll.ilvis0_solver_trust_v2 import fit_candidate
    from lll.ilvis0_boundary_controls import problem_for
    problem,_,_,_=problem_for('interior');seen=[]
    def verifier(u,r,j,evaluate,physical):
        for _ in range(4):evaluate(u,fresh=True)
        seen.append(1);return dict(passed=False,reason='deliberate final failure')
    fit=fit_candidate(problem,'control',start=np.zeros(2),maximum_evaluations=40,physical_step=meters,
        stability_verifier=verifier,verification_evaluations=5)
    assert seen==[1] and not fit['converged']
    assert fit['stability_probe']['reason']=='deliberate final failure'
    assert problem.calls==fit['evaluations']<=40


def test_core_linear_reservations_precede_every_actual_solve(monkeypatch):
    from lll import ilvis0_solver_trust_v2 as core
    from lll.ilvis0_boundary_controls import problem_for
    problem,_,_,_=problem_for('nonlinear');charges=[];attempts=[];original=core.lsq_linear
    def solve(*a,**k):
        assert len(charges)==len(attempts)+1
        attempts.append(1);return original(*a,**k)
    monkeypatch.setattr(core,'lsq_linear',solve)
    fit=core.fit_candidate(problem,'control',start=np.zeros(2),maximum_evaluations=40,physical_step=meters,
        stability_verifier=lambda *a:dict(passed=False),reserve_linear=lambda:charges.append(1))
    assert len(charges)==len(attempts)==fit['optimizer_linear_solves'] and charges


@pytest.mark.parametrize('reserve',[True,1,41])
def test_custom_verification_caps_are_validated_before_problem_access(reserve):
    from lll.ilvis0_solver_trust_v2 import fit_candidate
    with pytest.raises(ValueError):
        fit_candidate(None,'control',start=[],maximum_evaluations=40,verification_evaluations=reserve)


def test_near_zero_composition_accepts_explicit_ordinary_provider_without_changing_default():
    from lll.ilvis0_near_zero import fit_candidate
    from lll.ilvis0_solver_trust_v2 import fit_candidate as ordinary
    from lll.ilvis0_boundary_controls import problem_for
    problem,_,_,_=problem_for('interior');seen=[]
    def provider(*a,**k):seen.append(k['maximum_evaluations']);return ordinary(*a,**k)
    fit=fit_candidate(problem,'control',start=np.zeros(2),maximum_evaluations=40,
        physical_step=meters,ordinary_provider=provider)
    assert fit['converged'] and seen==[38]
    assert fit['evaluations']==problem.calls<=40
