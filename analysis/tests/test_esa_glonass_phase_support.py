# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.esa_glonass_phase_support import C, frequencies, phase_change


def test_glonass_frequencies_and_motion_survive_clock_change():
    assert frequencies(4) == (1_604_250_000., 1_247_750_000.)
    bands = frequencies(-5)
    first = dict(code_m=22e6, phase=(1e7, 2e7), lli=(0, 0),
                 doppler=tuple(-85. * f / C for f in bands))
    elapsed = .4990012
    travel = 85. * elapsed
    later = first | {'phase': tuple(v + f * (.001 + travel / C)
                                  for v, f in zip(first['phase'], bands, strict=True))}
    result, reason = phase_change(first, later, -5, elapsed=elapsed, jump=.001)
    assert reason is None
    assert result['range_difference_m'] == pytest.approx(travel, abs=1e-8)
    slip = later | {'phase': (later['phase'][0], later['phase'][1] + 1)}
    assert phase_change(first, slip, -5, elapsed=elapsed, jump=.001)[1] == 'band2_doppler'
