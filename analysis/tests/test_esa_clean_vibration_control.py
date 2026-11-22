"""Clean 100 Hz motion must not be rejected for floating-point roundoff."""

from lll.esa_clean_vibration_control import build


def test_clean_integrator_matches_both_analytic_motion_modes():
    result = build()
    assert [row['vibration'] for row in result['rows']] == [False, True]
    assert max(max(row['maximum_absolute_error_neu_m'])
               for row in result['rows']) < .0004
    assert result['errors_injected'] is False
