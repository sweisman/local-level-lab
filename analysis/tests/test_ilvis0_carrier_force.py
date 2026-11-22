# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np
import pytest

from lll.gnss_position import ecef
from lll.ilvis0_carrier_force import centered_path


def test_carrier_path_keeps_center_and_accumulates_relative_ecef_motion():
    tags = [1000, 2000, 3000, 4000]
    center = [.2, -.6, 3500.]
    steps = np.array([[100., 130., -5.], [105., 131., -1.], [115., 132., 2.]])
    pairs = {a: dict(last_tag=b, status='converged', displacement_ecef_m=s)
             for a, b, s in zip(tags[:-1], tags[1:], steps, strict=True)}
    coordinates = centered_path(tags, 3000, center, pairs)
    np.testing.assert_array_equal(coordinates[2], center)
    np.testing.assert_allclose(np.diff([ecef(*row) for row in coordinates], axis=0),
                               steps, atol=5e-9, rtol=0.)
    pairs[2000]['status'] = 'abstain'
    with pytest.raises(ValueError, match='complete adjacent'):
        centered_path(tags, 3000, center, pairs)
