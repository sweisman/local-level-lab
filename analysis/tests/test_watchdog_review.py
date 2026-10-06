# SPDX-License-Identifier: AGPL-3.0-or-later
"""Wind specificity and true-slip protection, using saved bins without more flight synthesis."""
import json
from pathlib import Path

import numpy as np
import pytest

from lll import slip
from review_watchdog import review


def test_saved_oracle_removes_wind_flags_and_preserves_creep_controls():
    path = Path(__file__).resolve().parents[2]/'docs/development-1000-20261005/watchdog-diagnostic-20261006.json'
    report = review(json.loads(path.read_text()))
    assert len(report['cases']) == 8
    for row in report['cases']:
        injected = row['case']['mount_yaw_creep_dph'] != 0
        assert bool(row['oracle_heading_excluded']) == injected
        assert row['oracle_watchdog']['mount_slip_confirmed'] is False
    failing = next(row for row in report['cases'] if row['case']['seed'] == 600107
                   and row['case']['scenario'] == 'wind' and row['case']['mount_yaw_creep_dph'] == 0)
    assert failing['original_excluded'] == [0, 6]
    assert failing['selected_fits'][0]['n_bins'] == 65
    assert failing['original_geometry']['n_bins'] == 74


def test_course_reference_cannot_distinguish_crab_from_mount_yaw(monkeypatch):
    t = np.arange(12)*60.
    phase = np.radians(3.*t/3600.)
    # With zero airframe field, either changing crab or mount yaw gives exactly this signal.
    bins = dict(t=t, lat=np.zeros(12), lon=np.zeros(12), h=np.zeros(12), psi=np.zeros(12),
        mag=np.column_stack((np.cos(phase), np.sin(phase), np.zeros(12))),
        up=np.tile([0., 0., 1.], (12, 1)), epoch=np.zeros(12), seg=np.zeros(12))
    monkeypatch.setattr(slip, 'declination_deg', lambda *unused: (np.zeros(12), np.ones(12)))
    result = slip.watchdog(bins, [0., 0., 0.], 2026., 1.5)
    assert result['exclude_segments'] == [0]
    assert result['mount_slip_confirmed'] is False
    assert result['variants']['wmm'][0]['apparent_yaw_rate_dph'] == pytest.approx(3.)
    assert result['variants']['wmm'][0]['airframe_field_calibrated'] is False


def test_oracle_review_refuses_validation_evidence():
    with pytest.raises(ValueError):
        review(dict(partition='validation', replay=True, state='complete'))
