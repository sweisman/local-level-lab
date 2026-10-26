# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent known-answer controls for saved-point diagnostic calculations."""
import importlib

import numpy as np
import pytest


FAMILIES = ('interior', 'lower', 'upper', 'near_dependent', 'null', 'nonlinear')


def fixture(family, width):
    # Analytical reference points and derivatives; no optimizer generates truth.
    point = np.zeros(width)
    matrix = np.eye(width)
    target = np.zeros(width)
    if family in ('lower', 'upper'):
        point[:] = -1 if family == 'lower' else 1
        target[:] = 2 * point
    if family == 'near_dependent':
        matrix[-1, -1] = 1e-8
        matrix[:, -1] += matrix[:, -2]
    if family == 'null':
        matrix[:, -1] = 0
    def evaluate(u, fresh=False):
        if family == 'nonlinear':
            return u + .1*u**2, np.diag(1 + .2*u), 0
        return matrix @ u - target, matrix.copy(), 0
    return point, evaluate


def run(point, evaluate, **overrides):
    module = importlib.import_module('lll.stopping_consistency')
    from lll.ilvis0_solver_position import verify_stability
    width=26 if point is None else len(point)
    settings = dict(bounds=(-np.ones(width), np.ones(width)),
        frozen_probe=lambda u,r,j,e: verify_stability(u,r,j,e,lambda d: np.tile(d[:,None],(1,3))),
        reserve=lambda **k: None, check_continue=lambda: None)
    settings.update(overrides)
    return module.probe(evaluate, point, **settings)


@pytest.mark.parametrize('width', [26, 27])
@pytest.mark.parametrize('family', FAMILIES)
def test_known_answer_derivatives_at_reference_optima(family, width):
    # Losing a column, using an infeasible centered stencil, or reversing a sign
    # breaks the independent identity/polynomial reference below.
    point, evaluate = fixture(family, width)
    charges=[]
    report=run(point,evaluate,reserve=lambda **k: charges.append(k))
    assert report['repeatability']['exact']
    assert report['columns']==width
    assert report['evaluations']==len(charges)<=170
    assert all(v=={'evaluations':1} for v in charges)
    for row in report['derivatives']:
        assert len(row['steps'])==3
        final=row['steps'][-1]
        assert final['error_norm']<=1e-8+1e-6*max(final['analytic_norm'],final['difference_norm'])
        if family=='lower': assert all(s['stencil']=='forward' for s in row['steps'])
        if family=='upper': assert all(s['stencil']=='backward' for s in row['steps'])
    assert report['nonlinear_fit_starts']==0
    assert report['stopping_probe']['passed']


@pytest.mark.parametrize('case', ['missing_point','out_of_box','missing_column',
    'invalid_budget','overspend','invalid_step','nonfinite','infeasible_stencil',
    'repeatability'])
def test_probe_guards(case):
    point, evaluate=fixture('interior',26)
    options={}
    if case=='missing_point': point=None
    if case=='out_of_box': point[0]=1.01
    if case=='invalid_budget': options['maximum_evaluations']=True
    if case=='overspend': options['maximum_evaluations']=3
    if case=='invalid_step': options['steps']=(0.,1e-4,1e-5)
    if case=='infeasible_stencil': options['bounds']=(np.zeros(26), np.full(26,1e-6))
    if case=='missing_column': evaluate=lambda u,fresh=False:(u,np.eye(26)[:,:-1],0)
    if case=='nonfinite': evaluate=lambda u,fresh=False:(u*np.nan,np.eye(26),0)
    if case=='repeatability':
        count=[0]
        def changed(u,fresh=False):
            count[0]+=1
            return u+count[0]*1e-9,np.eye(26),0
        report=run(point,changed)
        assert not report['repeatability']['exact']
        return
    with pytest.raises((ValueError,RuntimeError)):
        run(point,evaluate,**options)
