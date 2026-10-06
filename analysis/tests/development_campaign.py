# SPDX-License-Identifier: AGPL-3.0-or-later
"""Checkpointed, resumable development flights; never calibration or validation evidence."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import fcntl
import gzip
import json
import math
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'analysis'), str(ROOT/'server')]
import research
from lll import __version__, models
from lll.inference_policy import INFERENCE_POLICY, digest
from lll.policy import POLICY_VERSION, CANDIDATE_POLICY, eligibility_policies
from lll.rank_sweep import sweep
from lll.research_design import freeze_manifest, implementation_hash, plain, protocol_geometry, realize, seed_range
from lll.runtime import numerical_environment, numerical_environment_hash

DEFAULT_OUTPUT = ROOT/'docs/development-1000-20261005'


def plan(flights=1000, first_seed=600100, rank_margin=0.):
    if flights < 1:
        raise ValueError('flight count must be positive')
    if not math.isfinite(rank_margin) or rank_margin < 0:
        raise ValueError('rank margin must be finite and nonnegative')
    seed_range('development', first_seed, (flights+5)//6)
    return dict(partition='development', requested_flights=flights, first_seed=first_seed,
        truths=list(models.MODELS), scenarios=['bias_mixed', 'wind'], variant='spp', geometry='fixed',
        protocol=protocol_geometry(json.loads((ROOT/'docs/development-protocol-75min.json').read_text())),
        fit_options=dict(n_boot=20, bootstrap_sampling='moving', block_length=15,
            crab_model='dynamic', noise_model='axis_segment', bootstrap_refit='nonlinear',
            crab_rate_sigma_dph=1., forward_uncertainty=True, crab_knot_seconds=None,
            research_candidate=True, bias_model='dynamic', bias_knot_seconds=INFERENCE_POLICY['bias_knot_seconds'],
            bias_rw_sigma_dph_sqrth=INFERENCE_POLICY['bias_rw_sigma_dph_sqrth'], rank_min_relative_margin=rank_margin),
        model_test_ranks=[1, 2, 3], pairwise_evidence=True,
        evidence_use='development only; no threshold estimation or independent validation')


def tasks(config):
    """Paired seeds interleaved across the six cells; no outcome-based stopping."""
    rows = []
    for seed in seed_range('development', config['first_seed'], (config['requested_flights']+5)//6):
        for truth in config['truths']:
            for scenario in config['scenarios']:
                if len(rows) == config['requested_flights']:
                    return rows
                rows.append((truth, scenario, seed))
    return rows


def atomic_json(path, data):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(plain(data), indent=2, allow_nan=False)+'\n')
    os.replace(temporary, path)


def archive(path):
    destination = path.with_suffix(path.suffix+'.gz')
    temporary = destination.with_suffix(destination.suffix+'.tmp')
    with path.open('rb') as source, gzip.open(temporary, 'wb', compresslevel=6) as output:
        shutil.copyfileobj(source, output)
    os.replace(temporary, destination)


def magnetic_summary(records):
    groups = {}
    for row in records:
        key = row['truth']+'/'+row['scenario']
        group = groups.setdefault(key, dict(attempts=0, flagged=0, excluded_bins=0,
            design_failures=0, unstable_rank=0, flagged_segments_without_airframe_calibration=0))
        group['attempts'] += 1
        group['flagged'] += 'mount_slip_detected' in row.get('flags', [])
        watchdog = row.get('slip') or {}
        group['excluded_bins'] += watchdog.get('excluded_bins', 0)
        group['design_failures'] += 'model contrast not identified' in row.get('exclusions', [])
        group['unstable_rank'] += 'unstable model-test rank' in row.get('exclusions', [])
        variant = watchdog.get('variants', {}).get(watchdog.get('decided_by'), [])
        group['flagged_segments_without_airframe_calibration'] += sum(
            item['slip'] and not item['airframe_field_calibrated'] for item in variant)
    return dict(partition='development', cells=groups,
        note='Magnetic rates are apparent yaw change, not confirmed mount slip; no thresholds estimated.')


def load_records(path, config):
    rows, expected = [], tasks(config)
    if not path.exists():
        return rows
    offset, incomplete_tail, needs_newline = 0, None, False
    with path.open('rb') as source:
        for index, line in enumerate(source):
            try:
                row = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                if line.endswith(b'\n'):
                    raise ValueError('malformed completed checkpoint; inspect it before resuming') from None
                incomplete_tail = line
                break
            if index >= len(expected) or (row.get('truth'), row.get('scenario'), row.get('seed')) != expected[index]:
                raise ValueError('checkpoint order, duplicate or task mismatch')
            if (row.get('partition') != 'development' or row.get('replay') or
                    row.get('candidate_id') != digest(config['fit_options']) or
                    row.get('fit_options') != config['fit_options'] or
                    row.get('numerical_environment') != numerical_environment()):
                raise ValueError('checkpoint provenance mismatch')
            rows.append(row)
            offset += len(line)
            needs_newline = not line.endswith(b'\n')
    if incomplete_tail is not None:
        # Preserve every byte before repairing only an uncommitted final write.
        with (path.parent/'recovery.jsonl').open('a') as recovery:
            recovery.write(json.dumps(dict(offset=offset, discarded_base64=base64.b64encode(incomplete_tail).decode(),
                                           recovered_utc=datetime.now(timezone.utc).isoformat()))+'\n')
            recovery.flush()
            os.fsync(recovery.fileno())
        with path.open('r+b') as checkpoints:
            checkpoints.truncate(offset)
            checkpoints.flush()
            os.fsync(checkpoints.fileno())
    elif needs_newline:
        with path.open('ab') as checkpoints:
            checkpoints.write(b'\n')
            checkpoints.flush()
            os.fsync(checkpoints.fileno())
    return rows


def run_campaign(output, config, resume=False, flight_runner=None):
    output.mkdir(parents=True, exist_ok=True)
    with (output/'run.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('this campaign already has an active worker') from None
        manifest_path, records_path = output/'manifest.json', output/'records.jsonl'
        manifest = freeze_manifest(config)
        if manifest_path.exists():
            if not resume:
                raise ValueError('campaign exists; use --resume to retain every recorded attempt')
            if json.loads(manifest_path.read_text()) != manifest:
                raise ValueError('source, environment or configuration changed; cannot resume this campaign')
        else:
            if resume or records_path.exists():
                raise ValueError('cannot resume without the original manifest')
            atomic_json(manifest_path, manifest)
        records = load_records(records_path, config)
        pending = tasks(config)[len(records):]
        started = time.monotonic()
        accumulated = sum(row.get('elapsed_s', 0.) for row in records)
        last = None
        runner = research.flight_run if flight_runner is None else flight_runner

        def status(state, error=None):
            atomic_json(output/'status.json', dict(state=state, pid=os.getpid(),
                updated_utc=datetime.now(timezone.utc).isoformat(), requested_flights=config['requested_flights'],
                completed_flights=len(records), remaining_flights=config['requested_flights']-len(records),
                completed_cells=dict(Counter(row['truth']+'/'+row['scenario'] for row in records)),
                analysis_failures=sum(bool(row.get('failure')) for row in records),
                accepted_flights=sum(not row.get('exclusions') and row.get('rejected') is not None for row in records),
                rank_counts=dict(Counter(row.get('model_test_rank') for row in records)),
                prior_fit_seconds=accumulated, current_worker_seconds=time.monotonic()-started,
                manifest_hash=manifest['manifest_hash'], last_task=last, error=error))

        def check_frozen_source():
            if (implementation_hash() != manifest['implementation_hash'] or
                    numerical_environment_hash() != manifest['numerical_environment_hash']):
                raise RuntimeError('scientific source or numerical environment changed during the campaign')

        status('running')
        try:
            with records_path.open('a') as checkpoints:
                for truth, scenario, seed in pending:
                    check_frozen_source()
                    last = dict(truth=truth, scenario=scenario, seed=seed)
                    design = realize(seed, scenario, partition='development', geometry='fixed',
                                     variant=config['variant'], protocol=config['protocol'])
                    options = config['fit_options']
                    row = runner(truth, scenario, seed, options['bootstrap_sampling'], options['block_length'],
                                 options['n_boot'], config['variant'], partition='development', geometry='fixed',
                                 fit_options={key: value for key, value in options.items()
                                              if key not in ('n_boot', 'bootstrap_sampling', 'block_length')}, design=design)
                    check_frozen_source()
                    checkpoints.write(json.dumps(plain(row), separators=(',', ':'), allow_nan=False)+'\n')
                    checkpoints.flush()
                    os.fsync(checkpoints.fileno())
                    records.append(row)
                    status('running')
                    if len(records) % 25 == 0:
                        print(f'{len(records)}/{config["requested_flights"]} attempts checkpointed', flush=True)
            campaign = dict(partition='development', analysis_version=__version__, policy_version=POLICY_VERSION,
                implementation_hash=manifest['implementation_hash'], manifest=manifest, manifest_hash=manifest['manifest_hash'],
                eligibility_policies=eligibility_policies(), numerical_environment=numerical_environment(),
                numerical_environment_hash=numerical_environment_hash(), config=config, records=records,
                elapsed_s=accumulated+time.monotonic()-started,
                summary=research.summarize(records),
                simulation_assumption='approved provenance and usable bench tier; remaining gates applied')
            atomic_json(output/'campaign.json', campaign)
            atomic_json(output/'rank-sweep.json', sweep(campaign))
            cutoff = CANDIDATE_POLICY['retention_threshold']
            atomic_json(output/'rank-sweep-narrow.json', sweep(campaign, [cutoff*f for f in (.9, 1., 1.1)]))
            atomic_json(output/'magnetic-summary.json', magnetic_summary(records))
            archive(output/'campaign.json')
            archive(records_path)
            status('complete')
            print(f'Completed {len(records)} development attempts; {output}', flush=True)
        except BaseException as exc:
            status('interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'failed', repr(exc))
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--flights', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=600100)
    parser.add_argument('--rank-min-relative-margin', type=float, default=0.)
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--detach', action='store_true', help='start a background worker with a durable log')
    args = parser.parse_args()
    config = plan(args.flights, args.seed, args.rank_min_relative_margin)
    if args.detach:
        args.output.mkdir(parents=True, exist_ok=True)
        existing = args.output/'manifest.json'
        if existing.exists() and (not args.resume or json.loads(existing.read_text()) != freeze_manifest(config)):
            raise ValueError('existing campaign needs --resume with its unchanged source/environment/configuration')
        command = [sys.executable, str(Path(__file__).resolve()), '--output', str(args.output.resolve()),
                   '--flights', str(args.flights), '--seed', str(args.seed),
                   '--rank-min-relative-margin', str(args.rank_min_relative_margin)]
        if args.resume:
            command.append('--resume')
        with (args.output/'worker.log').open('ab') as log:
            worker = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
        atomic_json(args.output/'launch.json', dict(pid=worker.pid, command=command,
            launched_utc=datetime.now(timezone.utc).isoformat(), numerical_environment=numerical_environment()))
        print(json.dumps(dict(pid=worker.pid, output=str(args.output.resolve()), requested_flights=args.flights)))
        return
    def interrupted(*_):
        raise KeyboardInterrupt('campaign interrupted; completed attempts remain checkpointed')
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    run_campaign(args.output, config, args.resume)


if __name__ == '__main__':
    main()
