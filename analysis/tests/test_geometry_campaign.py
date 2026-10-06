# SPDX-License-Identifier: AGPL-3.0-or-later
"""Geometry checkpoints cannot replay failures, exceed budgets or change their freeze."""
import base64
import copy
import json
import subprocess

import pytest

import geometry_campaign as worker
from lll.research_design import freeze_manifest
from test_candidate_eligibility import candidate_fit


def small_plan(monkeypatch, seconds=10.):
    config = worker.plan(seconds)
    config['cases'] = config['cases'][:3]
    monkeypatch.setattr(worker, 'plan', lambda _: copy.deepcopy(config))
    return config


def test_plan_is_exactly_300_paired_development_cases():
    config = worker.plan(3600.)
    assert len(config['cases']) == 300
    assert all(c['seed'] == 600500 for c in config['cases'])
    assert {c['geometry'] for c in config['cases']} == {'fixed', 'stress'}
    assert sum(c['cell_id'] == 'exact-protocol' for c in config['cases']) == 12
    assert config['fit_options']['design_only'] is True
    with pytest.raises(ValueError, match='positive'):
        worker.plan(float('nan'))


def test_resume_preserves_failure_and_charges_interrupted_reservation(tmp_path, monkeypatch):
    config = small_plan(monkeypatch)
    calls = []
    def interrupted(output, case, settings, allocation):
        calls.append(case)
        if len(calls) == 2:
            raise KeyboardInterrupt()
        return {'failure': 'retained analysis failure'}
    with pytest.raises(KeyboardInterrupt):
        worker.run_campaign(tmp_path, config, runner=interrupted)
    assert json.loads((tmp_path/'status.json').read_text())['completed_evaluations'] == 1
    # The interrupted attempt conservatively uses the remaining slice; no automatic refill.
    worker.run_campaign(tmp_path, config, resume=True, runner=lambda *_: pytest.fail('budget exhausted'))
    assert len(calls) == 2
    status = json.loads((tmp_path/'status.json').read_text())
    assert status['state'] == 'budget_exhausted' and status['failures'] == 1
    assert status['charged_s'] == config['wall_time_cap_s']


def test_completed_resume_does_not_repeat_cases_or_accept_changed_manifest(tmp_path, monkeypatch):
    config = small_plan(monkeypatch)
    worker.run_campaign(tmp_path, config, runner=lambda *_: {'failure': 'no fit'})
    worker.run_campaign(tmp_path, config, resume=True, runner=lambda *_: pytest.fail('replayed'))
    assert json.loads((tmp_path/'status.json').read_text())['state'] == 'complete'
    changed = copy.deepcopy(config)
    changed['wall_time_cap_s'] += 1
    with pytest.raises(ValueError, match='unchanged'):
        worker.run_campaign(tmp_path, changed, resume=True)
    (tmp_path/'records.jsonl').unlink()
    with pytest.raises(ValueError, match='original journal missing'):
        worker.run_campaign(tmp_path, config, resume=True)


def test_truncated_tail_preserved_and_complete_corruption_rejected(tmp_path, monkeypatch):
    config = small_plan(monkeypatch)
    worker.run_campaign(tmp_path, config, runner=lambda *_: {'failure': 'no fit'})
    path = tmp_path/'records.jsonl'
    original = path.read_bytes()
    tail = b'{"case":'
    path.write_bytes(original+tail)
    rows = worker.load_records(path, config, freeze_manifest(config)['manifest_hash'])
    assert len(rows) == 3 and path.read_bytes() == original
    recovery = json.loads((tmp_path/'recovery.jsonl').read_text())
    assert base64.b64decode(recovery['discarded_base64']) == tail
    path.write_bytes(original+b'invalid\n')
    with pytest.raises(ValueError, match='malformed complete'):
        worker.load_records(path, config, freeze_manifest(config)['manifest_hash'])


def test_deadline_consumes_budget_without_completing_case(tmp_path, monkeypatch):
    config = small_plan(monkeypatch)
    def expired(*_):
        raise subprocess.TimeoutExpired('case', 10)
    worker.run_campaign(tmp_path, config, runner=expired)
    status = json.loads((tmp_path/'status.json').read_text())
    assert status['state'] == 'budget_exhausted' and status['completed_evaluations'] == 0
    assert status['charged_s'] == 10.


def test_score_requires_all_cases_and_uses_free_fit_rank_margin():
    config = worker.plan(3600.)
    fit = candidate_fit()
    fit['model_test_rank'] = 2
    fit['identifiability']['rank_boundary_margin'] = fit['identifiability']['rank_threshold']*.2
    rows = [dict(case=case, result=copy.deepcopy(fit)) for case in config['cases'][:12]]
    score = worker.scores(rows)[0]
    assert score['all_estimable'] and score['all_rank2_stable']
    assert not worker.scores(rows[:-1])[0]['all_estimable']
    rows[-1]['result']['convergence']['converged'] = False
    assert not worker.scores(rows)[0]['all_estimable']


def test_protocol_comparison_pairs_seeds_and_requires_every_expected_case(tmp_path):
    original = worker.plan(900.)
    path = tmp_path/'comparison.json'
    comparison = dict(partition='development', bootstrap=0, seeds=[600501, 600502, 600503],
        protocols={'control': original['protocol'], 'proposal': original['protocol']},
        truths=['sphere_rotating', 'sphere_still', 'flat_still'],
        scenarios=['bias_mixed', 'wind'], crab_models=['dynamic', 'wind'])
    path.write_text(json.dumps(comparison))
    config = worker.plan(900., path)
    assert len(config['cases']) == 72
    for control, proposal in zip(config['cases'][::2], config['cases'][1::2]):
        assert control['cell_id'] == 'control' and proposal['cell_id'] == 'proposal'
        assert {k: v for k, v in control.items() if k != 'cell_id'} == {
            k: v for k, v in proposal.items() if k != 'cell_id'}
    rows = [dict(case=c, result=candidate_fit()) for c in config['cases'] if c['cell_id'] == 'control']
    assert worker.scores(rows, {'control': 36, 'proposal': 36})[0]['all_estimable']
    assert not worker.scores(rows[:-1], {'control': 36, 'proposal': 36})[0]['all_estimable']
    comparison['seeds'] = [600501, 600501]
    path.write_text(json.dumps(comparison))
    with pytest.raises(ValueError, match='duplicate'):
        worker.plan(900., path)
