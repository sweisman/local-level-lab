import numpy as np
import pytest

from lll.esa_error_shape_transfer import compare
from lll.esa_repeat_turns import subtract, supported_windows


def test_exclusions_split_original_inclusive_indices_without_joins():
    assert subtract([(0, 10), (20, 30)], [(0, 2), (5, 7), (9, 22), (25, 25)]) == [
        (3, 4), (8, 8), (23, 24), (26, 30)]


def test_turn_forecast_requires_full_support_inside_one_retained_run():
    # Only the middle two candidates have complete 400/120-second supports.
    possible = supported_windows([1, 16, 24, 38], first_index=1000, full_reports=2400)
    assert [r['turn_block'] for r in possible] == [16, 24]
    assert possible[0]['first_index'] == 1100
    assert possible[0]['training_last_index'] == 1899
    assert possible[0]['last_index'] == 2139


def test_repeat_turn_and_changed_drift_fail_for_different_later_axes():
    time = np.arange(121.)
    age = time[1:]
    prefix = 70
    # Integrate an exponentially dying acceleration independently of the fitter.
    def displacement(event):
        elapsed = np.maximum(age-event, 0.)
        return 15.*elapsed-225.*(1.-np.exp(-elapsed/15.))

    exposures = np.zeros(120)
    exposures[[19, 94]] = 1.
    repeat = np.column_stack((0.*age, .005*(displacement(20)+displacement(95)), .001*age**2))
    changed = repeat.copy()
    changed[:, 1] -= .01*displacement(95)
    changed[:, 2] -= .002*np.maximum(age-prefix, 0.)**2
    stable = compare(time, repeat, prefix=prefix, exposure=exposures)['scores']['combined']
    shifted = compare(time, changed, prefix=prefix, exposure=exposures)['scores']['combined']
    assert stable['later_rms_neu_m'] == pytest.approx([0., 0., 0.], abs=1e-10)
    assert shifted['coefficients'] == stable['coefficients']
    assert shifted['later_rms_neu_m'] == pytest.approx(np.sqrt(np.mean((changed[prefix:]-repeat[prefix:])**2, axis=0)))
