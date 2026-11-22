# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_carrier_phase_support import L1_WAVELENGTH, L2_WAVELENGTH, pair_observation


def phase_at(displacement, *, flags=(0, 0), l2='2W'):
    return dict(code_m=22e6, l1=(1e6 + displacement / L1_WAVELENGTH, flags[0]),
        doppler=-100 / L1_WAVELENGTH,
        l2={l2: (2e6 + displacement / L2_WAVELENGTH, flags[1])})


def test_continuous_range_change_survives_both_screens():
    row, rejection = pair_observation(phase_at(0.), phase_at(50.), .5)
    assert rejection is None
    assert row['ionosphere_free_displacement_m'] == pytest.approx(50., abs=1e-8)


def test_loss_of_lock_switching_codes_and_unflagged_cycle_slips():
    first, second = phase_at(0.), phase_at(50.)
    assert pair_observation(first, phase_at(50., flags=(0, 1)), .5)[1] == 'loss_of_lock'
    assert pair_observation(first, phase_at(50., l2='2X'), .5)[1] == 'no_common_l2_code'
    assert pair_observation(first, second | dict(l1=(second['l1'][0] + 1, 0)), .5)[1] == 'l1_doppler'
    assert pair_observation(first, second | dict(l2={'2W': (second['l2']['2W'][0] + 1, 0)}), .5)[1] == 'dual_phase'
