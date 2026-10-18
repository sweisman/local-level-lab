# SPDX-License-Identifier: AGPL-3.0-or-later
"""Metadata-only recovery schedule; never start workers or read NASA originals."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
BASELINE = ROOT/'docs/ilvis0-highspeed-segments-20261008'
SUBSET = ROOT/'docs/ilvis0-convergence-recovery-preparation-20261012'
TRIAL = ROOT/'data/ilvis0-position-stability-trial-20261013'
MODELS = ('sphere_rotating', 'sphere_still', 'flat_still')
CASES = ('bias1_unsubtracted', 'bias1_profiled_removal')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def schedule(records, inventory, trial_plan):
    """Selection uses original completion status and UTC order, never model costs."""
    indexed = {record['segment_id']: record for record in records}
    if len(indexed) != len(records) or len(inventory) != len({row['segment_id'] for row in inventory}):
        raise ValueError('duplicate recording/stretch identity')
    trial = {task['identity']: task for task in trial_plan['tasks']}
    if len(trial) != len(trial_plan['tasks']) or len(trial) != 24:
        raise ValueError('exact frozen 24-task qualification plan required')
    recovery, repeats, controls, rates = [], [], [], []
    ordered = sorted(inventory, key=lambda row: (row['start_utc'], row['filename'], row['segment_id']))
    for index, source in enumerate(ordered):
        sid = source['segment_id']
        record = indexed[sid]
        if record['profile']['conditional_shape_preference'] != 'unresolved':
            raise ValueError('recovery inventory includes completed stretch')
        fits = {(case['case_id'], fit['model']): fit for case in record['cases'] for fit in case['fits']}
        if (sum(len(case['fits']) for case in record['cases']) != 6
                or len(fits) != 6 or set(fits) != {(case, model) for case in CASES for model in MODELS}):
            raise ValueError('original six-fit matrix required')
        failed = []
        for case in CASES:
            for model in MODELS:
                fit = fits[case, model]
                if fit['converged']:
                    continue
                point = fit['normalized_parameters']
                if (len(point) != len(fit['active_parameters']) or not point
                        or any(not math.isfinite(value) or abs(value) > 1 for value in point)):
                    raise ValueError('saved feasible original start required')
                identity = '::'.join((sid, case, model, 'primary'))
                row = dict(segment_id=sid, case_id=case, model=model, identity=identity,
                           role='recovery', action='reuse_qualified_subset' if identity in trial else 'new_start',
                           start_source='qualified trial' if identity in trial else 'original first-pass endpoint',
                           baseline_fit_calls=fit['evaluations'], baseline_elapsed_s=fit['elapsed_s'])
                if fit['evaluations'] <= 0 or not math.isfinite(fit['elapsed_s']) or fit['elapsed_s'] <= 0:
                    raise ValueError('positive saved runtime and call count required')
                recovery.append(row)
                failed.append(row)
                if row['action'] == 'new_start':
                    rates.append(fit['elapsed_s']/fit['evaluations'])
        if not failed or len(failed) != int(source['unfinished_fits']):
            raise ValueError('unfinished-fit inventory disagrees with original results')
        prior_repeat = [task for task in trial.values() if task['segment_id'] == sid and task['role'] == 'repeatability']
        if len(prior_repeat) > 1:
            raise ValueError('more than one predefined subset repeat')
        chosen = (next(row for row in failed if row['identity'].rsplit('::', 1)[0]
                       == prior_repeat[0]['identity'].rsplit('::', 1)[0]) if prior_repeat else
                  next((row for row in failed if row['model'] == MODELS[index % 3]), failed[0]))
        repeat = dict(chosen, identity=chosen['identity'].rsplit('::', 1)[0]+'::repeat', role='repeatability',
                      action='reuse_qualified_subset' if prior_repeat else 'new_start',
                      start_source='qualified trial' if prior_repeat else 'original endpoint plus fixed 0.01 perturbation')
        repeats.append(repeat)
        if not prior_repeat:
            rates.append(chosen['baseline_elapsed_s']/chosen['baseline_fit_calls'])
    for task in trial.values():
        if task['role'] != 'control':
            continue
        record = indexed[task['segment_id']]
        fit = next(fit for case in record['cases'] if case['case_id'] == task['case_id']
                   for fit in case['fits'] if fit['model'] == task['model'])
        if not fit['converged']:
            raise ValueError('control is not originally complete')
        controls.append(dict(segment_id=task['segment_id'], case_id=task['case_id'], model=task['model'],
                             identity=task['identity'], role='control', action='new_start',
                             start_source='qualified trial endpoint', baseline_fit_calls=fit['evaluations'],
                             baseline_elapsed_s=fit['elapsed_s']))
        rates.append(fit['elapsed_s']/fit['evaluations'])
    tasks = recovery+repeats+controls
    if len({row['identity'] for row in tasks}) != len(tasks):
        raise ValueError('duplicate task identity')
    reused = [row for row in tasks if row['action'] != 'new_start']
    expected = {task['identity'] for task in trial.values() if task['role'] != 'control'}
    if set(row['identity'] for row in reused) != expected or len(controls) != 6:
        raise ValueError('qualification coverage disagrees with recovery schedule')
    new_starts = len(tasks)-len(reused)
    estimate = sum(rates)*602/3600
    return dict(tasks=tasks, original_unfinished_fits=len(recovery), stretches=len(ordered),
                reused_subset_fits=len(reused), primary_new_starts=sum(row['action'] == 'new_start' for row in recovery),
                repeat_new_starts=sum(row['action'] == 'new_start' for row in repeats),
                fresh_controls=len(controls), maximum_starts=new_starts,
                maximum_fit_sweeps=600, maximum_diagnostic_sweeps=2,
                maximum_native_sweeps=new_starts*602, retries=0, numerical_threads=2,
                estimate_at_ceiling_hours=estimate, estimate_range_hours=[.8*estimate, 1.2*estimate],
                runtime_estimate_basis='matched original elapsed seconds per call; ceiling estimate, not a guarantee',
                ready_to_launch=False, required_gate='completed position-stability trial: all qualification checks passed',
                scientific_decision='abstain')


def main():
    prior_receipt = json.loads((BASELINE/'evidence-receipt.json').read_text())
    if sha(BASELINE/'summary.json.gz') != prior_receipt['artifacts']['summary.json.gz']:
        raise ValueError('original result hash mismatch')
    subset_receipt = json.loads((SUBSET/'preparation-receipt.json').read_text())
    if sha(SUBSET/'all-unresolved.csv') != subset_receipt['artifacts']['all-unresolved.csv']:
        raise ValueError('original unresolved-inventory hash mismatch')
    manifest = json.loads((TRIAL/'manifest.json').read_text())
    if sha(TRIAL/'proposal.json') != manifest['artifacts']['proposal.json']:
        raise ValueError('qualification proposal hash mismatch')
    summary = json.loads(gzip.decompress((BASELINE/'summary.json.gz').read_bytes()))
    with (SUBSET/'all-unresolved.csv').open() as stream:
        inventory = list(csv.DictReader(stream))
    plan = schedule(summary['results'], inventory, manifest['proposal'])
    if (plan['stretches'], plan['original_unfinished_fits'], plan['maximum_starts']) != (41, 130, 159):
        raise ValueError('frozen baseline population or schedule changed')
    plan.update(version='ilvis0-position-recovery-preparation-v1', state='metadata_preparation_only',
                qualification_manifest_sha256=sha(TRIAL/'manifest.json'), observed_fit_starts=0,
                native_predictions=0, original_files_read=0)
    (HERE/'plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False)+'\n')
    for name, rows in (('tasks.csv', plan['tasks']), ('stretches.csv', inventory)):
        with (HERE/name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    inputs = [BASELINE/'summary.json.gz', BASELINE/'evidence-receipt.json',
              SUBSET/'all-unresolved.csv', SUBSET/'preparation-receipt.json',
              TRIAL/'manifest.json', TRIAL/'proposal.json']
    receipt = dict(inputs={str(path.relative_to(ROOT)): sha(path) for path in inputs},
                   sources={str(Path(__file__).relative_to(ROOT)): sha(__file__),
                            'analysis/tests/test_ilvis0_position_recovery_plan.py':
                            sha(ROOT/'analysis/tests/test_ilvis0_position_recovery_plan.py')},
                   artifacts={name: sha(HERE/name) for name in ('plan.json', 'tasks.csv', 'stretches.csv', 'README.md')},
                   observed_fit_starts=0, native_predictions=0, original_files_read=0)
    (HERE/'receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(json.dumps({key: plan[key] for key in ('stretches', 'original_unfinished_fits', 'primary_new_starts',
                     'repeat_new_starts', 'fresh_controls', 'maximum_starts', 'maximum_native_sweeps',
                     'estimate_range_hours', 'ready_to_launch')}))


if __name__ == '__main__':
    main()
