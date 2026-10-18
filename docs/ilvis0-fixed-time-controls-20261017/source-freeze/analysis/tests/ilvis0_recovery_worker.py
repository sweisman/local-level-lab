# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite recovery qualification; original intervals, models and findings stay frozen."""
import argparse
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import ilvis0_prediction_covariance_worker as shared
from lll import ilvis0_recovery_plan as planning, ilvis0_solver_recovery as solver
from lll import ilvis0_sweep_journal as journal

base = shared.base
VERSION = 'ilvis0-recovery-qualification-worker-v1'
OUTPUT = Path('data/ilvis0-convergence-recovery-trial-20261012')
GUIDE = Path('docs/ilvis0-convergence-recovery-trial-20261012')
SUBSET = Path('docs/ilvis0-convergence-recovery-preparation-20261012')
BASELINE = Path('docs/ilvis0-highspeed-segments-20261008')


def repeat_start(point, step):
    point = np.asarray(point, dtype=float)
    if not 0 < step < 1 or not np.all(np.isfinite(point)) or np.any(abs(point) > 1):
        raise ValueError('finite feasible point and small perturbation required')
    return np.clip(point + np.where(point >= 0, -step, step), -1, 1)


def prepare(output):
    with shared.worker_lock(output):
        if (output / 'manifest.json').exists():
            return verify(output)
        if (output / 'starts.jsonl').exists():
            raise ValueError('unmarked charge journal')
        for directory, receipt in [(SUBSET, 'preparation-receipt.json'),
                                   (BASELINE, 'evidence-receipt.json'),
                                   (GUIDE, 'control-receipt.json')]:
            value = base.load(directory / receipt)
            shared.clock.audit.verify_artifacts(directory, value)
            shared.clock.residuals.check_hashes(value.get('sources', {}))
        prior = shared.verify(shared.OUTPUT)
        if not (shared.OUTPUT / 'completion.json').exists():
            raise ValueError('preceding covariance comparison must be complete')
        old = base.load(BASELINE / 'summary.json.gz')
        subset = base.load(SUBSET / 'selection-summary.json')
        plan = planning.build(old['results'], subset['selected_segment_ids'])
        original_selection = base.load(BASELINE / 'selection.json.gz')
        indexed = {r['segment']['segment_id']: r for r in original_selection['selected']}
        chosen = [indexed[sid] for sid in plan['selected_segment_ids']]
        sources = dict(prior['sources'])
        for path in [Path(__file__), Path(solver.__file__), Path(planning.__file__),
                     Path('analysis/tests/test_ilvis0_solver_recovery.py'),
                     Path('analysis/tests/test_ilvis0_recovery_plan.py'),
                     Path('analysis/tests/test_ilvis0_recovery_worker.py')]:
            sources[str(path.resolve())] = base.il.sha256(path)
        shared.clock.residuals.check_hashes(sources)
        if len({Path(p).name for p in sources}) != len(sources):
            raise ValueError('source snapshot filename collision')
        inputs = {}
        for directory, names in [(BASELINE, ['summary.json.gz', 'selection.json.gz', 'manifest.json',
                                            'fit-manifest.json', 'completion.json', 'evidence-receipt.json']),
                                 (SUBSET, ['preparation-receipt.json', 'selection-summary.json', 'representative-subset.csv']),
                                 (GUIDE, ['PLAN.md', 'control-receipt.json'])]:
            for name in names:
                p = (directory / name).resolve()
                inputs[str(p)] = base.il.sha256(p)
        context = Path('data/ilvis0-followup-20261007/summary.json').resolve()
        inputs[str(context)] = base.il.sha256(context)
        originals = {r['source_path']: base.il.sha256(r['source_path']) for r in chosen}
        base.observation.gzip_json(output / 'selection.json.gz', dict(selected=chosen))
        base.follow.atomic_json(output / 'proposal.json', plan)
        (output / 'source-freeze').mkdir(exist_ok=True)
        for path in sources:
            shutil.copyfile(path, output / 'source-freeze' / Path(path).name)
        manifest = dict(version=VERSION, proposal=plan, solver_policy=solver.POLICY,
                        sources=sources, inputs=inputs, originals=originals,
                        environment=prior['environment'], value_kernel=prior['value_kernel'],
                        tangent_kernel=prior['tangent_kernel'], cases=base.primary_cases(),
                        artifacts={n: base.il.sha256(output / n) for n in ('selection.json.gz', 'proposal.json')},
                        preparation_original_use='byte hashing only; no integration or observed fits',
                        scientific_decision='abstain')
        base.follow.atomic_json(output / 'manifest.json', manifest)
        return verify(output)


def verify(output, originals=False):
    m = base.load(output / 'manifest.json')
    if m['version'] != VERSION or m['solver_policy'] != solver.POLICY:
        raise ValueError('frozen recovery implementation changed')
    if m['proposal'] != base.load(output / 'proposal.json'):
        raise ValueError('finite proposal changed')
    shared.clock.residuals.check_hashes(m['sources'])
    shared.clock.residuals.check_hashes(m['inputs'])
    base.runtime.check_environment(m['environment'])
    if any(v != '2' for v in m['environment']['thread_settings'].values()):
        raise ValueError('exactly two numerical threads required')
    for name, digest in m['sources'].items():
        if base.il.sha256(output / 'source-freeze' / Path(name).name) != digest:
            raise ValueError('source snapshot mismatch')
    for name, digest in m['artifacts'].items():
        if base.il.sha256(output / name) != digest:
            raise ValueError('selection/proposal artifact changed')
    if originals:
        shared.clock.residuals.check_hashes(m['originals'])
    return m


def authorization(output, plan):
    expected = dict(manifest_sha256=base.il.sha256(output / 'manifest.json'),
                    maximum_starts=plan['maximum_starts'],
                    maximum_native_sweeps=plan['maximum_native_sweeps'], retries=0,
                    approval='explicit_user_approval')
    path = output / 'authorization.json'
    if not path.exists() or base.load(path) != expected:
        raise ValueError('explicit finite authorization matching the freeze required')


def fit_task(output, task, reference, case, arrays, kernels, book):
    identity = task['identity']
    charged = book.start(identity)
    begin = time.monotonic()
    fit = dict(model=task['model'], case_id=task['case_id'], role=task['role'], converged=False)
    try:
        values, times, gps, provenance, covariance = arrays
        seed, _ = base.corpus.initialize(times, gps, values, task['model'])
        problem = shared.ChargedProblem(values[:, 9:12], values[:, 12:15], np.full(len(values), .005),
            times, gps, covariance, seed, base.estimator.Bounds(case['limits']),
            fit_earth_removal=case['profile'], kernel=kernels[0], tangent_kernel=kernels[1],
            clock_hypothesis='nominal_200Hz', processing_hypothesis='unsubtracted_increment_hypothesis',
            maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.,
            ledger=book, identity=identity)
        if list(problem.bounds.active) != reference['active_parameters']:
            raise ValueError('saved parameter order differs from reconstructed problem')
        original = np.array(reference['normalized_parameters'])
        point = repeat_start(original, .01) if task['role'] == 'repeatability' else original
        fit.update(solver.fit_candidate(problem, task['model'], start=point, maximum_evaluations=600))
        if fit['evaluations'] != book.count(identity, 'fit'):
            raise ValueError('solver/native accounting mismatch')
        fit['reference_cost'] = reference['residual_sum_squares']
        fit['initial_cost_relative_difference'] = abs(fit['initial_cost'] - fit['reference_cost']) / max(1., fit['reference_cost'])
        if task['role'] != 'repeatability' and fit['initial_cost_relative_difference'] > 1e-6:
            raise ValueError('original saved objective did not reproduce before continuation')
        problem.phase = 'diagnostic'
        coordinates = problem.predict(np.array(fit['normalized_parameters']), task['model'])
        prior_coordinates = problem.predict(original, task['model'])
        metric = shared.physical_metric(gps)
        def errors(predicted, observed):
            delta = predicted - observed
            delta[:, 1] = (delta[:, 1] + np.pi) % (2 * np.pi) - np.pi
            return delta * metric
        raw = errors(coordinates, gps)
        fit['track_rms_neu_m'] = np.sqrt(np.mean(raw ** 2, axis=0)).tolist()
        fit['baseline_track_change_rms_neu_m'] = np.sqrt(np.mean(errors(coordinates, prior_coordinates) ** 2, axis=0)).tolist()
        name = identity.replace('::', '-') + '-epochs.json.gz'
        shared.clock.residuals.atomic_bytes(output / name, gzip.compress(json.dumps(
            dict(times_s=times.tolist(), errors_neu_m=raw.tolist()), sort_keys=True, allow_nan=False).encode(), mtime=0))
        fit.update(epoch_file=name, epoch_sha256=base.il.sha256(output / name),
                   extraction_provenance=provenance)
    except Exception as error:
        fit.update(converged=False, error=type(error).__name__ + ': ' + str(error))
    fit.update(start_charge=charged, role=task['role'], case_id=task['case_id'],
               fit_native_sweeps=book.count(identity, 'fit'), diagnostic_native_sweeps=book.count(identity, 'diagnostic'),
               elapsed_s=time.monotonic() - begin, scientific_decision='abstain', scientific_eligible=False)
    return fit


def qualify(output, plan, fits):
    reasons = []
    repeats = []
    for task in plan['tasks']:
        fit = fits[task['identity']]
        if not fit['converged']:
            reasons.append(task['identity'] + ': numerical checks unfinished')
            continue
        if task['role'] == 'control':
            difference = abs(fit['residual_sum_squares'] - fit['reference_cost']) / max(1., fit['reference_cost'])
            if difference > plan['control_cost_relative_tolerance'] or max(fit['baseline_track_change_rms_neu_m']) > .01:
                reasons.append(task['identity'] + ': completed control differs from reference')
        if task['role'] == 'repeatability':
            primary = fits[task['identity'].removesuffix('repeat') + 'primary']
            if not primary['converged']:
                reasons.append(task['identity'] + ': primary comparison unfinished')
                continue
            difference = abs(fit['residual_sum_squares'] - primary['residual_sum_squares']) / max(1., fit['residual_sum_squares'], primary['residual_sum_squares'])
            one = base.load(output / fit['epoch_file'])
            two = base.load(output / primary['epoch_file'])
            if one['times_s'] != two['times_s']:
                raise ValueError('repeat receiver epochs differ')
            rms = np.sqrt(np.mean((np.array(one['errors_neu_m']) - np.array(two['errors_neu_m'])) ** 2, axis=0))
            passed = difference <= plan['repeat_cost_relative_tolerance'] and max(rms) <= plan['repeat_track_rms_tolerance_m']
            repeats.append(dict(identity=task['identity'], passed=bool(passed), relative_cost_difference=difference, track_change_rms_neu_m=rms.tolist()))
            if not passed:
                reasons.append(task['identity'] + ': repeat differs in objective or prediction')
    return dict(qualified=not reasons, reasons=reasons, repeatability=repeats,
                global_optima_proven=False, scientific_decision='abstain')


def run(output, lock_fd=None):
    if (output / 'completion.json').exists():
        raise ValueError('completed trial is frozen; package only')
    if not (output / 'authorization.json').exists():
        raise ValueError('explicit finite authorization required')
    authorization(output, base.load(output / 'manifest.json')['proposal'])
    with shared.worker_lock(output, lock_fd):
        if (output / 'completion.json').exists():
            raise ValueError('completed trial is frozen; package only')
        manifest = verify(output, originals=True)
        plan = manifest['proposal']
        authorization(output, plan)
        digest = base.il.sha256(output / 'manifest.json')
        book = journal.Ledger(output, digest, plan['identities'], fit_limit=600, diagnostic_limit=2)
        book.read('starts'); book.read('sweeps')
        kernel, build = base.explore.load_kernel(output / 'kernel')
        tangent, tbuild = base.shape.load_tangent(output / 'kernel')
        if build != manifest['value_kernel'] or tbuild != manifest['tangent_kernel']:
            raise ValueError('native binary/source build changed')
        contexts = {r['task_id']: r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        originals = {r['segment_id']: r for r in base.load(BASELINE / 'summary.json.gz')['results']}
        cases = {c['case_id']: c for c in manifest['cases']}
        grid = {a.name: a for a in base.sensitivity.assumptions()}
        fits = {}
        for selected in base.load(output / 'selection.json.gz')['selected']:
            sid = selected['segment']['segment_id']
            values, times, gps, provenance = base.segments.extract_segment(Path(selected['source_path']), contexts[selected['task']], selected['segment'])
            if provenance != originals[sid]['provenance']:
                raise ValueError('original extraction provenance differs')
            blocks = np.tile(np.diag([.3 ** 2, .3 ** 2, .7 ** 2]), (len(gps), 1, 1))
            covariance = base.sensitivity.coordinate_covariance(times, gps[:, 0], gps[:, 2], blocks, grid['h1_v3_tau60'])
            references = {(c['case_id'], f['model']): f for c in originals[sid]['cases'] for f in c['fits']}
            for task in [t for t in plan['tasks'] if t['segment_id'] == sid]:
                verify(output)
                identity = task['identity']
                target = output / (identity.replace('::', '-') + '.json')
                fit = base.cached(target, digest)
                started = identity in {r['identity'] for r in book.read('starts')}
                if fit is not None and not started:
                    raise ValueError('cached result without start charge')
                if fit is None:
                    if started:
                        fit = dict(model=task['model'], converged=False, error='interrupted charged start; no retry',
                                   fit_native_sweeps=book.count(identity, 'fit'), diagnostic_native_sweeps=book.count(identity, 'diagnostic'),
                                   scientific_decision='abstain')
                    else:
                        base.follow.atomic_json(output / 'status.json', dict(state='fitting', identity=identity, pid=os.getpid()))
                        fit = fit_task(output, task, references[task['case_id'], task['model']], cases[task['case_id']],
                                       (values, times, gps, provenance, covariance), (kernel, tangent), book)
                    verify(output); base.save(target, fit, digest)
                if 'epoch_file' in fit:
                    shared.clock.residuals.check_hashes({str(output / fit['epoch_file']): fit['epoch_sha256']})
                fits[identity] = fit
        comparisons = []
        for sid in plan['selected_segment_ids']:
            row = originals[sid]
            combined = [dict(case_id=c['case_id'], fits=[fits.get('::'.join((sid, c['case_id'], f['model'], 'primary')), f)
                                                       for f in c['fits']]) for c in row['cases']]
            comparisons.append(dict(segment_id=sid, cases=combined, profile=base.shape.hierarchical_profile(combined)))
        summary = dict(version=VERSION, state='complete', results=fits, comparisons=comparisons,
                       qualification=qualify(output, plan, fits), starts=len(book.read('starts')),
                       native_sweeps=len(book.read('sweeps')), scientific_decision='abstain')
        base.follow.atomic_json(output / 'summary.json', summary)
        base.follow.atomic_json(output / 'completion.json', dict(state='complete', manifest_sha256=digest,
            summary_sha256=base.il.sha256(output / 'summary.json'), starts=summary['starts'], native_sweeps=summary['native_sweeps'],
            journal_hashes={n: base.il.sha256(output / n) for n in ('starts.jsonl', 'sweeps.jsonl')}))
        base.follow.atomic_json(output / 'status.json', dict(state='complete', starts=summary['starts'], native_sweeps=summary['native_sweeps']))


def publish(output):
    manifest = verify(output)
    complete = base.load(output / 'completion.json')
    if complete['manifest_sha256'] != base.il.sha256(output / 'manifest.json') or complete['summary_sha256'] != base.il.sha256(output / 'summary.json'):
        raise ValueError('completion hash mismatch')
    summary = base.load(output / 'summary.json')
    book = journal.Ledger(output, complete['manifest_sha256'], manifest['proposal']['identities'], fit_limit=600, diagnostic_limit=2)
    if (len(book.read('starts')) != manifest['proposal']['maximum_starts'] or
            set(summary['results']) != set(manifest['proposal']['identities']) or
            summary['starts'] != complete['starts'] or summary['starts'] != len(book.read('starts')) or
            summary['native_sweeps'] != complete['native_sweeps'] or summary['native_sweeps'] != len(book.read('sweeps'))):
        raise ValueError('incomplete recovery accounting')
    shared.clock.residuals.check_hashes({str(output / n): h for n, h in complete['journal_hashes'].items()})
    names = ['manifest.json', 'proposal.json', 'selection.json.gz', 'summary.json', 'completion.json',
             'starts.jsonl', 'sweeps.jsonl', 'authorization.json']
    for identity, fit in summary['results'].items():
        if fit['fit_native_sweeps'] != book.count(identity, 'fit') or fit['diagnostic_native_sweeps'] != book.count(identity, 'diagnostic'):
            raise ValueError('saved fit charge counts differ')
        if 'epoch_file' in fit:
            shared.clock.residuals.check_hashes({str(output / fit['epoch_file']): fit['epoch_sha256']})
            names.append(fit['epoch_file'])
    for name in names:
        shutil.copyfile(output / name, GUIDE / name)
    shutil.copytree(output / 'source-freeze', GUIDE / 'source-freeze', dirs_exist_ok=True)
    rows = [dict(identity=t['identity'], role=t['role'], converged=summary['results'][t['identity']]['converged'],
                 model=t['model'], case_id=t['case_id'], fit_sweeps=summary['results'][t['identity']]['fit_native_sweeps'])
            for t in manifest['proposal']['tasks']]
    shared.clock.residuals.atomic_bytes(GUIDE / 'fits.csv', shared.clock.residuals.csv_bytes(rows))
    q = summary['qualification']
    text = f"# Recovery qualification results\n\n{sum(r['converged'] for r in rows)}/{len(rows)} fits passed numerical checks. "
    text += f"Subset qualification: **{'passed' if q['qualified'] else 'not passed'}**.\n\n"
    text += 'Original results remain unchanged. Completed reference fits are reused where specified. '
    text += 'This trial checks continuation, control agreement and three perturbed-start repeats; '
    text += 'it does not prove global minima or calibrated scientific significance.\n\n'
    for row in summary['comparisons']:
        text += f"- `{row['segment_id']}`: {row['profile']['conditional_shape_preference']}.\n"
    if q['reasons']:
        text += '\nQualification failures:\n\n' + '\n'.join('- ' + r for r in q['reasons']) + '\n'
    (GUIDE / 'RESULTS.md').write_text(text)
    names += ['fits.csv', 'RESULTS.md']
    base.follow.atomic_json(GUIDE / 'evidence-receipt.json', dict(version=VERSION,
        artifacts={n: base.il.sha256(GUIDE / n) for n in names}, scientific_decision='abstain'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--record-authorization', action='store_true')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--package-only', action='store_true')
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args()
    os.chdir(Path(__file__).resolve().parents[2])
    output = args.output.resolve()
    if args.prepare_only:
        m = prepare(output)
        print(json.dumps(m['proposal'], sort_keys=True))
    elif args.package_only:
        publish(output)
    elif args.record_authorization:
        with shared.worker_lock(output):
            m = verify(output)
            if (output / 'completion.json').exists():
                raise ValueError('completed trial is frozen')
            base.follow.atomic_json(output / 'authorization.json', dict(manifest_sha256=base.il.sha256(output / 'manifest.json'),
                maximum_starts=m['proposal']['maximum_starts'], maximum_native_sweeps=m['proposal']['maximum_native_sweeps'],
                retries=0, approval='explicit_user_approval'))
    elif args.detach:
        with shared.worker_lock(output) as lock:
            m = verify(output)
            authorization(output, m['proposal'])
            if (output / 'completion.json').exists():
                raise ValueError('completed trial is frozen')
            with (output / 'worker.log').open('ab') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--output', str(output),
                    '--lock-fd', str(lock.fileno())], pass_fds=(lock.fileno(),), start_new_session=True, stdout=log, stderr=log)
            base.follow.atomic_json(output / 'worker.json', dict(pid=child.pid, manifest_sha256=base.il.sha256(output / 'manifest.json')))
            print('Detached recovery worker', child.pid)
    else:
        run(output, args.lock_fd)
        publish(output)


if __name__ == '__main__':
    main()
