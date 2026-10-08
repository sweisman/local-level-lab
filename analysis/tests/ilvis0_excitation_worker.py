# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen analytic duration/rotation controls, with bounded interruption recovery."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_excitation_controls as controls, ilvis0_gps_sensitivity as sensitivity, runtime
from ilvis0_correlated_controls_worker import cached, result_hash


def load(path):
    with gzip.open(path, 'rt') if path.suffix == '.gz' else path.open() as stream:
        return json.load(stream)


def run(root, output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked output; use new owned directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = root/'docs/ilvis0-correlated-controls-20261007'
        complete = load(prior/'completion.json')
        for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
            if il.sha256(prior/name) != complete[key]:
                raise ValueError('prior control evidence mismatch')
        old = load(prior/'manifest.json'); sources = dict(old['sources'])
        for path in (Path(controls.__file__), Path(__file__), root/'analysis/tests/test_ilvis0_excitation_controls.py'):
            sources[str(path)] = il.sha256(path)
        inputs = {str(prior/name):il.sha256(prior/name)
            for name in ('manifest.json', 'completion.json', 'summary.json.gz')}
        tasks = {}
        for duration in controls.DURATIONS:
            for motion in controls.MOTIONS:
                for name in controls.ASSUMPTIONS:
                    tasks[f'tangent_{duration:g}_{motion}_{name}'] = dict(kind='tangent',
                        duration=duration, motion=motion, assumption=name)
        for duration in (20., 60.):
            for parameter in ('gyro_bias_y', 'time_offset'):
                tasks[f'recovery_{duration:g}_{parameter}'] = dict(kind='recovery',
                    duration=duration, parameter=parameter, assumption='h1_v3_tau60')
        grid = {a.name:a for a in sensitivity.assumptions()}
        manifest = dict(version=controls.VERSION, sources=sources, inputs=inputs, tasks=tasks,
            environment=runtime.numerical_environment(), limits=controls.LIMITS,
            assumptions=[grid[name].report() for name in controls.ASSUMPTIONS],
            durations=list(controls.DURATIONS), motions=list(controls.MOTIONS),
            maximum_starts_per_task=2, maximum_tasks=len(tasks), maximum_total_starts=2*len(tasks),
            maximum_fit_evaluations=160, maximum_tangent_predictions=18,
            pulse_duration_s=1., pulse_peak_degrees=.1,
            scope='18 analytic eight-parameter tangents and four single-parameter recovery controls; no archived observations',
            empirical_earth_fit_attempts=0, scientific_eligibility_changes=0, originals_deleted=0)
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
                raise ValueError('completed excitation controls are frozen; do not resume')
        else:
            follow.atomic_json(path, manifest)
            snapshots = output/'source-freeze'; snapshots.mkdir()
            for name in sources:
                shutil.copyfile(name, snapshots/Path(name).name)
        results = []; digest = il.sha256(path)
        for task, spec in tasks.items():
            verify(); target = output/(task+'.json')
            result = cached(target, task, digest)
            if result is None:
                with (output/'control-starts.jsonl').open('a+') as journal:
                    journal.seek(0); starts = [json.loads(line) for line in journal]
                    if any(r.get('start') != i+1 or r.get('task') not in tasks or
                            r.get('manifest_sha256') != digest for i, r in enumerate(starts)):
                        raise ValueError('corrupt start journal')
                    if len(starts) >= 2*len(tasks) or sum(r['task'] == task for r in starts) >= 2:
                        raise ValueError('interruption retry allowance exhausted')
                    journal.write(json.dumps(dict(start=len(starts)+1, task=task, manifest_sha256=digest),
                        sort_keys=True)+'\n'); journal.flush(); os.fsync(journal.fileno())
                    descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
                follow.atomic_json(output/'status.json', dict(state='running', task=task,
                    completed=len(results), pid=os.getpid()))
                if spec['kind'] == 'tangent':
                    result = controls.run_tangent(spec['duration'], spec['motion'], grid[spec['assumption']])
                else:
                    result = controls.run_recovery(spec['duration'], spec['parameter'], grid[spec['assumption']])
                verify()
                follow.atomic_json(target, dict(task=task, result=result, result_sha256=result_hash(result),
                    manifest_sha256=digest))
            results.append(dict(task=task, kind=spec['kind'], result=result))
            if len(results) % 6 == 0 or spec['kind'] == 'recovery':
                print(json.dumps(dict(completed=len(results), task=task)), flush=True)
        tangents = [r['result'] for r in results if r['kind'] == 'tangent']
        recoveries = [r['result'] for r in results if r['kind'] == 'recovery']
        summary = dict(version=controls.VERSION, state='complete', results=results,
            tangent_controls=len(tangents), recovery_controls=len(recoveries),
            analytic_trajectory_failures=sum(not r['analytic_control_passed'] for r in tangents),
            recovery_failures=sum(not r['recovery_passed'] for r in recoveries),
            tangent_prediction_evaluations=sum(r['prediction_evaluations'] for r in tangents),
            recovery_residual_evaluations=sum(r['fit']['evaluations'] for r in recoveries),
            empirical_earth_fit_attempts=0, scientific_eligibility_changes=0,
            covariance_calibrated=False, originals_deleted=0)
        verify(); observation.gzip_json(output/'summary.json.gz', summary)
        compact = {k:v for k,v in summary.items() if k != 'results'}
        compact.update(manifest_sha256=digest, summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json', compact)
        follow.atomic_json(output/'status.json', dict(state='complete', tasks=len(results), pid=os.getpid()))
        print(json.dumps(compact, sort_keys=True), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-excitation-20261007'))
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[2], args.output.resolve())
