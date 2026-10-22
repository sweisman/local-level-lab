# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest


def test_endpoint_average_is_exact_for_an_independent_quadratic_example():
    from lll.ilvis0_endpoint_curvature import compare,GROUPS
    point=np.zeros(27);point[0]=.5;point[15]=.25
    j0=np.zeros((3,3,27));j0[:,:,0]=2.
    jp=j0.copy();jp[:,:,0]+=4*point[0];jp[:,:,15]+=8*point[15]
    actual=np.full((3,3),2*point[0]+2*point[0]**2+4*point[15]**2)
    result=compare(j0,jp,point,actual)
    assert result['maximum_linear_error_m']==.75
    assert result['maximum_endpoint_error_m']==0.
    assert result['future_group_curvature_m']['attitude']==[.5]*3
    assert result['future_group_curvature_m']['gyro_gain']==[.25]*3
    assert sorted(i for a,b in GROUPS.values() for i in range(a,b))==list(range(27))


def test_endpoint_average_does_not_claim_exactness_for_cubic_motion():
    from lll.ilvis0_endpoint_curvature import compare
    p=np.zeros(27);p[0]=1.;j0=np.zeros((2,3,27));jp=j0.copy();jp[:,:,0]=3.
    result=compare(j0,jp,p,np.ones((2,3)))
    assert result['maximum_endpoint_error_m']==.5 and not result['numerical_coverage_qualified']


def test_missing_derivative_column_is_rejected():
    from lll.ilvis0_endpoint_curvature import compare
    with pytest.raises(ValueError):compare(np.zeros((2,3,26)),np.zeros((2,3,26)),np.zeros(27),np.zeros((2,3)))


def test_endpoint_report_rejects_a_coverage_claim():
    from ilvis0_endpoint_curvature_worker import render
    tasks=[dict(identity=str(int(p)),payload=dict(profile=p)) for p in (False,True)]
    text=render(dict(tasks=tasks),dict(completed=0,total=2),{})
    assert '0/2' in text and 'not a curvature bound' in text
    with pytest.raises(ValueError):render(dict(tasks=tasks),dict(completed=1,total=2),
        {'0':dict(passed=True,numerical_coverage_qualified=True)})
