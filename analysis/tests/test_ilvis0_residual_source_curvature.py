# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def example(cubic_residual=False,shift=False):
    maps=np.zeros((2,3,51));maps[:,:,27]=1.;p=np.zeros(27);p[0]=1.
    source=np.zeros(24);source[0]=2. if shift else 1.;center=np.zeros(24);center[0]=float(shift)
    d0=np.zeros((24,27));dp=d0.copy();dp[0,0]=3.
    jp=np.zeros((2,3,27));jp[:,:,0]=6. if cubic_residual else 5.
    return maps,jp,p,source,center,dp,d0,np.full((2,3),2.)


def test_cubic_source_is_retained_while_quadratic_remaining_error_is_exact():
    from lll.ilvis0_residual_source_curvature import compare
    row=compare(*example())
    assert row['maximum_anchored_error_m']==1. and row['maximum_corrected_error_m']==0.
    assert row['physical_parameter_count']==27 and row['source_parameter_count']==24


def test_nonzero_source_center_is_explicitly_reanchored():
    from lll.ilvis0_residual_source_curvature import compare
    row=compare(*example(shift=True))
    assert row['source_error_m']==[[0.]*3]*2
    assert row['maximum_anchored_error_m']==1. and row['maximum_corrected_error_m']==0.


def test_higher_order_remaining_error_is_not_claimed_exact_or_bounded():
    from lll.ilvis0_residual_source_curvature import compare
    row=compare(*example(cubic_residual=True))
    assert row['maximum_corrected_error_m']==.5 and not row['numerical_coverage_qualified']


def test_missing_source_derivative_column_is_rejected():
    from lll.ilvis0_residual_source_curvature import compare
    args=list(example());args[5]=np.zeros((24,26))
    with pytest.raises(ValueError):compare(*args)


def test_report_rejects_a_curvature_bound_claim():
    from ilvis0_residual_source_curvature_worker import render
    tasks=[dict(identity=str(int(p)),payload=dict(profile=p)) for p in (False,True)]
    text=render(dict(tasks=tasks),dict(completed=0,total=2),{})
    assert '0/2' in text and 'not a certified bound' in text
    with pytest.raises(ValueError):render(dict(tasks=tasks),dict(completed=1,total=2),
        {'0':dict(passed=True,numerical_coverage_qualified=True)})
