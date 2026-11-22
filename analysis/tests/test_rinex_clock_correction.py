# SPDX-License-Identifier: AGPL-3.0-or-later

from copy import deepcopy

import numpy as np
import pytest

from lll.esa_carrier_phase_support import C, L1_WAVELENGTH, L2_WAVELENGTH
from lll.rinex_clock_correction import correct_clock


def test_clock_correction_preserves_transmit_time_when_epoch_is_retimed():
    record = dict(gps_week_seconds=406350., receiver_clock_offset_s=-.00049,
                  satellites=[dict(signals=[dict(pseudorange_m=2.13e7), dict(pseudorange_m=None)])])
    initial = deepcopy(record)
    phases = np.array([[1e8, 8e7]])
    changed, adjusted = correct_clock(record, phases, retime=True)
    code = changed['satellites'][0]['signals'][0]['pseudorange_m']
    assert record == initial
    assert changed['gps_week_seconds']-code/C == pytest.approx(406350.-2.13e7/C, abs=1e-10, rel=0)
    np.testing.assert_allclose((adjusted-phases)*[L1_WAVELENGTH, L2_WAVELENGTH], -C*record['receiver_clock_offset_s'])
    legacy, _ = correct_clock(record, phases, retime=False)
    assert legacy['gps_week_seconds'] == record['gps_week_seconds']
    assert legacy['gps_week_seconds']-code/C-(406350.-2.13e7/C) == pytest.approx(-.00049, abs=1e-10, rel=0)
