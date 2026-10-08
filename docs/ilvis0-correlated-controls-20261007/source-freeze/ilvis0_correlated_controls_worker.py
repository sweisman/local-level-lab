# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen deterministic joint IMU/GPS covariance controls; no archival fits."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_correlated_controls as controls, ilvis0_estimator as estimator
from lll import ilvis0_estimator_controls as fixtures, ilvis0_gps_sensitivity as sensitivity, runtime


def load(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def result_hash(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()


def charge(path, task, manifest_digest, tasks):
    """Count interrupted control starts separately from the unused empirical ledger."""
    if task not in tasks:
        raise ValueError('unknown control task')
    with path.open('a+') as stream:
        stream.seek(0); records = [json.loads(line) for line in stream]
        if any(r.get('start') != i+1 or r.get('manifest_sha256') != manifest_digest or
                r.get('task') not in tasks or
                r.get('maximum_fit_evaluations') != controls.MAXIMUM_EVALUATIONS or
                r.get('maximum_precision_predictions') != 7 for i, r in enumerate(records)):
            raise ValueError('corrupt control start journal')
        if len(records) >= 2*len(tasks) or sum(r['task'] == task for r in records) >= 2:
            raise ValueError('control interruption retry allowance exhausted')
        record = dict(start=len(records)+1, task=task, manifest_sha256=manifest_digest,
            maximum_fit_evaluations=controls.MAXIMUM_EVALUATIONS, maximum_precision_predictions=7)
        stream.write(json.dumps(record, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
        descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def cached(path, task, manifest_digest):
    if not path.exists():
        return None
    saved = load(path)
    if saved.get('manifest_sha256') != manifest_digest or saved.get('task') != task or (
            saved.get('result_sha256') != result_hash(saved.get('result'))):
        raise ValueError('corrupt or incompatible completed control')
    return saved['result']


def run(root, output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked output; use new owned directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = root/'docs/ilvis0-gps-sensitivity-20261007'
        complete = load(prior/'completion.json')
        for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
            if il.sha256(prior/name) != complete[key]:
                raise ValueError('prior sensitivity evidence mismatch')
        old = load(prior/'manifest.json'); sources = dict(old['sources'])
        for module in (controls, estimator, fixtures):
            path = Path(module.__file__); sources[str(path)] = il.sha256(path)
        for path in (Path(__file__), root/'analysis/tests/test_ilvis0_correlated_controls.py'):
            sources[str(path)] = il.sha256(path)
        frozen_estimator = root/'docs/ilvis0-estimator-20261007/manifest.json'
        for name, digest in load(frozen_estimator)['sources'].items():
            if il.sha256(Path(name)) != digest:
                raise ValueError('frozen estimator dependency changed')
        inputs = {str(prior/name):il.sha256(prior/name)
            for name in ('manifest.json', 'completion.json', 'summary.json.gz')}
        inputs[str(frozen_estimator)] = il.sha256(frozen_estimator)
        grid = {a.name:a for a in sensitivity.assumptions()}
        tasks = {case+'__'+name:dict(case=case, assumption=name)
            for case in fixtures.CASES for name in grid}
        manifest = dict(version=controls.VERSION, sources=sources, inputs=inputs,
            environment=runtime.numerical_environment(), tasks=tasks, cases=fixtures.CASES,
            assumptions=[a.report() for a in grid.values()], fixture_duration_s=2.,
            maximum_control_starts=2*len(tasks), maximum_starts_per_task=2,
            maximum_fit_evaluations=controls.MAXIMUM_EVALUATIONS, maximum_precision_predictions_per_task=7,
            scope='65 deterministic analytic covariance/recovery controls and two structural ambiguities; not flight simulations',
            empirical_earth_fit_attempts=0, covariance_calibrated=False, scientific_eligibility_changes=0)
        def verify():
            for name, digest in {**sources, **inputs}.items():
                if il.sha256(Path(name)) != digest:
                    raise ValueError('frozen source/input changed')
            if runtime.numerical_environment() != manifest['environment']:
                raise ValueError('numerical environment changed')
        verify(); path = output/'manifest.json'
        if path.exists():
            if load(path) != manifest:
                raise ValueError('source/input/environment mismatch; use new freeze')
            if (output/'completion.json').exists():
                raise ValueError('completed control audit is frozen; do not resume')
        else:
            follow.atomic_json(path, manifest)
            snapshots = output/'source-freeze'; snapshots.mkdir()
            for name in sources:
                shutil.copyfile(name, snapshots/Path(name).name)
        results = []; manifest_digest = il.sha256(path)
        for task, spec in tasks.items():
            verify(); target = output/(task+'.json')
            result = cached(target, task, manifest_digest)
            if result is None:
                charge(output/'control-starts.jsonl', task, manifest_digest, tasks)
                follow.atomic_json(output/'status.json', dict(state='running', task=task,
                    completed=len(results), pid=os.getpid()))
                result = controls.run_case(spec['case'], grid[spec['assumption']])
                verify()
                follow.atomic_json(target, dict(task=task, manifest_sha256=manifest_digest,
                    result_sha256=result_hash(result), result=result))
            results.append(result)
            if len(results) % len(grid) == 0:
                print(json.dumps(dict(case=spec['case'], completed=len(results),
                    recovery_failures=sum(not r['noiseless_recovery_passed'] for r in results))), flush=True)
        structural = controls.structural_error_controls(); verify()
        summary = dict(version=controls.VERSION, state='complete', results=results,
            control_cases=len(fixtures.CASES), covariance_assumptions=len(grid), controls=len(results),
            noiseless_recovery_failures=sum(not r['noiseless_recovery_passed'] for r in results),
            structural_controls=structural, structural_failures=sum(not r['passed'] for r in structural['controls']),
            fit_residual_evaluations=sum(r['noiseless_fit']['evaluations'] for r in results),
            precision_prediction_evaluations=sum(r['diagnostic_prediction_evaluations'] for r in results),
            empirical_earth_fit_attempts=0, covariance_calibrated=False,
            scientific_eligibility_changes=0, originals_deleted=0)
        observation.gzip_json(output/'summary.json.gz', summary)
        compact = {k:v for k,v in summary.items() if k not in ('results', 'structural_controls')}
        compact.update(manifest_sha256=manifest_digest, summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json', compact)
        follow.atomic_json(output/'status.json', dict(state='complete', controls=len(results), pid=os.getpid()))
        print(json.dumps(compact, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-correlated-controls-20261007'))
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[2], args.output.resolve())
