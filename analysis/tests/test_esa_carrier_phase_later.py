# SPDX-License-Identifier: AGPL-3.0-or-later
import numpy as np

from lll.esa_carrier_phase_later import recover_metre_change


def test_metre_adapter_recovers_displacement_with_free_clock_change():
    # Use a symmetric, stationary constellation and independent Euclidean range changes.
    anchor = np.array([0., 0., 6_374_000.])
    displacement = np.array([32., -21., 4.])
    satellite = 21e6 * np.array([[1, 0, 1], [-1, 0, 1], [0, 1, 1],
                                [0, -1, 1], [0, 0, 1], [1, 1, 0]], float)
    measured = (np.linalg.norm(satellite - anchor - displacement, axis=1)
                - np.linalg.norm(satellite - anchor, axis=1) + 2.5)
    zeros = np.zeros(len(satellite))
    answer = recover_metre_change(anchor, satellite, satellite, zeros, zeros, zeros, zeros, measured)
    assert answer['status'] == 'converged'
    # The production adapter includes Earth-rotation range correction.
    assert np.linalg.norm(np.asarray(answer['displacement_ecef_m']) - displacement) < .001
    assert abs(answer['receiver_clock_change_m'] - 2.5) < .001
