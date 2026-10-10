# SPDX-License-Identifier: AGPL-3.0-or-later
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import ilvis0_residual_diagnostic as worker


def renderer():
    source = Path(__file__).resolve().parents[2]/'docs/ilvis0-residual-diagnostic-20261010/build_report.py'
    spec = importlib.util.spec_from_file_location('residual_report', source)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_report_rejects_tampered_evidence_before_rendering(tmp_path):
    (tmp_path/'summary.json').write_text('{}')
    (tmp_path/'evidence-receipt.json').write_text(json.dumps(dict(artifacts={'summary.json': '0'*64})))
    with pytest.raises(ValueError, match='hash'):
        renderer().build(tmp_path)
    assert not (tmp_path/'README.md').exists()
    assert not (tmp_path/'residuals.svg').exists()


def test_report_rejects_duplicate_prediction_identities(tmp_path):
    payload = json.dumps(dict(charged_predictions=24, optimizer_starts=0,
                   results=[dict(identity='duplicate', state='complete')]*24)).encode()
    (tmp_path/'summary.json').write_bytes(payload)
    (tmp_path/'evidence-receipt.json').write_text(json.dumps(dict(
        artifacts={'summary.json': hashlib.sha256(payload).hexdigest()})))
    with pytest.raises(ValueError, match='incompatible'):
        renderer().build(tmp_path)


def test_completed_worker_cannot_relaunch_native_predictions(tmp_path, monkeypatch):
    (tmp_path/'completion.json').write_text('{}'); (tmp_path/'manifest.json').write_text('{}')
    monkeypatch.setattr(worker, 'prepare', lambda output: {})
    def forbidden(directory):
        raise AssertionError('native kernel must not load for a completed study')
    monkeypatch.setattr(worker.base.explore, 'load_kernel', forbidden)
    with pytest.raises(ValueError, match='completed'):
        worker.run(tmp_path)
