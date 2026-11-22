# SPDX-License-Identifier: AGPL-3.0-or-later

from pathlib import Path

import pytest

from lll.esa_direction_evidence import FILES, audit, angle_pair_scores, read_report


def test_angle_pair_score_has_known_tie_distance():
    row = dict(observed_deg=[1.0]*28, disc_minus_globe_deg=2.0,
               scores={'globe': dict(predicted_deg=[1.0]*28, rms_deg=0.0),
                       'disc': dict(predicted_deg=[3.0]*28, rms_deg=2.0)})
    assert angle_pair_scores(row) == (0.0, 2.0, 1.0)
    row['scores']['disc']['rms_deg'] = 1.0
    with pytest.raises(ValueError, match='score differs'):
        angle_pair_scores(row)


def test_altered_report_is_rejected_before_parsing(tmp_path):
    filename, expected = next(iter(FILES.items()))
    (tmp_path / filename).write_bytes(b'not the saved report')
    with pytest.raises(ValueError, match='hash differs'):
        read_report(tmp_path / filename, expected)


def test_public_tables_recompute_from_saved_reports():
    folder = Path(__file__).resolve().parents[2] / 'docs/prediction-observed-development'
    result = audit(folder)
    assert result['paired_settings'] == 48
    assert result['adjacent_pair_omissions_favoring_globe'] == 672
    assert result['retained_field_globe_transfer_factor']['later_median'] == pytest.approx(4.591113631568517)
    assert sum(x['globe_lower'] for x in result['angle_pairs']) == 48
    assert len(result['angle_pairs']) == 6
    assert sum(x['globe_lower'] for x in result['lever_arm_angle_pairs']) == 48
    assert result['largest_lever_arm_angle_change_rms_deg'] == pytest.approx(0.08798809472081237)
