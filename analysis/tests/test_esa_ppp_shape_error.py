# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_ppp_shape_error import probe_windows


def test_receiver_probe_retains_incomplete_and_overlapping_windows():
    window_ids = (4, 5, 6)
    times = set(range(150, 839))
    values = {t: np.array([t, 0., 0.]) for t in times}
    values.pop(839 - 1)
    shape = np.zeros((520, 3))
    shape[-1, 0] = .5
    rows = probe_windows(window_ids, values, shape, comparison_bounds=(80., 160.))
    assert rows == [
        dict(window_id=4, status='overlaps_comparison'),
        dict(window_id=5, status='complete', signed_difference=359.5),
        dict(window_id=6, status='incomplete', missing_reports=2),
    ]
