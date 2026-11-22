"""Compare fixed and calibration-aware covariance on identical receiver rows."""
import numpy as np
import pytest


def test_compare_coverage_uses_same_later_receiver_rows_for_both_laws():
    from lll.esa_linear_uncertainty_report import compare_coverage
    receiver=np.tile([.5,.2,100.],(3,1))
    fixed=receiver.copy();fixed[:,2]=99.
    local=fixed.copy()
    fixed_cov=np.tile(np.diag([1e-12,1e-12,.04]),(3,1,1))
    local_cov=np.tile(np.diag([1e-12,1e-12,1.]),(3,1,1))
    result=compare_coverage(fixed,fixed_cov,local,local_cov,receiver)
    assert result['fixed']['axes']['up']['nominal_95_fraction']==0.
    assert result['local']['axes']['up']['nominal_95_fraction']==1.
    assert result['fixed']['epochs']==result['local']['epochs']==3
    with pytest.raises(ValueError,match='aligned'):
        compare_coverage(fixed,fixed_cov,local[:2],local_cov,receiver)
