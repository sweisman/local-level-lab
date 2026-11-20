# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from pathlib import Path
from shutil import copyfile

import pytest

from lll.esa_code_receipt_audit import audit


SOURCE = Path(__file__).resolve().parents[2] / 'docs/prediction-observed-development'


def test_audit_needs_only_the_saved_report_files(tmp_path):
    for name in (
        'esa-rinex-code-comparison-freeze.zip',
        'esa-rinex-code-comparison-result.json',
        'esa-alternate-ppp-scoring-result.json',
    ):
        copyfile(SOURCE / name, tmp_path / name)
    rows, receiver = audit(tmp_path)
    assert len(rows) == 2
    assert receiver['l1_broadcast']['later']['horizontal_rms_m'] == pytest.approx(1.51, abs=.005)
    assert all(row['law'] in {'increment', 'point'} for row in rows)
    for row in rows:
        expected = {'air1', 'l1_broadcast', 'dual_frequency'}
        assert set(row['total_rms_m']) == expected
        for scores in row['total_rms_m'].values():
            assert scores['sphere_rotating'] < scores['sphere_still'] < scores['flat_still']

    saved = tmp_path / 'esa-rinex-code-comparison-result.json'
    altered = json.loads(saved.read_bytes())
    altered['result']['matched_epochs'] -= 1
    saved.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='hash'):
        audit(tmp_path)
