# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_ground_x_bias import spread


def test_ground_nominal_and_endpoint_wrapper_pass_lists():
    actual = spread([np.array([[.1,0.,9.8]]*3)], [.1,0.,0.], [0.,0.,0.])
    assert actual['stops'][0]['mean_mps2'] == 9.8
    assert actual['stops'][0]['half_spread_mps2'] == 0.
