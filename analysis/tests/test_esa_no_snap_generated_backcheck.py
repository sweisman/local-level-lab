# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_no_snap_generated_backcheck import standardized_maximum


def test_standardized_maximum_subtracts_the_earlier_only_correction():
    future = [[9., 2., 3.], [3., 1., -10.]]
    forecast = dict(center_m=[[-7., -2., -3.], [-3., -1., 6.]],
                    sigma_m=[[2., 2., 2.], [1., 1., .5]],
                    later_receiver_positions_used=False)
    assert standardized_maximum(forecast, np.array(future)) == 8.
