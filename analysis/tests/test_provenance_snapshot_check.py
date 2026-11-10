"""The frozen provenance publication remains verifiable after later source edits."""

from pathlib import Path
from importlib import import_module


ROOT = Path(__file__).resolve().parents[2]


def test_frozen_provenance_snapshot_survives_newer_findings_receipt():
    assert (ROOT / 'analysis/lll/provenance_snapshot_check.py').is_file()
    result = import_module('lll.provenance_snapshot_check').verify(ROOT)
    assert result == {
        'verified': True,
        'records': 62,
        'conservative_groups': 35,
        'historical_receipt_recovered': True,
        'current_receipt_differs': True,
        'original_files_read': 0,
        'native_predictions': 0,
    }
