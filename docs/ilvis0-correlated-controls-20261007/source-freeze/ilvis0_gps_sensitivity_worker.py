# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen six-file GPS-error sensitivity; no original rescan or Earth fits."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_gps_sensitivity as sensitivity, runtime
from ilvis0_gnss_worker import verify_cached


def load(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def run(root, output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked output; use a new owned directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = root/'docs/ilvis0-position-20261007'
        complete = load(prior/'completion.json')
        for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
            if il.sha256(prior/name) != complete[key]:
                raise ValueError('prior positioning evidence hash mismatch')
        old = load(prior/'manifest.json'); tasks = old['tasks']
        reports = {r['task_id']:r for r in load(prior/'summary.json.gz')['results']}
        if len(tasks) != 6 or sum(r['preselected_epochs'] for r in reports.values()) != 2968:
            raise ValueError('requires same six files and 2968 epochs')
        sources = dict(old['sources'])
        for path in (Path(sensitivity.__file__), Path(__file__),
                root/'analysis/tests/test_ilvis0_gps_sensitivity.py'):
            sources[str(path)] = il.sha256(path)
        inputs = dict(old['inputs'])
        for name in ('manifest.json', 'completion.json', 'summary.json.gz'):
            inputs[str(prior/name)] = il.sha256(prior/name)
        data = root/'data/ilvis0-position-20261007'
        for report in reports.values():
            for name, digest in report['artifacts_sha256'].items():
                inputs[str(data/name)] = digest
        manifest = dict(version=sensitivity.VERSION, sources=sources, inputs=inputs, tasks=tasks,
            environment=runtime.numerical_environment(), assumptions=[a.report() for a in sensitivity.assumptions()],
            window_seconds=list(sensitivity.WINDOW_SECONDS), maximum_epoch_gap_s=1.5,
            epochs=2968, selection='unchanged prior GPS epochs; every supported centered window; no residual selection',
            scope='assumed trajectory-error sensitivity, not calibrated covariance, an IMU fit or Earth comparison',
            covariance_calibrated=False, empirical_earth_fit_attempts=0,
            gnss_position_fits=0, scientific_eligibility_changes=0, originals_deleted=0)
        def verify():
            for name, digest in {**sources, **inputs}.items():
                if il.sha256(Path(name)) != digest:
                    raise ValueError('source/input changed; new freeze required')
            if runtime.numerical_environment() != manifest['environment']:
                raise ValueError('numerical environment mismatch')
        verify(); path = output/'manifest.json'
        if path.exists():
            if load(path) != manifest:
                raise ValueError('source/input/environment mismatch; new freeze required')
            if (output/'completion.json').exists():
                raise ValueError('completed sensitivity is frozen; do not resume')
        else:
            follow.atomic_json(path, manifest)
            snapshots = output/'source-freeze'; snapshots.mkdir()
            for name in sources:
                shutil.copyfile(name, snapshots/Path(name).name)
        results = []
        for task in tasks:
            verify()
            report = verify_cached(output, task, il.sha256(path))
            if report is None:
                follow.atomic_json(output/'status.json', dict(state='running', pid=os.getpid(),
                    completed=len(results), task_id=task['task_id']))
                report = sensitivity.run_file(task, reports[task['task_id']], data, output)
                verify()
                target = output/(task['task_id']+'.json.gz')
                observation.gzip_json(target, report)
                follow.atomic_json(output/(task['task_id']+'.receipt.json'), dict(
                    manifest_sha256=il.sha256(path), report_sha256=il.sha256(target)))
            results.append(report)
            print(json.dumps(dict(task_id=task['task_id'], epochs=report['epochs'],
                assumptions=len(report['assumptions']), complete=len(results))), flush=True)
        summary = dict(version=sensitivity.VERSION, state='complete', files=len(results),
            results=results, epochs=sum(r['epochs'] for r in results), assumptions=13,
            window_seconds=list(sensitivity.WINDOW_SECONDS), covariance_calibrated=False,
            source_audit_errors=0, empirical_earth_fit_attempts=0, gnss_position_fits=0,
            scientific_eligibility_changes=0, originals_deleted=0)
        verify(); observation.gzip_json(output/'summary.json.gz', summary)
        compact = {k:v for k,v in summary.items() if k != 'results'}
        compact.update(manifest_sha256=il.sha256(path), summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json', compact)
        follow.atomic_json(output/'status.json', dict(state='complete', files=len(results), pid=os.getpid()))
        print(json.dumps(compact, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-gps-sensitivity-20261007'))
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[2], args.output.resolve())
