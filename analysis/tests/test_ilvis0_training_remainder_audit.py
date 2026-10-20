# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from lll.ilvis0_training_remainder_audit import scaled_design


def test_every_physical_and_common_column_is_scaled_once():
    jac=[[float(j+1) for j in range(27)] for _ in range(3)]
    report=dict(previous_coefficients=[[2.]*6]*3,acceleration_coefficients=[[3.]*9]*3,
        transform_coefficients=[[4.]*9]*3)
    result=scaled_design(jac,report,[2.,3.,1.])
    assert [len(r) for r in result]==[51]*3
    assert result[0]==[2.*(j+1) for j in range(27)]+[4.]*6+[6.]*9+[8.]*9
    assert result[1][27:]==[6.]*6+[9.]*9+[12.]*9
    assert result[2][27:]==[2.]*6+[3.]*9+[4.]*9


@pytest.mark.parametrize('bad',[0.,float('inf'),-1.])
def test_invalid_coordinate_scale_is_rejected(bad):
    report=dict(previous_coefficients=[[0.]*6]*3,acceleration_coefficients=[[0.]*9]*3,
        transform_coefficients=[[0.]*9]*3)
    with pytest.raises(ValueError):scaled_design([[0.]*27]*3,report,[1.,bad,1.])
