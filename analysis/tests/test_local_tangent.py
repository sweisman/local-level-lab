"""Exact local-information controls for saved whitened Jacobians."""

import numpy as np
import pytest


def test_conditional_column_norm_removes_other_nuisance_directions():
    from lll.local_tangent import conditional_column_norm
    matrix=np.array([[3.,0.,3.],[0.,4.,0.],[0.,0.,0.]],float)
    assert conditional_column_norm(matrix,0)==pytest.approx(0.,abs=1e-12)
    assert conditional_column_norm(matrix,1)==pytest.approx(4.)
    assert conditional_column_norm(matrix,2)==pytest.approx(0.,abs=1e-12)


def test_conditional_column_norm_keeps_independent_sensitivity():
    from lll.local_tangent import conditional_column_norm
    matrix=np.array([[3.,0.],[0.,4.],[0.,0.]],float)
    assert conditional_column_norm(matrix,0)==pytest.approx(3.)
    assert conditional_column_norm(matrix,1)==pytest.approx(4.)
