# SPDX-License-Identifier: AGPL-3.0-or-later
import math

import numpy as np
import pytest

from lll import gnss_position as gps
from lll.esa_sounding_carrier import PAIRS, _saved_path, sounding_slant_delay
from lll.gnss_carrier_phase import _atmosphere
from lll.gnss_sounding import vapour_at_dewpoint, zenith_delay


def test_regional_column_preserves_elevation_mask_and_maps_zenith_delay():
    class ConstantWeather:
        def weather_at(self, height):
            assert height == pytest.approx(2000.)
            return 800., 280., 270.

    # At the equator and prime meridian, local up is +X and east is +Y.
    anchor = np.asarray(gps.ecef(0., 0., 2000.))
    satellites = anchor + 2e7 * np.array([[1., 0., 0.], [.5, math.sqrt(.75), 0.], [0., 1., 0.]])
    ion_model = {'alpha': (0.,) * 4, 'beta': (0.,) * 4}
    original_mask, original_ion, _ = _atmosphere(anchor, satellites, 0., ion_model)
    mask, ion, delays = _atmosphere(anchor, satellites, 0., ion_model,
                                    neutral_delay=sounding_slant_delay(ConstantWeather()))
    zenith = zenith_delay(0., 2000., 800., 280., vapour_at_dewpoint(270.))
    np.testing.assert_array_equal(mask, original_mask)
    np.testing.assert_array_equal(ion, original_ion)
    np.testing.assert_allclose(delays, [zenith, 2. * zenith, 0.], rtol=1e-14)


def test_saved_path_audit_preserves_rejected_runner_disposition():
    class Replay:
        rows = {'task': {'charged': {'bound_calls': PAIRS, 'bound_steps': 16 * PAIRS}}}
        result = dict(passed=False, error_type='ValueError',
                      reason='one explicit software result and continued scientific abstention required')

        def envelope(self, identity):
            return {'result': self.result}

        def artifact(self, identity, name):
            return {'positions': [{}] + [{'range_difference_rms_m': .01}] * PAIRS, 'failure': None}

    replay = Replay()
    status, path = _saved_path(replay, 'task')
    assert status['runner_passed'] is False
    assert status['path_complete'] is True
    assert len(path) == PAIRS + 1
    replay.result['reason'] = 'some other failure'
    status, path = _saved_path(replay, 'task')
    assert status['path_complete'] is False and path is None
