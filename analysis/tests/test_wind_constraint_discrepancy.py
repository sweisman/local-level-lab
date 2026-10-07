# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest
import wind_constraint_discrepancy as discrepancy


def test_existing_allowance_only_adds_auxiliary_model_variance():
    C=np.eye(4);C[0,3]=C[3,0]=.4
    result=discrepancy.add_discrepancy(C,3,'wind_tas')
    assert result[:3]==pytest.approx(C[:3])
    assert result[3,:3]==pytest.approx(C[3,:3])
    assert result[3,3]==pytest.approx(C[3,3]+1.)
    assert np.linalg.eigvalsh(result).min()>0
    assert discrepancy.POLICY['sigma_mps']==2.
    assert discrepancy.add_discrepancy(np.eye(3),3,'wind')==pytest.approx(np.eye(3))


def test_wrong_candidate_or_auxiliary_layout_is_rejected():
    with pytest.raises(ValueError):discrepancy.discrepancy_covariance(4,3,'wind')
    with pytest.raises(ValueError):discrepancy.discrepancy_covariance(5,3,'wind_tas')
