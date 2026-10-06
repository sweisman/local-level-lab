# SPDX-License-Identifier: AGPL-3.0-or-later
"""Recovery checks for the bounded development worker, with no expensive fits."""
from collections import Counter
import json

import pytest

import development_campaign as worker
from lll.inference_policy import digest
from lll.runtime import numerical_environment


def fake_flight(truth, scenario, seed, sampling, block, boot, variant, **kwargs):
    options = dict(n_boot=boot, bootstrap_sampling=sampling, block_length=block, **kwargs['fit_options'])
    return dict(truth=truth, scenario=scenario, seed=seed, partition='development',
        candidate_id=digest(options), fit_options=options, numerical_environment=numerical_environment(),
        model_test_rank=2, rejected=False, exclusions=[], elapsed_s=.01,
        identifiability={'normalized_singular_values': [.8, .6, .1]},
        candidate_engine='candidate', geometry='fixed', geometry_cell=kwargs['design']['geometry_cell'], variant=variant)


@pytest.fixture(autouse=True)
def cheap_summary(monkeypatch):
    monkeypatch.setattr(worker.research, 'summarize', lambda rows: {'attempted': len(rows)})


def test_thousand_attempts_are_balanced_fresh_and_deterministic():
    config = worker.plan()
    tasks = worker.tasks(config)
    assert len(tasks) == len(set(tasks)) == 1000
    assert min(task[2] for task in tasks) == 600100
    counts = Counter(task[:2] for task in tasks)
    assert len(counts) == 6 and set(counts.values()) == {166, 167}
    assert worker.tasks(config) == tasks


def test_new_pilot_has_disjoint_seeds_and_frozen_rank_margin():
    config = worker.plan(1000, 600300, .1)
    assert config['fit_options']['rank_min_relative_margin'] == .1
    assert not set(worker.tasks(config)) & set(worker.tasks(worker.plan()))
    with pytest.raises(ValueError, match='rank margin'):
        worker.plan(rank_margin=float('nan'))


def test_interruption_resumes_without_repeating_successes_or_failures(tmp_path):
    config, attempts = worker.plan(6), []
    def interrupting(*args, **kwargs):
        if len(attempts) == 2:
            raise KeyboardInterrupt('simulated disconnect')
        attempts.append(args[:3])
        row = fake_flight(*args, **kwargs)
        if len(attempts) == 1:
            row.update(failure='deliberate failed attempt', rejected=None)
        return row
    with pytest.raises(KeyboardInterrupt):
        worker.run_campaign(tmp_path, config, flight_runner=interrupting)
    assert json.loads((tmp_path/'status.json').read_text())['completed_flights'] == 2
    def resumed(*args, **kwargs):
        attempts.append(args[:3])
        return fake_flight(*args, **kwargs)
    worker.run_campaign(tmp_path, config, resume=True, flight_runner=resumed)
    assert attempts == worker.tasks(config)
    data = json.loads((tmp_path/'campaign.json').read_text())
    assert len(data['records']) == 6 and data['records'][0]['failure']
    assert json.loads((tmp_path/'status.json').read_text())['state'] == 'complete'
    assert (tmp_path/'campaign.json.gz').exists() and (tmp_path/'records.jsonl.gz').exists()
    assert (tmp_path/'rank-sweep-narrow.json').exists() and (tmp_path/'magnetic-summary.json').exists()
    # Resuming a completed run never manufactures more evidence.
    worker.run_campaign(tmp_path, config, resume=True, flight_runner=lambda *a, **k: pytest.fail('repeated fit'))


def test_resume_rejects_changed_configuration_and_source(tmp_path):
    config = worker.plan(1)
    worker.run_campaign(tmp_path, config, flight_runner=fake_flight)
    with pytest.raises(ValueError, match='campaign exists'):
        worker.run_campaign(tmp_path, config, flight_runner=fake_flight)
    with pytest.raises(ValueError, match='changed'):
        worker.run_campaign(tmp_path, worker.plan(2), resume=True, flight_runner=fake_flight)
    manifest = json.loads((tmp_path/'manifest.json').read_text())
    manifest['implementation_hash'] = 'different'
    worker.atomic_json(tmp_path/'manifest.json', manifest)
    with pytest.raises(ValueError, match='changed'):
        worker.run_campaign(tmp_path, config, resume=True, flight_runner=fake_flight)


def test_source_change_during_fit_stops_before_recording_it(tmp_path, monkeypatch):
    def changing(*args, **kwargs):
        row = fake_flight(*args, **kwargs)
        monkeypatch.setattr(worker, 'implementation_hash', lambda: 'changed during fit')
        return row
    with pytest.raises(RuntimeError, match='changed during'):
        worker.run_campaign(tmp_path, worker.plan(1), flight_runner=changing)
    status = json.loads((tmp_path/'status.json').read_text())
    assert status['state'] == 'failed' and status['completed_flights'] == 0


def test_partial_write_is_preserved_and_only_missing_task_is_rerun(tmp_path):
    config = worker.plan(2)
    worker.run_campaign(tmp_path, config, flight_runner=fake_flight)
    checkpoint = tmp_path/'records.jsonl'
    original = checkpoint.read_bytes()
    first, second = original.splitlines(keepends=True)
    checkpoint.write_bytes(first+second[:20])
    assert len(worker.load_records(checkpoint, config)) == 1
    assert checkpoint.read_bytes() == first
    assert (tmp_path/'recovery.jsonl').exists()
    attempts = []
    def resumed(*args, **kwargs):
        attempts.append(args[:3])
        return fake_flight(*args, **kwargs)
    worker.run_campaign(tmp_path, config, resume=True, flight_runner=resumed)
    assert attempts == worker.tasks(config)[1:]
    assert checkpoint.read_bytes() == original
    checkpoint.write_bytes(original.rstrip(b'\n'))
    assert len(worker.load_records(checkpoint, config)) == 2
    assert checkpoint.read_bytes() == original


def test_duplicate_record_and_malformed_completed_line_are_rejected(tmp_path):
    config = worker.plan(2)
    worker.run_campaign(tmp_path, config, flight_runner=fake_flight)
    checkpoint = tmp_path/'records.jsonl'
    first = checkpoint.read_bytes().splitlines(keepends=True)[0]
    checkpoint.write_bytes(first+first)
    with pytest.raises(ValueError, match='duplicate or task mismatch'):
        worker.load_records(checkpoint, config)
    checkpoint.write_bytes(b'{broken}\n')
    with pytest.raises(ValueError, match='malformed completed'):
        worker.load_records(checkpoint, config)


def test_second_worker_is_rejected(tmp_path):
    import fcntl
    with (tmp_path/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match='active worker'):
            worker.run_campaign(tmp_path, worker.plan(1), flight_runner=fake_flight)
