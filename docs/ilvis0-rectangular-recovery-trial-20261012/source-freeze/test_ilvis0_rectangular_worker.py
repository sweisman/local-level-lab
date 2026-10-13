# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
import json
from pathlib import Path

import pytest


def load_worker():
    path = Path(__file__).with_name('ilvis0_rectangular_worker.py')
    spec = importlib.util.spec_from_file_location('rectangular_worker_test', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_separate_worker_configuration_does_not_mutate_completed_worker():
    import ilvis0_recovery_worker as original
    version, guide, method = original.VERSION, original.GUIDE, original.solver.VERSION
    worker = load_worker()
    assert worker.core.VERSION != version
    assert worker.core.OUTPUT != original.OUTPUT
    assert worker.core.solver.POLICY['method'] == 'dogbox'
    assert (original.VERSION, original.GUIDE, original.solver.VERSION) == (version, guide, method)


def test_local_tangent_artifact_is_hashed_and_corruption_is_rejected(tmp_path):
    worker = load_worker()
    fit = dict(local_linearization={'residual': [1.], 'jacobian': [[2.]]})
    worker.save_linearization(tmp_path, 'segment::case::model::primary', fit)
    assert 'local_linearization' not in fit
    worker.verify_linearizations(tmp_path, {'results': {'id': fit}})
    (tmp_path/fit['linearization_file']).write_bytes(b'bad')
    with pytest.raises(ValueError):
        worker.verify_linearizations(tmp_path, {'results': {'id': fit}})


def test_missing_authorization_prevents_original_access(tmp_path, monkeypatch):
    worker = load_worker()
    def unexpected(*args, **kwargs):
        raise AssertionError('originals or kernels accessed before authorization')
    monkeypatch.setattr(worker.core, 'verify', unexpected)
    with pytest.raises(ValueError, match='authorization'):
        worker.core.run(tmp_path)


def test_completed_trial_cannot_resume(tmp_path):
    worker = load_worker()
    (tmp_path/'completion.json').write_text(json.dumps({'state': 'complete'}))
    with pytest.raises(ValueError, match='completed'):
        worker.core.run(tmp_path)
