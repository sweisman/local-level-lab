# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent analytical minima; do not change the original stopping checker."""
import json
import os
from pathlib import Path

import numpy as np
import pytest


@pytest.mark.parametrize('kind,center,expected_pass',[
    ('smooth_minimum',0.,True),('kink_minimum',0.,False),
    ('kink_minimum',.25,False),('smooth_nonminimum',0.,False)])
def test_original_stability_check_on_independently_known_curves(kind,center,expected_pass):
    from lll.ilvis0_solver_position import verify_stability
    b=.00005
    def residual(u):
        x=float(u[0])
        if kind=='smooth_minimum':return np.array([15.,b*(x-center)])
        if kind=='kink_minimum':return np.array([15.+b*abs(x-center)])
        return np.array([15.+b*x])
    def derivative(u):
        if kind=='smooth_minimum':return np.array([[0.],[b]])
        sign=-1. if kind=='kink_minimum' and u[0]<center else 1.
        return np.array([[b*sign]])
    optimum=-1. if kind=='smooth_nonminimum' else center
    # These inequalities follow directly from a square or |u-center|, independently
    # of the solver. The nonminimum control is evaluated away from its true minimum.
    minimum=float(residual([optimum])@residual([optimum]))
    for x in (-1.,-.2,0.,.25,.8,1.):
        assert float(residual([x])@residual([x]))>=minimum
    h=.125
    left=(residual([center])-residual([center-h]))/h
    right=(residual([center+h])-residual([center]))/h
    expected_left=-b if kind=='kink_minimum' else b
    assert left[-1]==pytest.approx(expected_left,abs=1e-12)
    assert right[-1]==pytest.approx(b,abs=1e-12)
    assert derivative([center])[-1,0]==b
    calls=[]
    def fresh(u,*,fresh=False):
        assert fresh is True
        calls.append(1)
        return residual(u),derivative(u),0
    def physical(delta):
        return np.column_stack((delta,np.zeros_like(delta),np.zeros_like(delta)))
    point=np.array([center]);r=residual(point)
    result=verify_stability(point,r,derivative(point),fresh,physical)
    assert len(calls)==1
    assert result['passed'] is expected_pass
    if kind=='kink_minimum':
        assert result['actual_cost_change']>1e-8
        assert result['fresh_stationarity']<1e-4
        assert max(result['position_max_abs_neu_m'])<.001
    output=os.environ.get('LLL_KINK_CONTROL_OUTPUT')
    if output:
        directory=Path(output);directory.mkdir(parents=True,exist_ok=True)
        name=kind+'-'+str(center)+'.json'
        with (directory/name).open('x') as stream:
            json.dump(dict(kind=kind,center=center,known_optimum=optimum,
                evaluated_at_known_optimum=kind!='smooth_nonminimum',check=result,
                analytical_fresh_evaluations=1,linear_solves=1,native_calls=0,
                nonlinear_fit_starts=0),stream,sort_keys=True,indent=2)
