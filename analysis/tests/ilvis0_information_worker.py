# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded, resumable derivative diagnostics on existing analytic fixtures only."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_observation as observation
from lll import ilvis0_information as info, ilvis0_excitation_controls as controls
from lll import ilvis0_gps_sensitivity as sensitivity, runtime
from ilvis0_excitation_worker import load
from ilvis0_correlated_controls_worker import cached, result_hash


def charge(output, tasks, task, digest):
    with (output/'control-starts.jsonl').open('a+') as journal:
        journal.seek(0); starts = [json.loads(line) for line in journal]
        if any(r.get('start') != i+1 or r.get('task') not in tasks or
               r.get('manifest_sha256') != digest for i, r in enumerate(starts)):
            raise ValueError('corrupt start journal')
        if task not in tasks or len(starts) >= 2*len(tasks) or sum(r['task'] == task for r in starts) >= 2:
            raise ValueError('interruption retry allowance exhausted')
        journal.write(json.dumps(dict(start=len(starts)+1, task=task, manifest_sha256=digest),
                                 sort_keys=True)+'\n')
        journal.flush(); os.fsync(journal.fileno())
    descriptor = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def run(root, output):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked output; use new owned directory')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        prior = root/'docs/ilvis0-excitation-20261007'
        complete = load(prior/'completion.json')
        if complete['state'] != 'complete':
            raise ValueError('completed preceding controls required')
        for name, key in (('manifest.json', 'manifest_sha256'), ('summary.json.gz', 'summary_sha256')):
            if il.sha256(prior/name) != complete[key]:
                raise ValueError('prior control evidence mismatch')
        sources = dict(load(prior/'manifest.json')['sources'])
        for path in (Path(info.__file__), Path(__file__), root/'analysis/tests/test_ilvis0_information.py'):
            sources[str(path)] = il.sha256(path)
        inputs = {str(prior/name):il.sha256(prior/name)
                  for name in ('manifest.json', 'completion.json', 'summary.json.gz')}
        tasks = {f'information_{duration:g}_{motion}_{name}':
                 dict(duration=duration, motion=motion, assumption=name)
                 for duration in controls.DURATIONS for motion in controls.MOTIONS
                 for name in controls.ASSUMPTIONS}
        grid = {a.name:a for a in sensitivity.assumptions()}
        manifest = dict(version=info.VERSION, sources=sources, inputs=inputs, tasks=tasks,
            environment=runtime.numerical_environment(), limits=controls.LIMITS, truth=info.TRUTH,
            steps=list(info.STEPS), resolution_tolerance=info.RESOLUTION_TOLERANCE,
            unit_information_scale=info.INFORMATION_SCALE, derivative_noise_multiplier=3.,
            derivative_noise_proxy_is_bound=False,
            assumptions=[grid[n].report() for n in controls.ASSUMPTIONS],
            maximum_starts_per_task=2, maximum_total_starts=2*len(tasks),
            maximum_tasks=len(tasks), maximum_predictions_per_task=65,
            scope='18 fixed analytic fixtures, four central derivative steps; no optimization or archival observations',
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
                raise ValueError('completed information diagnostics are frozen; do not resume')
        else:
            follow.atomic_json(path, manifest)
            snapshots = output/'source-freeze'; snapshots.mkdir()
            if len({Path(n).name for n in sources}) != len(sources):
                raise ValueError('source snapshot filename collision')
            for name in sources:
                shutil.copyfile(name, snapshots/Path(name).name)
        results = []; digest = il.sha256(path)
        for task, spec in tasks.items():
            verify(); target = output/(task+'.json')
            result = cached(target, task, digest)
            if result is None:
                charge(output, tasks, task, digest)
                follow.atomic_json(output/'status.json', dict(state='running', task=task,
                    completed=len(results), pid=os.getpid()))
                result = info.run_control(spec['duration'], spec['motion'], grid[spec['assumption']])
                if result['prediction_evaluations'] > manifest['maximum_predictions_per_task']:
                    raise ValueError('prediction budget exceeded')
                verify()
                follow.atomic_json(target, dict(task=task, result=result,
                    result_sha256=result_hash(result), manifest_sha256=digest))
            results.append(dict(task=task, result=result))
            if len(results) % 6 == 0:
                print(json.dumps(dict(completed=len(results), task=task)), flush=True)
        by_task = {r['task']:r['result'] for r in results}
        covariance_differences = []
        for duration in controls.DURATIONS:
            for motion in controls.MOTIONS:
                for smaller, larger in zip(controls.ASSUMPTIONS, controls.ASSUMPTIONS[1:]):
                    a = by_task[f'information_{duration:g}_{motion}_{smaller}']['information']['steps']
                    b = by_task[f'information_{duration:g}_{motion}_{larger}']['information']['steps']
                    covariance_differences.extend(
                        x['parameters'][name]['data_resolution_fraction']-
                        y['parameters'][name]['data_resolution_fraction']
                        for x,y in zip(a,b) for name in controls.LIMITS)
        summary = dict(version=info.VERSION, state='complete', results=results,
            controls=len(results), derivative_step_cases=len(results)*len(info.STEPS),
            analytic_trajectory_failures=sum(not r['result']['analytic_control_passed'] for r in results),
            information_step_instabilities=sum(not r['result']['information']['resolution_stable_under_tested_steps']
                                              for r in results),
            maximum_resolution_operator_change=max(r['result']['information']['maximum_resolution_operator_change']
                                                   for r in results),
            prediction_evaluations=sum(r['result']['prediction_evaluations'] for r in results),
            covariance_monotonic_parameter_comparisons=len(covariance_differences),
            covariance_monotonicity_failures=sum(d < -1e-9 for d in covariance_differences),
            smallest_covariance_resolution_difference=min(covariance_differences),
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
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-information-20261007'))
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[2], args.output.resolve())
