# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def screen():
    from lll import ilvis0_solver_screen
    return ilvis0_solver_screen


@pytest.mark.parametrize('name',['mixed_interior','mixed_boundary'])
def test_mixed_controls_have_independently_known_optima(name):
    p,optimum=screen().mixed_problem(name)
    residual,jac,_=p.residual_tangent(optimum,'control')
    assert residual@residual==pytest.approx(1.,abs=1e-8)
    assert max(np.linalg.svd(jac,compute_uv=False))/min(np.linalg.svd(jac,compute_uv=False))==pytest.approx(5e7,rel=1e-6)
    assert len(optimum)==27
    assert np.all(abs(optimum)<=1.)


def test_screen_is_finite_reproducible_and_preserves_unresolved_cases():
    out=screen().run()
    assert out['observed_fit_starts']==out['native_predictions']==0
    assert len(out['results'])==72
    assert len({r['identity'] for r in out['results']})==72
    assert all(0<r['evaluations']<=200 for r in out['results'])
    assert all(isinstance(r['passed'],bool) for r in out['results'])
    assert out['scientific_decision']=='abstain'
    assert out['qualifies_archival_solver'] is False
    second=screen().run()
    assert out==second
