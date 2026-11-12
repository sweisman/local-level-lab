"""Freeze a transfer scale from prior first-cut errors only."""
import csv
import io
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[2] / 'docs/prediction-rolling-origin/result.csv'
SHA256 = '651ae7c87d28d4d5e2d4b9493d3f5a990fc550adc1972c30d970e3bc32ac4117'


def test_reference_uses_three_previously_scored_first_cuts():
    from lll.prediction_transfer_reference import from_saved_csv
    result = from_saved_csv(SOURCE.read_bytes(), expected_sha256=SHA256)
    assert result['recordings'] == 3
    assert result['settings'] == 12
    assert result['reference_rms_m']['north'] == pytest.approx(5.092235592304115)
    assert result['reference_rms_m']['east'] == pytest.approx(19.764265256987176)
    assert result['reference_rms_m']['vertical'] == pytest.approx(10.778407396732868)
    assert result['coverage_calibrated'] is False
    assert result['scientific_decision'] == 'abstain'


def test_outer_scores_cannot_change_earlier_reference():
    from lll.prediction_transfer_reference import from_saved_csv
    import hashlib
    raw = SOURCE.read_bytes()
    base = from_saved_csv(raw, expected_sha256=SHA256)
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    for row in rows:
        for key in row:
            if key.startswith('outer_') or key.endswith('_outer_rms_m') or key.endswith('_ratio'):
                row[key] = '987654321'
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=rows[0].keys(), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    altered = output.getvalue().encode()
    later_changed = from_saved_csv(altered, expected_sha256=hashlib.sha256(altered).hexdigest())
    assert later_changed['reference_rms_m'] == base['reference_rms_m']
    assert later_changed['selected_inner_identities'] == base['selected_inner_identities']


def test_changed_binding_and_missing_inner_result_fail_closed():
    from lll.prediction_transfer_reference import from_saved_csv
    import hashlib
    raw = SOURCE.read_bytes()
    with pytest.raises(ValueError):
        from_saved_csv(raw, expected_sha256='0' * 64)
    rows = list(csv.DictReader(io.StringIO(raw.decode())))
    row = next(row for row in rows if row['profile'] == 'False' and row['clock'] == 'header_elapsed')
    row['north_inner_rms_m'] = ''
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=rows[0].keys(), lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    changed = output.getvalue().encode()
    with pytest.raises(ValueError):
        from_saved_csv(changed, expected_sha256=hashlib.sha256(changed).hexdigest())
