# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
from assess_covariance_refits import pair_diagnostics


def test_shared_covariance_projection_matches_closed_form_and_nuisance_units():
    J=np.array([[1.,.2,-.3,1.],[.5,1.,.2,2.],[.1,.3,1.,-.5],[1.,1.,1.,.3]])
    C=np.eye(4);C[0,3]=C[3,0]=.4
    result=pair_diagnostics(J,C);d=np.array([1.,0.,0.]);x=J[:,:3]@d;n=J[:,3:]
    inverse=np.linalg.inv(C);after=x-n@np.linalg.solve(n.T@inverse@n,n.T@inverse@x)
    key='sphere_rotating__sphere_still'
    assert result[key]['information']==pytest.approx(after@inverse@after)
    assert result[key]['retained_fraction']==pytest.approx((after@inverse@after)/(x@inverse@x))
    changed=J.copy();changed[:,3]*=1e7
    other=pair_diagnostics(changed,C)
    for k in result:
        assert other[k]['information']==pytest.approx(result[k]['information'])
        assert other[k]['retained_fraction']==pytest.approx(result[k]['retained_fraction'])


def test_fully_absorbed_contrast_has_zero_information():
    J=np.column_stack([np.array([1.,2.,3.]),np.array([3.,1.,2.]),np.array([2.,3.,1.]),np.array([1.,2.,3.])])
    result=pair_diagnostics(J,np.eye(3))
    assert result['sphere_rotating__sphere_still']['information']<1e-25
