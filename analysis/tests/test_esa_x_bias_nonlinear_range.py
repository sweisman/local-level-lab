# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_x_bias_nonlinear_range import local_proposal


def test_proposal_cannot_cross_bias_boundary_or_local_radius():
    point = np.array([.225,.3])
    proposal = local_proposal(point,[1.,1.],np.eye(2),[.225,-1.])
    assert proposal['point'][0] == .225
    assert abs(proposal['point'][1]-.25) < 1e-12
    assert proposal['settled']
