# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite whole-history scalar constraints, using sealed extraction caches."""
import argparse
import csv
import fcntl
import gzip
import os
from pathlib import Path
import shutil
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'analysis'))
from ilvis0_channel_envelope_worker import sha, load, write, environment

NAME = 'ilvis0-channel-history-v2-20261019'
DATA = ROOT/'data'/NAME
PUBLIC = ROOT/'docs'/NAME
PARENT = ROOT/'docs/ilvis0-channel-envelopes-20261019'
BASE = ROOT/'docs/ilvis0-current-findings-20261015'
LIMITS = dict(maximum_groups=840, maximum_identities=3360, maximum_receiver_operators=3360,
    maximum_force_boxes=10080, maximum_scalar_comparisons=30240, numerical_threads=4,
    maximum_wall_s=1800, optimizer_starts=0, native_evaluations=0, original_reads=0, retries=0)


class Deadline(BaseException):
    pass


def require_unfinished():
    if (DATA/'completion.json').exists() or (DATA/'terminal.json').exists():
        raise ValueError('completed/terminal study cannot restart')


def identities(inventories):
    tasks = []
    for sid, selected in sorted(inventories.items()):
        for group in selected['groups']:
            if not group['eligible']: continue
            for clock in ('nominal', 'header'):
                for metres in (1, 5):
                    tasks.append(dict(identity=f'{sid}--g{group["group_index"]:04d}--{clock}--r{metres}',
                        segment_id=sid, group=group, clock=clock, receiver_error_m=metres))
    if len(tasks) > LIMITS['maximum_identities']: raise ValueError('finite identity cap exceeded')
    return tasks


def prepare():
    if (DATA/'manifest.json').exists(): return verify()
    from lll import ilvis0_history_envelope as science
    import numpy as np
    receipt = load(PARENT/'evidence-receipt.json')
    for name, digest in receipt['artifacts'].items():
        if sha(PARENT/name) != digest: raise ValueError('changed predecessor evidence')
    parent = load(PARENT/'manifest.json'); inventories = {}; inputs = {}; caches = {}; provenance = {}
    ledger_path = ROOT/'docs/analysis-provenance/ledger.json'; ledger = load(ledger_path)
    for row in parent['selected']:
        sid = row['segment']['segment_id']; extraction_path = PARENT/'results'/(sid+'--extract.json.gz')
        record = next(r for r in ledger['records'] if r['record_id']=='ilvis0:'+sid)
        if record['role'] != 'retrospective_development': raise ValueError('development provenance required')
        provenance[sid] = record
        extraction = load(extraction_path)
        source = ROOT/'data/ilvis0-channel-envelopes-20261019/cache'/(sid+'.json.gz')
        if not extraction['supported'] or sha(source) != extraction['cache_sha256']:
            raise ValueError('sealed extracted cache required')
        cache = load(source)
        inventories[sid] = science.inventory(np.asarray(cache['values']), cache['times'], row['segment'])
        target = DATA/'input-freeze'/(sid+'.json.gz'); target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target); caches[sid] = sha(target)
        for path in (source, extraction_path): inputs[str(path.relative_to(ROOT))] = sha(path)
    if sum(len(r['groups']) for r in inventories.values()) > LIMITS['maximum_groups']:
        raise ValueError('finite inventory cap exceeded')
    tasks = identities(inventories)
    for path in (PARENT/'manifest.json', PARENT/'evidence-receipt.json',
                 BASE/'findings-receipt.json', BASE/'current-stretches.csv', ledger_path):
        inputs[str(path.relative_to(ROOT))] = sha(path)
    baseline = load(BASE/'findings-receipt.json')
    if sha(BASE/'current-stretches.csv') != baseline['artifacts']['current-stretches.csv']:
        raise ValueError('baseline publication changed')
    files = {str(Path(module.__file__).resolve().relative_to(ROOT)) for name, module in tuple(sys.modules.items())
        if name.startswith('lll') and getattr(module, '__file__', None) and Path(module.__file__).resolve().is_relative_to(ROOT)}
    files.update(['analysis/tests/ilvis0_history_envelope_worker.py', 'analysis/tests/ilvis0_channel_envelope_worker.py',
        'analysis/tests/run_numerical.py', 'analysis/tests/test_ilvis0_history_envelope.py',
        'analysis/tests/test_ilvis0_history_envelope_worker.py', 'analysis/tests/test_ilvis0_channel_envelope.py',
        'analysis/tests/test_ilvis0_channel_envelope_worker.py', 'docs/'+NAME+'/PLAN.md'])
    sources = {name: sha(ROOT/name) for name in sorted(files)}
    for name in sources:
        target = DATA/'source-freeze'/name; target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/name, target)
    manifest = dict(version='whole-history-scalar-envelopes-v1', sources=sources, inputs=inputs, caches=caches,
        selected=parent['selected'], inventories=inventories, provenance=provenance, environment=environment(), limits=LIMITS,
        plan=dict(tasks=tasks, numerical_threads=4), scientific_decision='abstain')
    write(DATA/'manifest.json', manifest)
    write(DATA/'authorization.json', dict(manifest_sha256=sha(DATA/'manifest.json'), **LIMITS))
    return verify()


def verify():
    manifest = load(DATA/'manifest.json')
    if manifest['environment'] != environment() or manifest['limits'] != LIMITS:
        raise ValueError('frozen environment or allowance changed')
    if manifest['plan']['tasks'] != identities(manifest['inventories']): raise ValueError('frozen identities changed')
    if load(DATA/'authorization.json') != dict(manifest_sha256=sha(DATA/'manifest.json'), **LIMITS):
        raise ValueError('finite authorization changed')
    for name, digest in manifest['sources'].items():
        if sha(ROOT/name) != digest or sha(DATA/'source-freeze'/name) != digest: raise ValueError('frozen source changed: '+name)
    for name, digest in manifest['inputs'].items():
        if sha(ROOT/name) != digest: raise ValueError('frozen input changed: '+name)
    for sid, digest in manifest['caches'].items():
        if sha(DATA/'input-freeze'/(sid+'.json.gz')) != digest: raise ValueError('input snapshot changed')
    return manifest


def evaluate(task, cache, counts):
    from lll import ilvis0_history_envelope as science
    def tick(kind, limit):
        if counts[kind] >= limit: raise ValueError('per-identity calculation allowance exceeded')
        counts[kind] += 1
    batch = science.prepare_group(cache['values'], cache['times'], cache['coordinates'], task['group'],
        task['clock'], task['receiver_error_m'], on_operator=lambda: tick('operators', 1))
    models = {}
    if batch['supported']:
        for model in science.MODELS:
            try:
                models[model] = science.assess_group(cache['values'], batch, model=model,
                    velocity_scale=cache['provenance']['velocity_scale_mps_per_count'], on_force=lambda: tick('force_boxes', 3))
            except Exception as error:
                models[model] = dict(supported=False, reason='candidate_evaluation_failure', error=type(error).__name__+': '+str(error))
    return dict(batch=batch, models=models, supported=bool(batch['supported']) and all(r['supported'] for r in models.values()),
        reason=batch['reason'], scientific_decision='abstain')


def require_time(started, now):
    remaining = LIMITS['maximum_wall_s']-(now-started)
    if remaining <= 0.: raise Deadline('overall wall allowance exhausted')
    return max(1, int(remaining))


def run():
    import numpy as np
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA/'worker.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); require_unfinished(); manifest = verify()
        if not (DATA/'start.json').exists():
            write(DATA/'start.json', dict(manifest_sha256=sha(DATA/'manifest.json'), started_at=time.time(), pid=os.getpid()))
        started = load(DATA/'start.json')['started_at']; rows = []; caches = {}
        def timeout(*_): raise Deadline('overall wall allowance exhausted')
        signal.signal(signal.SIGALRM, timeout)
        try:
            signal.alarm(require_time(started, time.time()))
            for task in manifest['plan']['tasks']:
                require_time(started, time.time()); identity = task['identity']
                target = DATA/'results'/(identity+'.json.gz'); charge = DATA/'charges'/(identity+'.json')
                if not target.exists():
                    interrupted = charge.exists(); counts = dict(operators=None if interrupted else 0, force_boxes=None if interrupted else 0)
                    if interrupted:
                        result = dict(supported=False, reason='interrupted_charged_identity_no_retry')
                    else:
                        write(charge, dict(identity=identity, manifest_sha256=sha(DATA/'manifest.json'), charged_at=time.time()))
                        try:
                            sid = task['segment_id']
                            if sid not in caches:
                                cache = load(DATA/'input-freeze'/(sid+'.json.gz'))
                                for key in ('values', 'times', 'coordinates'):
                                    cache[key] = np.asarray(cache[key]); cache[key].setflags(write=False)
                                caches[sid] = cache
                            result = evaluate(task, caches[sid], counts)
                        except Exception as error:
                            result = dict(supported=False, reason='identity_evaluation_failure', error=type(error).__name__+': '+str(error))
                    write(target, {**task, **result, **counts})
                result = load(target)
                rows.append(dict(task, artifact=str(target.relative_to(DATA)), artifact_sha256=sha(target),
                    passed=result['supported'], reason=result['reason'], operators=result['operators'], force_boxes=result['force_boxes']))
                write(DATA/'status.json', dict(state='running', total=len(manifest['plan']['tasks']), identity=identity,
                    pid=os.getpid(), numerical_threads=4), replace=True)
                write(DATA/'progress.json', dict(completed=len(rows), passed=sum(r['passed'] for r in rows)), replace=True)
            summary = dict(state='complete', results=rows, receiver_operators=sum(r['operators'] or 0 for r in rows),
                force_boxes=sum(r['force_boxes'] or 0 for r in rows),
                unknown_calculation_counts=sum(r['operators'] is None or r['force_boxes'] is None for r in rows),
                elapsed_s=time.time()-started, native_evaluations=0, optimizer_starts=0, scientific_decision='abstain')
            write(DATA/'summary.json', summary)
            write(DATA/'completion.json', dict(state='complete', manifest_sha256=sha(DATA/'manifest.json'),
                summary_sha256=sha(DATA/'summary.json'), completed_at=time.time()))
            write(DATA/'status.json', dict(state='complete', total=len(rows), numerical_threads=0), replace=True)
        except Deadline as error:
            write(DATA/'terminal.json', dict(state='deadline', error=str(error), finished_identities=len(rows)))
            write(DATA/'status.json', dict(state='stopped', total=len(manifest['plan']['tasks']), numerical_threads=0), replace=True)
            raise
        finally: signal.alarm(0)
    publish()


def publish():
    from lll.ilvis0_history_envelope import shared_zero_check, MODELS
    completion = load(DATA/'completion.json'); summary = load(DATA/'summary.json'); manifest = load(DATA/'manifest.json')
    if completion['manifest_sha256'] != sha(DATA/'manifest.json') or completion['summary_sha256'] != sha(DATA/'summary.json'):
        raise ValueError('completed evidence changed')
    names = ['manifest.json','authorization.json','start.json','summary.json','completion.json']; histories = {}; records = []
    for row in summary['results']:
        if sha(DATA/row['artifact']) != row['artifact_sha256']: raise ValueError('sealed identity changed')
        names.extend([row['artifact'], 'charges/'+row['identity']+'.json']); result = load(DATA/row['artifact'])
        for model in MODELS:
            value = result.get('models', {}).get(model, dict(supported=False, reason=result['reason']))
            key = (row['segment_id'], row['clock'], row['receiver_error_m'], model)
            histories.setdefault(key, []).append(value)
            for calibration in ('zero','narrow','broad'):
                comparison = value.get('comparisons', {}).get(calibration, {})
                measured = comparison.get('measured_bounds_mps2', ['', '']); predicted = comparison.get('predicted_bounds_mps2', ['', ''])
                records.append(dict(segment_id=key[0], group_index=row['group']['group_index'], first_packet=row['group']['first_packet'],
                    clock=key[1], receiver_error_m=key[2], model=model, calibration=calibration,
                    supported=value['supported'], reason=value.get('reason'), relation=comparison.get('relation','unsupported'),
                    measured_lower_mps2=measured[0], measured_upper_mps2=measured[1], predicted_lower_mps2=predicted[0],
                    predicted_upper_mps2=predicted[1], minimum_gap_mps2=comparison.get('minimum_gap_mps2',''), scientific_decision='abstain'))
    shared = [dict(segment_id=key[0], clock=key[1], receiver_error_m=key[2], model=key[3], groups=len(values),
        **shared_zero_check(values)) for key, values in histories.items()]
    for name in names:
        target=PUBLIC/name; target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(DATA/name, target)
    for directory in ('source-freeze','input-freeze'): shutil.copytree(DATA/directory, PUBLIC/directory, dirs_exist_ok=True)
    groups = [dict(segment_id=sid, **{k:v for k,v in group.items() if k!='clock_spans_s'},
        nominal_start_s=group['clock_spans_s']['nominal'][0], nominal_end_s=group['clock_spans_s']['nominal'][1],
        header_start_s=group['clock_spans_s']['header'][0], header_end_s=group['clock_spans_s']['header'][1])
        for sid, inventory in manifest['inventories'].items() for group in inventory['groups']]
    for name, rows in [('envelopes.csv', records), ('groups.csv', groups), ('shared-zero.csv', shared)]:
        with (PUBLIC/name).open('w', newline='') as stream:
            writer=csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    write(PUBLIC/'shared-zero.json', shared, replace=True)
    overlaps = sum(r['relation']=='overlap' for r in records); disjoint=sum(r['relation']=='disjoint' for r in records)
    points = sum(r['zero_calibration_not_excluded_everywhere'] for r in shared)
    lines = ['# Whole-history acceleration-only constraints', '',
        f"Completed {len(summary['results'])} frozen identities in {summary['elapsed_s']:.2f} seconds: "
        f"{summary['receiver_operators']} receiver operators and {summary['force_boxes']} force boxes. Zero new fits, native integrations or original reads.", '',
        f"Scalar group cases: **{overlaps} overlap, {disjoint} disjoint, {len(records)-overlaps-disjoint} unsupported**. "
        f"A fixed zero gain/offset correction is not excluded in every assessed group for **{points}/{len(shared)}** recording/clock/receiver-error/candidate histories.", '',
        'This checks one common calibration point, with other uncertainty dependence relaxed. It does not establish a jointly feasible receiver trajectory, '
        'gravity/latency, orientation or full gyro-free reconstruction. It supplies no calibrated significance or new scientific decision.', '',
        '[All groups and exclusions](groups.csv) · [Every scalar case](envelopes.csv) · [Common-zero check](shared-zero.csv) · '
        '[Frozen method](PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    names += ['PLAN.md','README.md','envelopes.csv','groups.csv','shared-zero.csv','shared-zero.json']
    names += ['source-freeze/'+name for name in manifest['sources']]
    names += ['input-freeze/'+sid+'.json.gz' for sid in manifest['caches']]
    write(PUBLIC/'evidence-receipt.json', dict(artifacts={name:sha(PUBLIC/name) for name in names}), replace=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true'); parser.add_argument('--run', action='store_true')
    parser.add_argument('--package-only', action='store_true'); args=parser.parse_args()
    if sum((args.prepare,args.run,args.package_only)) != 1: parser.error('choose one operation')
    from lll.compute_budget import environment as guarded
    if any(os.environ.get(k)!=v for k,v in guarded(threads=4).items()): parser.error('use run_numerical.py with four threads')
    if args.prepare:
        m=prepare(); print('Frozen',len(m['plan']['tasks']),'identities; no force evaluation.')
    elif args.run: run(); print('Completed whole-history necessary-constraint assessment.')
    else: publish(); print('Published saved evidence only.')


if __name__=='__main__': main()
