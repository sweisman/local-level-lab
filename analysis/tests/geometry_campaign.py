# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, checkpointed synthetic geometry diagnostics; never calibrated decisions."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'analysis'), str(ROOT/'server')]
import research
from development_campaign import archive
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.policy import design_eligibility
from lll.research_design import freeze_manifest, plain, protocol_geometry, realize

DEFAULT_OUTPUT = ROOT/'docs/geometry-development-20261006'
PLAN = ROOT/'docs/research-next-stage-20261006/geometry-stress-plan.json'
PROTOCOL = ROOT/'docs/development-protocol-75min.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as target:
        target.write(json.dumps(plain(value), indent=2, allow_nan=False)+'\n')
        target.flush()
        os.fsync(target.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def plan(seconds, protocol_plan=None):
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('wall-time cap must be finite and positive')
    if protocol_plan is not None:
        path = Path(protocol_plan).resolve()
        comparison = json.loads(path.read_text())
        if comparison.get('partition') != 'development' or comparison.get('bootstrap') != 0:
            raise ValueError('protocol comparison requires development and zero bootstrap')
        seeds = comparison['seeds']
        from lll.research_design import seed_range
        if not seeds or len(set(seeds)) != len(seeds):
            raise ValueError('duplicate or empty development seeds')
        for seed in seeds:
            seed_range('development', seed)
        protocols = {name: protocol_geometry(value) for name, value in comparison['protocols'].items()}
        if not protocols or set(comparison['truths']) != {'sphere_rotating', 'sphere_still', 'flat_still'}:
            raise ValueError('protocol comparison requires named protocols and all three truths')
        if comparison['scenarios'] != ['bias_mixed', 'wind'] or comparison['crab_models'] != ['dynamic', 'wind']:
            raise ValueError('protocol comparison must cover both scenarios and nuisance models')
        # Interleave protocols within each seed so a time cap cannot complete only one arm.
        cases = [dict(cell_id=name, geometry='fixed', truth=truth, scenario=scenario,
                      crab_model=crab, seed=seed)
                 for seed in seeds for truth in comparison['truths']
                 for scenario in comparison['scenarios'] for crab in comparison['crab_models']
                 for name in protocols]
        config = plan(seconds)
        config.update(cases=cases, protocols=protocols, protocol_plan_path=str(path),
            inputs={str(path): sha(path)}, seed_pairing='shared within seed across protocols/truths/scenarios/crab models')
        return config
    source = json.loads(PLAN.read_text())
    cells = source['selected_synthetic_cells']
    comparison = source['proposed_comparisons']
    if (source['partition'] != 'development' or len(cells) != 24 or
            comparison['bootstrap'] != 0 or comparison['common_seed_start'] != 600500):
        raise ValueError('unexpected development geometry plan')
    cases = []
    # Controls first, then the fixed plan order; no outcome-based selection or stopping.
    for cell in [None, *cells]:
        for truth in comparison['truths']:
            for scenario in comparison['scenarios']:
                for crab in comparison['crab_models']:
                    cases.append(dict(cell_id=cell['id'] if cell else 'exact-protocol',
                        geometry='stress' if cell else 'fixed', truth=truth, scenario=scenario,
                        crab_model=crab, seed=600500))
    if len(cases) != 300 or len({digest(case) for case in cases}) != 300:
        raise ValueError('expected exactly 300 unique cases')
    return dict(partition='development', mode='geometry-only; no bootstrap or calibrated decisions',
        wall_time_cap_s=float(seconds), case_time_cap_s=300., cases=cases,
        inputs={str(PLAN.relative_to(ROOT)): sha(PLAN), str(PROTOCOL.relative_to(ROOT)): sha(PROTOCOL)},
        runner_sha256=sha(Path(__file__)), protocol=protocol_geometry(json.loads(PROTOCOL.read_text())),
        fit_options=dict(research_candidate=True, design_only=True, noise_model='axis_segment',
            bias_model='dynamic', forward_uncertainty=True, bootstrap_refit='nonlinear',
            crab_rate_sigma_dph=1., crab_knot_seconds=None,
            bias_knot_seconds=INFERENCE_POLICY['bias_knot_seconds'],
            bias_rw_sigma_dph_sqrth=INFERENCE_POLICY['bias_rw_sigma_dph_sqrth'],
            rank_min_relative_margin=.1), variant='spp', seed_pairing='one shared seed across all cases')


def evaluate(case, config):
    protocol = config.get('protocols', {}).get(case['cell_id'], config['protocol'])
    kwargs = dict(geometry_cell=case['cell_id']) if case['geometry'] == 'stress' else dict(protocol=protocol)
    design = realize(case['seed'], case['scenario'], geometry=case['geometry'], **kwargs)
    return research.flight_run(case['truth'], case['scenario'], case['seed'], 'moving', 15, 0,
        config['variant'], geometry=case['geometry'], design=design,
        fit_options={**config['fit_options'], 'crab_model': case['crab_model']})


def load_records(path, config, manifest_hash):
    records, offset, tail = [], 0, None
    if not path.exists():
        raise ValueError('original journal missing; recover it before resuming')
    with path.open('rb') as source:
        for line in source:
            try:
                row = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                if line.endswith(b'\n'):
                    raise ValueError('malformed complete journal record') from None
                tail = line
                break
            index = len(records)
            if (index >= len(config['cases']) or row.get('case') != config['cases'][index] or
                    row.get('manifest_hash') != manifest_hash or 'result' not in row):
                raise ValueError('journal identity, order or provenance mismatch')
            records.append(row)
            offset += len(line)
    if tail is not None:
        with (path.parent/'recovery.jsonl').open('a') as recovery:
            recovery.write(json.dumps(dict(offset=offset, discarded_base64=base64.b64encode(tail).decode()))+'\n')
            recovery.flush()
            os.fsync(recovery.fileno())
        with path.open('r+b') as journal:
            journal.truncate(offset)
            journal.flush()
            os.fsync(journal.fileno())
    elif offset and not line.endswith(b'\n'):
        with path.open('ab') as journal:
            journal.write(b'\n')
            journal.flush()
            os.fsync(journal.fileno())
    return records


def scores(records, expected_counts=None):
    groups = {}
    for row in records:
        result, case = row['result'], row['case']
        criterion = design_eligibility(result.get('design_identifiability') or {})
        design_rank = (result.get('design_identifiability') or {}).get('estimable_rank')
        valid = bool(criterion['valid'] and isinstance(design_rank, int) and design_rank > 0 and not result.get('failure') and
                     result.get('convergence', {}).get('converged') is True)
        rank = result.get('model_test_rank')
        information = result.get('identifiability') or {}
        cutoff, margin = information.get('rank_threshold'), information.get('rank_boundary_margin')
        stable = (isinstance(cutoff, (int, float)) and cutoff > 0 and
                  isinstance(margin, (int, float)) and math.isfinite(margin) and margin/cutoff >= .1)
        entry = dict(case=case, valid=valid, all_estimable=bool(valid and criterion['all_estimable']),
            margin=criterion['worst_margin'] if valid else None,
            information=criterion['worst_information'] if valid else None,
            limiting_contrast=criterion['limiting_contrast'], rank=rank, rank_stable=stable,
            failure=result.get('failure'), exclusions=result.get('exclusions'), flags=result.get('flags'))
        groups.setdefault(case['cell_id'], []).append(entry)
    result = []
    for cell, entries in groups.items():
        complete = len(entries) == (expected_counts.get(cell, 0) if expected_counts is not None else 12)
        valid = complete and all(entry['valid'] for entry in entries)
        result.append(dict(cell_id=cell, completed_evaluations=len(entries), complete=complete,
            all_estimable=bool(valid and all(e['all_estimable'] for e in entries)),
            worst_estimability_margin=min(e['margin'] for e in entries) if valid else None,
            worst_contrast_information=min(e['information'] for e in entries) if valid else None,
            all_rank2_stable=bool(complete and all(e['rank'] == 2 and e['rank_stable'] for e in entries)),
            evaluations=entries))
    return sorted(result, key=lambda row: (-int(row['all_estimable']),
        -(row['worst_estimability_margin'] if row['worst_estimability_margin'] is not None else -math.inf),
        -(row['worst_contrast_information'] if row['worst_contrast_information'] is not None else -math.inf), row['cell_id']))


def child_case(output, case, config, allocation):
    request, response = output/'case-input.json', output/'case-output.json'
    atomic_json(request, dict(case=case, config=config))
    response.unlink(missing_ok=True)
    command = [sys.executable, str(Path(__file__).resolve()), '--case-input', str(request), '--case-output', str(response)]
    process = subprocess.Popen(command, cwd=ROOT)
    try:
        process.wait(timeout=allocation)
        if process.returncode != 0:
            return dict(failure=f'geometry subprocess exited {process.returncode}')
        return json.loads(response.read_text())
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2.)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def run_campaign(output, config, resume=False, runner=child_case):
    output.mkdir(parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('geometry worker already active') from None
        manifest, path = freeze_manifest(config), output/'manifest.json'
        if path.exists():
            if not resume or json.loads(path.read_text()) != manifest:
                raise ValueError('resume requires unchanged source, environment, inputs and budget')
        else:
            if resume or (output/'records.jsonl').exists():
                raise ValueError('cannot recover missing manifest')
            atomic_json(path, manifest)
            (output/'records.jsonl').touch()
            atomic_json(output/'budget.json', dict(charged_s=0., reserved_s=0.))
        rows = load_records(output/'records.jsonl', config, manifest['manifest_hash'])
        budget_path = output/'budget.json'
        budget = json.loads(budget_path.read_text())
        # A crash cannot create extra budget. Unsettled reservations remain fully charged.
        budget['charged_s'] += budget.pop('reserved_s', 0.)
        budget['reserved_s'] = 0.
        if not math.isfinite(budget['charged_s']) or not 0 <= budget['charged_s'] <= config['wall_time_cap_s']:
            raise ValueError('invalid cumulative budget checkpoint')
        atomic_json(budget_path, budget)

        def status(state, error=None):
            atomic_json(output/'status.json', dict(state=state, updated_utc=datetime.now(timezone.utc).isoformat(),
                pid=os.getpid(), completed_evaluations=len(rows), requested_evaluations=len(config['cases']),
                failures=sum(bool(row['result'].get('failure')) for row in rows),
                completed_cells=dict(Counter(row['case']['cell_id'] for row in rows)),
                charged_s=budget['charged_s'], reserved_s=budget['reserved_s'],
                wall_time_cap_s=config['wall_time_cap_s'], manifest_hash=manifest['manifest_hash'], error=error))

        def check_freeze():
            current = (plan(config['wall_time_cap_s'], config['protocol_plan_path'])
                       if config.get('protocol_plan_path') else plan(config['wall_time_cap_s']))
            if (current != config or freeze_manifest(config) != manifest):
                raise RuntimeError('source, environment, runner or geometry inputs changed')

        state, error = 'running', None
        status(state)
        try:
            with (output/'records.jsonl').open('a') as journal:
                for case in config['cases'][len(rows):]:
                    check_freeze()
                    allocation = min(config['case_time_cap_s'], config['wall_time_cap_s']-budget['charged_s'])
                    if allocation <= 0:
                        state = 'budget_exhausted'
                        break
                    budget['reserved_s'] = allocation
                    atomic_json(budget_path, budget)
                    started = time.monotonic()
                    try:
                        result = runner(output, case, config, allocation)
                    except subprocess.TimeoutExpired:
                        if allocation < config['case_time_cap_s']:
                            state = 'budget_exhausted'
                            break  # Incomplete last case can resume only with remaining authorized budget.
                        result = dict(failure='preregistered 300-second case deadline reached')
                    check_freeze()
                    row = dict(case=case, result=plain(result), manifest_hash=manifest['manifest_hash'],
                               elapsed_s=time.monotonic()-started)
                    journal.write(json.dumps(row, allow_nan=False, separators=(',', ':'))+'\n')
                    journal.flush()
                    os.fsync(journal.fileno())
                    rows.append(row)
                    budget['charged_s'] += min(allocation, time.monotonic()-started)
                    budget['reserved_s'] = 0.
                    atomic_json(budget_path, budget)
                    status('running')
                    print(f'{len(rows)}/{len(config["cases"])} geometry evaluations checkpointed', flush=True)
                else:
                    state = 'complete'
        except BaseException as exc:
            state = 'interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'failed'
            error = repr(exc)
            raise
        finally:
            # Any interrupted/timeout case consumes its entire pre-reserved slice.
            budget['charged_s'] += budget['reserved_s']
            budget['reserved_s'] = 0.
            atomic_json(budget_path, budget)
            atomic_json(output/'summary.json', dict(partition='development', state=state,
                manifest_hash=manifest['manifest_hash'], completed_evaluations=len(rows),
                score_order=['all_estimable', 'worst_estimability_margin', 'worst_contrast_information'],
                geometry_scores=scores(rows, Counter(c['cell_id'] for c in config['cases'])),
                evidence_scope='Paired development geometry screening; no calibrated power, tail guarantee or real IMU evidence.'))
            archive(output/'records.jsonl')
            status(state, error)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--wall-time-minutes', type=float)
    parser.add_argument('--protocol-plan', type=Path, help='frozen development protocol comparison input')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--case-input', type=Path)
    parser.add_argument('--case-output', type=Path)
    args = parser.parse_args()
    if args.case_input:
        request = json.loads(args.case_input.read_text())
        atomic_json(args.case_output, evaluate(request['case'], request['config']))
        return
    if args.wall_time_minutes is None:
        parser.error('--wall-time-minutes is required and must match the authorized cap')
    config = plan(args.wall_time_minutes*60., args.protocol_plan)
    if args.detach:
        args.output.mkdir(parents=True, exist_ok=True)
        existing = args.output/'manifest.json'
        if existing.exists() and (not args.resume or json.loads(existing.read_text()) != freeze_manifest(config)):
            raise ValueError('existing campaign requires its unchanged freeze and --resume')
        with (args.output/'run.lock').open('a') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('geometry worker already active') from None
        command = [sys.executable, str(Path(__file__).resolve()), '--output', str(args.output.resolve()),
                   '--wall-time-minutes', str(args.wall_time_minutes)]
        if args.resume:
            command.append('--resume')
        if args.protocol_plan:
            command.extend(['--protocol-plan', str(args.protocol_plan.resolve())])
        with (args.output/'worker.log').open('ab') as log:
            worker = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        atomic_json(args.output/'launch.json', dict(pid=worker.pid, command=command,
            launched_utc=datetime.now(timezone.utc).isoformat()))
        print(json.dumps(dict(pid=worker.pid, output=str(args.output))))
        return
    def interrupt(*_):
        raise KeyboardInterrupt('geometry worker interrupted')
    signal.signal(signal.SIGINT, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    run_campaign(args.output, config, args.resume)


if __name__ == '__main__':
    main()
