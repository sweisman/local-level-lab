# SPDX-License-Identifier: AGPL-3.0-or-later
import gzip
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


def load_worker():
    path = Path(__file__).with_name('ilvis0_boundary_worker.py')
    assert path.exists(), 'separate boundary-aware worker is missing'
    spec = importlib.util.spec_from_file_location('boundary_worker_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_worker_keeps_frozen_recovery_globals_unchanged():
    import ilvis0_recovery_worker as original
    before = original.VERSION, original.GUIDE, original.OUTPUT, original.solver.VERSION
    worker = load_worker()
    assert worker.core.VERSION != original.VERSION
    assert worker.core.OUTPUT != original.OUTPUT
    assert worker.core.solver.VERSION == 'ilvis0-boundary-bvls-v1'
    assert before == (original.VERSION, original.GUIDE, original.OUTPUT, original.solver.VERSION)


def test_saved_tangent_preserves_values_and_rejects_corruption(tmp_path):
    worker = load_worker()
    local = dict(residual=[1.], jacobian=[[2.]], normalized_parameters=[.2])
    fit = dict(local_linearization=local, converged=True)
    worker.save_linearization(tmp_path, 'one::case::model::primary', fit)
    assert json.loads(gzip.decompress((tmp_path/fit['linearization_file']).read_bytes())) == local
    worker.verify_linearizations(tmp_path, {'results': {'one': fit}})
    (tmp_path/fit['linearization_file']).write_bytes(b'corrupted')
    with pytest.raises(ValueError):
        worker.verify_linearizations(tmp_path, {'results': {'one': fit}})


def test_missing_frozen_budget_record_prevents_scientific_access(tmp_path, monkeypatch):
    worker = load_worker()
    monkeypatch.setattr(worker.core, 'verify', lambda *a, **k: pytest.fail('scientific access before limits'))
    with pytest.raises(ValueError, match='authorization'):
        worker.core.run(tmp_path)


def test_completed_trial_cannot_resume(tmp_path):
    worker = load_worker()
    (tmp_path/'completion.json').write_text('{}')
    with pytest.raises(ValueError, match='completed'):
        worker.core.run(tmp_path)


def test_budget_record_matches_freeze_and_does_not_replace_existing_record(tmp_path):
    worker = load_worker()
    proposal = dict(maximum_starts=24, maximum_native_sweeps=14448)
    (tmp_path/'manifest.json').write_text(json.dumps(dict(proposal=proposal)))
    worker.record_limits(tmp_path, {'proposal': proposal})
    first = (tmp_path/'authorization.json').read_bytes()
    worker.core.authorization(tmp_path, proposal)
    worker.record_limits(tmp_path, {'proposal': proposal})
    assert (tmp_path/'authorization.json').read_bytes() == first
    with pytest.raises(ValueError, match='authorization'):
        worker.core.authorization(tmp_path, dict(maximum_starts=25, maximum_native_sweeps=15050))


def test_incomplete_control_receipt_rejected():
    worker = load_worker()
    with pytest.raises(ValueError, match='qualification'):
        worker.validate_controls(dict(artifacts={}, sources={}))


def completed_dependency(tmp_path, worker):
    source = tmp_path/'native.c'
    source.write_text('unchanged numerical source')
    (tmp_path/'source-freeze').mkdir()
    (tmp_path/'source-freeze'/'native.c').write_bytes(source.read_bytes())
    public = tmp_path/'PLAN.md'
    public.write_text('updated public explanation')
    artifact = tmp_path/'selection.json'
    artifact.write_text('unchanged selection')
    ids = [f'control-{i}' for i in range(12)]
    manifest = dict(sources={str(source): worker.core.base.il.sha256(source)},
                    inputs={str(public): 'prior-public-text-hash'},
                    artifacts={'selection.json': worker.core.base.il.sha256(artifact)},
                    environment=worker.core.base.runtime.numerical_environment(),
                    proposal={'identities': ids})
    worker.core.base.follow.atomic_json(tmp_path/'manifest.json', manifest)
    digest = worker.core.base.il.sha256(tmp_path/'manifest.json')
    book = worker.core.journal.Ledger(tmp_path, digest, ids)
    for identity in ids:
        book.start(identity)
    (tmp_path/'sweeps.jsonl').write_text('')
    summary = dict(starts=12, native_sweeps=0, results={identity:
                   dict(fit_native_sweeps=0, diagnostic_native_sweeps=0) for identity in ids})
    worker.core.base.follow.atomic_json(tmp_path/'summary.json', summary)
    complete = dict(state='complete', manifest_sha256=digest,
                    summary_sha256=worker.core.base.il.sha256(tmp_path/'summary.json'),
                    starts=12, native_sweeps=0,
                    journal_hashes={name: worker.core.base.il.sha256(tmp_path/name)
                                    for name in ('starts.jsonl', 'sweeps.jsonl')})
    worker.core.base.follow.atomic_json(tmp_path/'completion.json', complete)
    return manifest


def test_completed_tools_can_be_reused_after_public_text_changes(tmp_path):
    worker = load_worker()
    expected = completed_dependency(tmp_path, worker)
    assert worker.completed_numerical_dependency(tmp_path) == expected


@pytest.mark.parametrize('name', ['native.c', 'source-freeze/native.c',
                                 'selection.json', 'summary.json', 'starts.jsonl'])
def test_completed_dependency_rejects_altered_numerical_evidence(tmp_path, name):
    worker = load_worker()
    completed_dependency(tmp_path, worker)
    (tmp_path/name).write_text('altered')
    with pytest.raises(ValueError):
        worker.completed_numerical_dependency(tmp_path)


@pytest.mark.parametrize('model', ['sphere_rotating', 'sphere_still', 'flat_still'])
def test_actual_boundary_solver_on_independent_native_control(tmp_path, monkeypatch, model):
    from lll import ilvis0_geographic_controls as geographic
    worker = load_worker()
    fixture = geographic.fixture(model, 'nominal')
    kernels = (worker.core.base.explore.load_kernel(tmp_path/'kernel')[0],
               worker.core.base.shape.load_tangent(tmp_path/'kernel')[0])
    values = np.zeros((len(fixture['dt']), 15))
    values[:, 9:12] = fixture['theta']
    values[:, 12:15] = fixture['dv']
    covariance = np.diag(np.tile(.1/fixture['metric'], len(fixture['gps_times']))**2)
    # This fixture's sensor X points north while the aircraft flies east. Supply
    # its independently defined initial pose: the archival initializer assumes
    # a forward mount, which this particular software fixture does not have.
    monkeypatch.setattr(worker.core.base.corpus, 'initialize',
                        lambda *args: (fixture['initial'], 9.81))
    seed, _ = worker.core.base.corpus.initialize(fixture['gps_times'], fixture['gps'], values, model)
    problem = worker.core.base.shape.TangentProblem(
        fixture['theta'], fixture['dv'], fixture['dt'], fixture['gps_times'], fixture['gps'],
        covariance, seed, worker.core.base.estimator.Bounds(geographic.LIMITS),
        fit_earth_removal=False, kernel=kernels[0], tangent_kernel=kernels[1],
        clock_hypothesis='nominal_200Hz', processing_hypothesis='unsubtracted_increment_hypothesis',
        maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
    point = np.zeros(len(problem.bounds.active))
    residual, _, _ = problem.residual_tangent(point, model)
    reference = dict(active_parameters=list(problem.bounds.active),
                     normalized_parameters=point.tolist(), residual_sum_squares=float(residual@residual))
    book = worker.core.journal.Ledger(tmp_path, 'software', ['one'], fit_limit=600, diagnostic_limit=2)
    fit = worker.fit_task(tmp_path, dict(identity='one', model=model, case_id='case', role='control'),
                          reference, dict(limits=geographic.LIMITS, profile=False),
                          (values, fixture['gps_times'], fixture['gps'], {}, covariance), kernels, book)
    assert 'error' not in fit, fit
    assert fit['converged'] and fit['stability_verified']
    assert fit['fit_native_sweeps'] == fit['evaluations'] <= 600
    assert fit['diagnostic_native_sweeps'] == 2
    assert max(fit['track_rms_neu_m']) < 1e-4
    assert not fit['scientific_eligible']
    worker.verify_linearizations(tmp_path, {'results': {'one': fit}})
