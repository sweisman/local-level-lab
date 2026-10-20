# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen, finite recorded scalar-envelope assessment; no observed fits."""
import argparse
import csv
import fcntl
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'analysis'))
from lll.ilvis0_receipt_journal import durable_write, encoded

NAME = 'ilvis0-channel-envelopes-20261019'
DATA = ROOT/'data'/NAME
PUBLIC = ROOT/'docs'/NAME
PARENT = ROOT/'docs/ilvis0-horizontal-observed-20261018'
LIMITS = dict(diagnostic_identities=170, original_extractions=2, operator_batches=24,
    maximum_receiver_operators=6144, candidate_identities=144, maximum_force_boxes=36864,
    maximum_packets_per_identity=256, optimizer_starts=0, native_evaluations=0,
    numerical_threads=4, maximum_wall_s=1800, retries=0)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def load(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())


def plain(value):
    if isinstance(value, dict): return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [plain(v) for v in value]
    if hasattr(value, 'tolist'): return value.tolist()
    return value


def write(path, value, *, replace=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = encoded(plain(value))
    if path.suffix == '.gz': payload = gzip.compress(payload, mtime=0)
    durable_write(path, payload, replace=replace)


def environment():
    return dict(python=sys.version, executable=sys.executable,
        packages={name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'pytest')})


def tasks(selected):
    result = []
    for row in selected:
        sid = row['segment']['segment_id']
        result.append(dict(identity=sid+'--extract', kind='extract', segment_id=sid))
        for fraction in range(3):
            for clock in ('nominal', 'header'):
                for metres in (1, 5):
                    batch = f'{sid}--f{fraction}--{clock}--r{metres}'
                    common = dict(segment_id=sid, fraction=fraction, clock=clock, receiver_error_m=metres)
                    result.append(dict(identity=batch, kind='batch', **common))
                    for calibration in ('narrow', 'broad'):
                        for model in ('sphere_rotating', 'sphere_still', 'flat_still'):
                            result.append(dict(identity=batch+'--'+calibration+'--'+model,
                                kind='candidate', batch=batch, calibration=calibration, model=model, **common))
    return result


def numerical_modules():
    # Import only documented project modules, under run_numerical.py's guard.
    from lll import ilvis0_channel_envelope, ilvis0_segments
    return ilvis0_channel_envelope, ilvis0_segments


def prepare():
    if (DATA/'manifest.json').exists(): return verify()
    numerical_modules()
    parent = load(PARENT/'manifest.json')
    if {r['segment']['segment_id'] for r in parent['selected']} != {
            'b365bdf39150ee6afc303ac1', '7df21c836bec5751f83c0cce'}:
        raise ValueError('exact two preselected development stretches required')
    receipt = load(PARENT/'evidence-receipt.json')
    if receipt['artifacts']['manifest.json'] != sha(PARENT/'manifest.json'):
        raise ValueError('parent manifest not sealed')
    files = {str(Path(module.__file__).resolve().relative_to(ROOT))
        for name, module in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(module, '__file__', None)
        and Path(module.__file__).resolve().is_relative_to(ROOT)}
    files.update(['analysis/tests/ilvis0_channel_envelope_worker.py', 'analysis/tests/run_numerical.py',
        'analysis/tests/test_ilvis0_channel_envelope.py', 'analysis/tests/test_ilvis0_channel_envelope_worker.py',
        'docs/'+NAME+'/PLAN.md'])
    sources = {name: sha(ROOT/name) for name in sorted(files)}
    inputs = {str((PARENT/name).relative_to(ROOT)): sha(PARENT/name)
        for name in ('manifest.json', 'evidence-receipt.json')}
    for name in sources:
        target = DATA/'source-freeze'/name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
    manifest = dict(version='recorded-scalar-envelopes-v1', environment=environment(), sources=sources,
        inputs=inputs, selected=parent['selected'], contexts=parent['contexts'], originals=parent['originals'],
        tasks=tasks(parent['selected']), limits=LIMITS, scientific_decision='abstain')
    write(DATA/'manifest.json', manifest)
    write(DATA/'authorization.json', dict(manifest_sha256=sha(DATA/'manifest.json'), **LIMITS))
    return verify()


def verify():
    manifest = load(DATA/'manifest.json')
    if manifest['environment'] != environment() or manifest['limits'] != LIMITS or manifest['tasks'] != tasks(manifest['selected']):
        raise ValueError('environment, finite tasks or allowance changed')
    if load(DATA/'authorization.json') != dict(manifest_sha256=sha(DATA/'manifest.json'), **LIMITS):
        raise ValueError('authorization changed')
    for name, digest in manifest['sources'].items():
        if sha(ROOT/name) != digest or sha(DATA/'source-freeze'/name) != digest:
            raise ValueError('frozen source changed: '+name)
    for name, digest in manifest['inputs'].items():
        if sha(ROOT/name) != digest: raise ValueError('frozen input changed: '+name)
    return manifest


def evaluate(task, manifest, counts):
    import numpy as np
    channel, segments = numerical_modules()
    sid = task['segment_id']
    selected = next(r for r in manifest['selected'] if r['segment']['segment_id'] == sid)
    def tick(kind):
        if counts[kind] >= LIMITS['maximum_packets_per_identity']:
            raise ValueError('frozen per-identity calculation allowance exceeded')
        counts[kind] += 1
    if task['kind'] == 'extract':
        source = Path(selected['source_path'])
        if sha(source) != manifest['originals'][str(source)]: raise ValueError('compressed original hash mismatch')
        values, times, gps, provenance = segments.extract_segment(source,
            manifest['contexts'][selected['task']], selected['segment'])
        origin = provenance['first_interval_start_utc_s']
        # Cache only packet offsets, timestamps, periods and three delta-V counts.
        cache = dict(values=values[:, :6], times=times+origin, coordinates=gps, provenance=provenance)
        path = DATA/'cache'/(sid+'.json.gz'); write(path, cache)
        return dict(supported=True, cache_sha256=sha(path), provenance=provenance,
            original_extractions=1, operators=0, force_boxes=0)
    extraction = load(DATA/'results'/(sid+'--extract.json.gz'))
    if not extraction.get('supported'): return dict(supported=False, reason='source_extraction_unavailable', operators=0, force_boxes=0)
    cache_path = DATA/'cache'/(sid+'.json.gz')
    if sha(cache_path) != extraction['cache_sha256']: raise ValueError('extracted input changed')
    cache = load(cache_path); values = np.asarray(cache['values'])
    if task['kind'] == 'batch':
        center = channel.centers(selected['segment'])[task['fraction']]
        result = channel.prepare_jets(values, cache['times'], cache['coordinates'], center,
            task['clock'], task['receiver_error_m'], on_operator=lambda: tick('operators'))
        if result['supported']:
            packets = values[result['support']['packet_indices']]
            result['packets'] = [dict(packet_offset=int(row[0]), time_utc_s=float(row[1]),
                header_period_s=float(row[2]), raw_dv=[int(x) for x in row[3:6]]) for row in packets]
        return dict(result, center_utc_s=center, force_boxes=0)
    batch = load(DATA/'results'/(task['batch']+'.json.gz'))
    if not batch.get('supported'): return dict(supported=False, reason='receiver_batch_unavailable', operators=0, force_boxes=0)
    return dict(channel.assess(values, batch, model=task['model'], calibration=task['calibration'],
        velocity_scale=cache['provenance']['velocity_scale_mps_per_count'], on_force=lambda: tick('force_boxes')), operators=0)


def run():
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (DATA/'completion.json').exists(): raise ValueError('completed assessment cannot restart')
        manifest = verify(); started = time.time()
        if not (DATA/'start.json').exists():
            write(DATA/'start.json', dict(manifest_sha256=sha(DATA/'manifest.json'), started_at=started, pid=os.getpid()))
        def timeout(*_): raise TimeoutError('frozen wall allowance exhausted')
        elapsed = time.time()-load(DATA/'start.json')['started_at']
        if elapsed >= LIMITS['maximum_wall_s']:
            raise ValueError('frozen overall wall allowance expired; no new identities')
        signal.signal(signal.SIGALRM, timeout); signal.alarm(max(1, int(LIMITS['maximum_wall_s']-elapsed)))
        rows = []
        try:
            for task in manifest['tasks']:
                identity = task['identity']; target = DATA/'results'/(identity+'.json.gz')
                charge = DATA/'charges'/(identity+'.json')
                if not target.exists():
                    interrupted = charge.exists()
                    if not interrupted:
                        write(charge, dict(identity=identity, manifest_sha256=sha(DATA/'manifest.json'), charged_at=time.time()))
                    counts = dict(operators=None if interrupted and task['kind']=='batch' else 0,
                        force_boxes=None if interrupted and task['kind']=='candidate' else 0)
                    try:
                        result = dict(supported=False, reason='interrupted_charged_identity_no_retry') if interrupted else evaluate(task, manifest, counts)
                    except Exception as error:
                        result = dict(supported=False, reason='evaluation_failure', error=type(error).__name__+': '+str(error))
                    write(target, {**task, **result, **counts, 'scientific_decision':'abstain'})
                result = load(target)
                rows.append(dict(task, artifact=str(target.relative_to(DATA)), artifact_sha256=sha(target),
                    supported=result.get('supported', False), operators=result.get('operators', 0), force_boxes=result.get('force_boxes', 0)))
                if sum(r['operators'] if r['operators'] is not None else 256 for r in rows) > LIMITS['maximum_receiver_operators'] or sum(r['force_boxes'] if r['force_boxes'] is not None else 256 for r in rows) > LIMITS['maximum_force_boxes']:
                    raise ValueError('finite calculation allowance exceeded')
                write(DATA/'status.json', dict(state='running', completed_tasks=len(rows), total_tasks=len(manifest['tasks']),
                    current_identity=identity, pid=os.getpid(), numerical_threads=4, updated_at=time.time()), replace=True)
            summary = dict(state='complete', results=rows, completed_tasks=len(rows), total_tasks=len(manifest['tasks']),
                receiver_operators=sum(r['operators'] or 0 for r in rows), force_boxes=sum(r['force_boxes'] or 0 for r in rows),
                unknown_calculation_counts=sum(r['operators'] is None or r['force_boxes'] is None for r in rows),
                elapsed_s=time.time()-started, optimizer_starts=0, native_evaluations=0, scientific_decision='abstain')
            write(DATA/'summary.json', summary)
            write(DATA/'completion.json', dict(manifest_sha256=sha(DATA/'manifest.json'), summary_sha256=sha(DATA/'summary.json'), completed_at=time.time()))
            write(DATA/'status.json', dict(state='complete', completed_tasks=len(rows), total_tasks=len(rows), numerical_threads=0), replace=True)
        finally: signal.alarm(0)
    publish()


def publish():
    completion = load(DATA/'completion.json'); summary = load(DATA/'summary.json')
    if completion['manifest_sha256'] != sha(DATA/'manifest.json') or completion['summary_sha256'] != sha(DATA/'summary.json'):
        raise ValueError('completed manifest or summary changed')
    names = ['manifest.json', 'authorization.json', 'start.json', 'summary.json', 'completion.json']
    results = []
    for row in summary['results']:
        if sha(DATA/row['artifact']) != row['artifact_sha256']: raise ValueError('result changed')
        names.extend([row['artifact'], 'charges/'+row['identity']+'.json'])
        result = load(DATA/row['artifact'])
        if row['kind'] == 'candidate': results.append(result)
    for name in names:
        target = PUBLIC/name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(DATA/name, target)
    shutil.copytree(DATA/'source-freeze', PUBLIC/'source-freeze', dirs_exist_ok=True)
    fields = ['segment_id','fraction','clock','receiver_error_m','calibration','model','supported','reason','relation',
        'packet_count','integration_duration_s','measured_lower_mps2','measured_upper_mps2',
        'predicted_lower_mps2','predicted_upper_mps2','minimum_gap_mps2','scientific_decision']
    with (PUBLIC/'envelopes.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n'); writer.writeheader()
        for row in results:
            record = {key: row.get(key, '') for key in fields}
            for label in ('measured','predicted'):
                bounds = row.get(label+'_bounds_mps2', ['', ''])
                record[label+'_lower_mps2'], record[label+'_upper_mps2'] = bounds
            writer.writerow(record)
    counts = {label: sum(r.get('relation') == label for r in results) for label in ('overlap','disjoint','unsupported')}
    unsupported = sum(not r.get('supported') for r in results)
    lines = ['# Recorded acceleration-only envelopes', '',
        f"Completed {len(summary['results'])}/170 diagnostic identities in {summary['elapsed_s']:.2f} seconds: "
        f"{summary['receiver_operators']} receiver operators and {summary['force_boxes']} force boxes. Zero optimizer starts or native integrations.", '',
        f"Identities with unknown interrupted calculation counts: {summary['unknown_calculation_counts']}.", '',
        f"Across 144 candidate identities: **{counts['overlap']} overlapping, {counts['disjoint']} disjoint, {unsupported} unsupported**.", '',
        'Overlap is non-exclusion by a necessary scalar constraint, not a complete feasible fit. '
        'Disjoint bounds apply only under the frozen physical/error hypotheses. No calibrated significance or new scientific decision follows.', '',
        'The complete-observation comparison still favors globe on all 53 stretches. This diagnostic uses no gyro or fused-attitude observations, '
        'and does not relabel prior horizontal-only sensitivity failures.', '',
        '[All envelopes](envelopes.csv) · [Frozen method and finite allowance](PLAN.md) · '
        '[Contribution overview](../ilvis0-measurement-contribution/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    names += ['PLAN.md', 'README.md', 'envelopes.csv']
    names += ['source-freeze/'+name for name in load(DATA/'manifest.json')['sources']]
    write(PUBLIC/'evidence-receipt.json', dict(artifacts={name: sha(PUBLIC/name) for name in names}), replace=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--run', action='store_true')
    parser.add_argument('--package-only', action='store_true'); args = parser.parse_args()
    if sum((args.prepare, args.run, args.package_only)) != 1: parser.error('choose one operation')
    if args.prepare or args.run:
        from lll.compute_budget import environment as guarded_environment
        if any(os.environ.get(key) != value for key, value in guarded_environment(threads=4).items()):
            parser.error('use run_numerical.py with one worker and four threads before numerical imports')
    if args.prepare: prepare(); print('Frozen 170 identities; no original-file reads or fits.')
    elif args.run: run(); print('Completed finite scalar-envelope assessment.')
    else: publish(); print('Published saved artifacts without numerical work.')


if __name__ == '__main__': main()
