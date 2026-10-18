# SPDX-License-Identifier: AGPL-3.0-or-later
"""Exact linear controls for the finite precision diagnostic, without archive data."""
import numpy as np
import pytest

from lll import ilvis0_precision_probes as precision
from test_ilvis0_shared_leg_probes import LinearProblem


def test_fourteen_evaluations_compare_the_same_feasible_points():
    problem=LinearProblem();point=np.array([.2,-.3,.4]);history=[]
    def call(function,*args):
        history.append((problem.tangent_kernel,args[0].copy()))
        return function(*args)
    result=precision.inspect_endpoint(problem,point,'control',-point,'ordinary','extended',call)
    assert len(history)==14
    assert len(result['fixed_correction_probes'])==10
    for index in range(2,len(history)-2,2):
        np.testing.assert_array_equal(history[index][1],history[index+1][1])
        assert history[index][0]=='ordinary'
        assert history[index+1][0]=='extended'
    assert max(result['central_coordinate_difference']['maximum_neu_m'])==0
    for row in result['fixed_correction_probes']:
        assert max(row['linear_prediction_error']['maximum_neu_m'])<1e-8
    assert result['extended_correction_probes'][1]['cost']==pytest.approx(0.,abs=1e-25)
    assert result['qualifies_original_fit'] is False


def test_infeasible_frozen_direction_is_rejected_before_native_calls():
    calls=[]
    with pytest.raises(ValueError,match='feasible'):
        precision.inspect_endpoint(LinearProblem(),np.array([.2,-.3,.4]),'control',np.ones(3)*2,
            'ordinary','extended',lambda fn,*args:calls.append(args))
    assert calls==[]
