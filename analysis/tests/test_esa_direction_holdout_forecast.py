# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test the predetermined reference rule and clock support."""

import pytest

from lll.esa_direction_holdout_forecast import FIELDS, METHODS, WIDTHS, receiver_times, reference_errors


def test_reference_error_is_the_largest_previous_closest_model_error():
    windows = []
    for i in range(8):
        scores = {method: dict(angles={field: {
            'uncorrected': dict(rms_deg={'globe': i + .2, 'disc': 10.}),
            'antenna_corrected': dict(rms_deg={'globe': 10., 'disc': 8. - i})}
            for field in FIELDS}) for method in METHODS}
        windows.append(dict(window=i, kind='straight', widths=[dict(width_reports=width, scores={'air1': scores})
                                                                 for width in WIDTHS]))
    reference = reference_errors(dict(windows=windows))
    assert reference[str(WIDTHS[0])][METHODS[0]][FIELDS[0]] == dict(uncorrected=7.2, antenna_corrected=8.)
    with pytest.raises(ValueError, match='eight earlier'):
        reference_errors(dict(windows=windows[:-1]))


@pytest.mark.parametrize('field,replacement', [('time_s', 40.03), ('sequence', 81), ('gps_week', 2270)])
def test_receiver_gaps_or_sequence_errors_cannot_enter_forecast(field, replacement):
    rows = [dict(time_s=float(i), sequence=i*2, gps_week=2269) for i in range(400)]
    assert receiver_times(rows)[-1] == 399.
    rows[40][field] = replacement
    with pytest.raises(ValueError, match='receiver clock and sequence'):
        receiver_times(rows)
