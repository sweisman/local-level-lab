# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind the observed trial check to the original fit and forecast allowances."""

from lll import ilvis0_matched_trial_observed as study


def test_recorded_trial_tasks_allow_only_one_control_forecast():
    original = {identity: dict(identity=identity, training_packets=50, training_epochs=3,
                               full_packets=100, scoring_epochs=2, limits={})
                for identity in (*study.FORECASTS, 'unused')}
    rows = study.tasks(original)
    assert [row['identity'] for row in rows] == list(study.FORECASTS)
    assert sum(row['limits']['native_calls'] for row in rows) == 121
    for row in rows:
        allowed = int(study.FORECASTS[row['identity']])
        assert row['limits']['packet_visits'] == 9000+500*allowed
        assert row['limits']['native_calls'] == 60+allowed
