# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.esa_x_bias_position_replay import endpoint_proposal


def test_free_columns_compensate_for_fixed_endpoint_within_box():
    point = np.array([.2,.1,-.2])
    residual = np.array([0.,.05,0.])
    jacobian = np.array([[1.,1.,0.],[0.,0.,1.],[0.,0.,0.]])
    result = endpoint_proposal(point,residual,jacobian,0)
    assert result['proposed'] == pytest.approx([1.,-.7,-.25])
    assert result['affine_loss_increase'] == pytest.approx(-.0025)
    assert result['settled']
