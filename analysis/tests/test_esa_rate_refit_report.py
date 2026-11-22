"""Saved-only ESA refit scoring keeps training and later epochs separate."""
import numpy as np
import pytest


def test_rate_refit_report_scores_six_routes_without_fit():
    from lll.esa_rate_refit_report import compare

    receiver = np.array([[0., 0., 100.] for _ in range(9)])
    routes = {f'{method}-{law}': receiver.copy()
              for method in ('linear_points', 'left_hold', 'right_hold')
              for law in ('increment', 'point')}
    result = compare(routes, receiver, training_epochs=6)
    assert len(result) == 6
    assert all(row['training']['horizontal_rms_m'] == 0 and
               row['prediction']['vertical_rms_m'] == 0
               for row in result.values())
    routes['left_hold-point'] = receiver[:8]
    with pytest.raises(ValueError, match='matched complete'):
        compare(routes, receiver, training_epochs=6)
