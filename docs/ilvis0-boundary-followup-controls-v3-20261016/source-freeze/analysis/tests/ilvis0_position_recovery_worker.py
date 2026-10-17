# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite all-stretch recovery using the qualified actual-position solver."""
import argparse
import copy
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GUIDE = Path('docs/ilvis0-position-recovery-20261013')
OUTPUT = Path('data/ilvis0-position-recovery-20261013')
PREPARATION = ROOT/'docs/ilvis0-position-recovery-preparation-20261013'
TRIAL = ROOT/'data/ilvis0-position-stability-trial-20261013'
VERSION = 'ilvis0-full-position-recovery-v1'
spec = importlib.util.spec_from_file_location('full_recovery_position_dependency',
    Path(__file__).with_name('ilvis0_position_stability_worker.py'))
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
core, base, shared = prior.core, prior.core.base, prior.core.shared
core.VERSION, core.GUIDE, core.OUTPUT = VERSION, GUIDE, OUTPUT
solver = prior.solver


def execution_plan(plan, qualified):
    if qualified.get('qualification', {}).get('qualified') is not True:
        raise ValueError('completed qualified position trial required')
    reused = [t for t in plan['tasks'] if t['action'] == 'reuse_qualified_subset']
    tasks = [t for t in plan['tasks'] if t['action'] == 'new_start']
    if (len(tasks), len(reused), plan['maximum_native_sweeps']) != (159, 18, 95718):
        raise ValueError('frozen full recovery scope changed')
    if any(not qualified['results'][t['identity']]['converged'] for t in reused):
        raise ValueError('unqualified reused fit')
    # Fresh controls run first; selection and repeat identities stay unchanged.
    tasks = sorted(tasks, key=lambda t: t['role'] != 'control')
    proposal = copy.deepcopy(plan)
    proposal.update(version=VERSION, state='prepared', ready_to_launch=True,
        tasks=tasks, all_tasks=copy.deepcopy(plan['tasks']),
        identities=[t['identity'] for t in tasks], reused_identities=[t['identity'] for t in reused],
        selected_segment_ids=list(dict.fromkeys(t['segment_id'] for t in tasks+reused)),
        recovery_segment_ids=list(dict.fromkeys(t['segment_id'] for t in plan['tasks'] if t['role'] != 'control')),
        solver_version=solver.VERSION, perturbation=.01,
        repeat_cost_relative_tolerance=1e-6, repeat_track_rms_tolerance_m=.01,
        control_cost_relative_tolerance=1e-6, physical_bounds_unchanged=True,
        clock='nominal_200Hz', covariance='h1_v3_tau60',
        execution_authority='standing_analysis_roadmap', observed_allowance_authorized=True)
    if len(set(proposal['identities']+proposal['reused_identities'])) != 177:
        raise ValueError('duplicate/reused charge identity')
    return proposal


def reference_for(task, originals, trial):
    if task['role'] == 'control':
        fit = trial['results'][task['identity']]
    else:
        fit = next(f for c in originals[task['segment_id']]['cases'] if c['case_id'] == task['case_id']
                   for f in c['fits'] if f['model'] == task['model'])
    return copy.deepcopy({k: fit[k] for k in
                          ('active_parameters', 'normalized_parameters', 'residual_sum_squares')})


def qualified_dependency():
    manifest, summary, hashes = prior.completed_endpoints(TRIAL)
    if (summary['starts'] != 24 or summary['qualification']['qualified'] is not True
            or len(summary['qualification']['repeatability']) != 3
            or not all(f['converged'] for f in summary['results'].values())):
        raise ValueError('complete qualified 24-fit dependency required')
    prior.wrapper.verify_linearizations(TRIAL, summary)
    for fit in summary['results'].values():
        shared.clock.residuals.check_hashes({str(TRIAL/fit['epoch_file']): fit['epoch_sha256']})
    return manifest, summary, hashes


def verify(output, originals=False):
    manifest = core.verify(output, originals=originals)
    plan = manifest['proposal']
    if (plan['maximum_starts'], plan['maximum_native_sweeps'], len(plan['identities']),
            len(plan['reused_identities'])) != (159, 95718, 159, 18):
        raise ValueError('finite full recovery allowance mismatch')
    if not {str(Path(__file__).resolve()), str(ROOT/'analysis/tests/test_ilvis0_position_recovery_worker.py')} <= set(manifest['sources']):
        raise ValueError('full recovery qualification sources missing')
    return manifest


def prepare(output):
    with shared.worker_lock(output):
        if (output/'completion.json').exists():
            raise ValueError('completed recovery is frozen')
        if (output/'manifest.json').exists():
            return verify(output)
        if (output/'starts.jsonl').exists():
            raise ValueError('unmarked charged start journal')
        receipt = base.load(PREPARATION/'receipt.json')
        shared.clock.audit.verify_artifacts(PREPARATION, receipt)
        for section in ('inputs', 'sources'):
            shared.clock.residuals.check_hashes({str(ROOT/name): digest for name, digest in receipt[section].items()})
        saved, trial, hashes = qualified_dependency()
        tests = base.load(GUIDE/'test-receipt.json')
        if tests.get('exit_code') != 0 or tests.get('failures') != 0 or tests.get('tests', 0) < 89:
            raise ValueError('full recovery software checks incomplete')
        shared.clock.residuals.check_hashes(tests['sources'])
        proposal = execution_plan(base.load(PREPARATION/'plan.json'), trial)
        baseline = base.load(core.BASELINE/'summary.json.gz')
        indexed = {r['segment']['segment_id']: r for r in base.load(core.BASELINE/'selection.json.gz')['selected']}
        chosen = [indexed[sid] for sid in proposal['selected_segment_ids']]
        sources = dict(saved['sources'])
        for path in (Path(__file__), ROOT/'analysis/tests/test_ilvis0_position_recovery_worker.py',
                     PREPARATION/'build_plan.py', ROOT/'analysis/tests/test_ilvis0_position_recovery_plan.py'):
            sources[str(path.resolve())] = base.il.sha256(path)
        if len({Path(p).name for p in sources}) != len(sources):
            raise ValueError('source snapshot filename collision')
        shared.clock.residuals.check_hashes(sources)
        inputs = {str(TRIAL/name): digest for name, digest in hashes.items()}
        inputs[str(TRIAL/'completion.json')] = base.il.sha256(TRIAL/'completion.json')
        for directory, names in ((core.BASELINE, ('summary.json.gz', 'selection.json.gz', 'evidence-receipt.json')),
                (PREPARATION, ('plan.json', 'receipt.json', 'tasks.csv', 'stretches.csv')),
                (GUIDE, ('PLAN.md', 'test-receipt.json'))):
            for name in names:
                path = (directory/name).resolve()
                inputs[str(path)] = base.il.sha256(path)
        context = ROOT/'data/ilvis0-followup-20261007/summary.json'
        inputs[str(context)] = base.il.sha256(context)
        originals = {r['source_path']: base.il.sha256(r['source_path']) for r in chosen}
        reused = {identity: copy.deepcopy(trial['results'][identity]) for identity in proposal['reused_identities']}
        artifacts = ['selection.json.gz', 'proposal.json', 'reused-results.json.gz']
        for fit in reused.values():
            fit['result_origin'] = 'qualified_subset'
            for file_key, hash_key in (('epoch_file', 'epoch_sha256'), ('linearization_file', 'linearization_sha256')):
                name = fit[file_key]
                if Path(name).name != name or base.il.sha256(TRIAL/name) != fit[hash_key]:
                    raise ValueError('invalid sealed subset artifact')
                shutil.copyfile(TRIAL/name, output/name)
                artifacts.append(name)
        base.observation.gzip_json(output/'selection.json.gz', dict(selected=chosen))
        base.observation.gzip_json(output/'reused-results.json.gz', dict(results=reused))
        base.follow.atomic_json(output/'proposal.json', proposal)
        (output/'source-freeze').mkdir(exist_ok=True)
        for path in sources:
            shutil.copyfile(path, output/'source-freeze'/Path(path).name)
        manifest = dict(version=VERSION, proposal=proposal, solver_policy=solver.POLICY,
            sources=sources, inputs=inputs, originals=originals, environment=saved['environment'],
            value_kernel=saved['value_kernel'], tangent_kernel=saved['tangent_kernel'], cases=core.base.primary_cases(),
            artifacts={name: base.il.sha256(output/name) for name in artifacts},
            preparation_original_use='byte hashing only; no fits', scientific_decision='abstain')
        base.follow.atomic_json(output/'manifest.json', manifest)
        return verify(output)


def interrupted_fit(task, book):
    return dict(model=task['model'], case_id=task['case_id'], role=task['role'], converged=False,
        error='interrupted charged start; no retry', fit_native_sweeps=book.count(task['identity'], 'fit'),
        diagnostic_native_sweeps=book.count(task['identity'], 'diagnostic'),
        scientific_decision='abstain', scientific_eligible=False)


def saved_fit(output, identity, digest, book):
    fit = base.cached(output/(identity.replace('::', '-')+'.json'), digest)
    if fit is None:
        return None
    if identity not in {r['identity'] for r in book.read('starts')}:
        raise ValueError('cached result without charged start')
    for key, hash_key in (('epoch_file', 'epoch_sha256'), ('linearization_file', 'linearization_sha256')):
        if key in fit:
            name = fit[key]
            if Path(name).name != name:
                raise ValueError('invalid fit artifact path')
            shared.clock.residuals.check_hashes({str(output/name): fit[hash_key]})
    return fit


def comparisons(plan, originals, fits, qualification):
    repeats = {r['identity'].split('::')[0]: r['passed'] for r in qualification['repeatability']}
    rows = []
    for sid in plan['recovery_segment_ids']:
        cases = [dict(case_id=c['case_id'], fits=[fits.get('::'.join((sid, c['case_id'], f['model'], 'primary')), f)
                                                for f in c['fits']]) for c in originals[sid]['cases']]
        raw = base.shape.hierarchical_profile(cases)
        checked = qualification['controls_passed'] and repeats.get(sid, False)
        profile = copy.deepcopy(raw)
        if not checked:
            profile.update(conditional_shape_preference='unresolved', rotation_diagnostics=None,
                           rotation_withheld_reason='recovery control or scheduled repeat check failed')
        rows.append(dict(segment_id=sid, cases=cases, raw_profile=raw, profile=profile,
                         recovery_checks_passed=bool(checked), source_provenance=originals[sid]['provenance']))
    return rows


def qualification(output, proposal, fits):
    result = core.qualify(output, dict(proposal, tasks=proposal['all_tasks']), fits)
    controls = [t for t in proposal['tasks'] if t['role'] == 'control']
    result['controls_passed'] = all(fits[t['identity']]['converged']
        and abs(fits[t['identity']]['residual_sum_squares']-fits[t['identity']]['reference_cost'])
            /max(1., fits[t['identity']]['reference_cost']) <= proposal['control_cost_relative_tolerance']
        and max(fits[t['identity']]['baseline_track_change_rms_neu_m']) <= .01 for t in controls)
    return result


def run(output, lock_fd=None):
    if (output/'completion.json').exists():
        raise ValueError('completed recovery is frozen; package only')
    with shared.worker_lock(output, lock_fd):
        if (output/'completion.json').exists():
            raise ValueError('completed recovery is frozen; package only')
        manifest = verify(output, originals=True)
        proposal = manifest['proposal']
        prior.wrapper.authorization(output, proposal)
        digest = base.il.sha256(output/'manifest.json')
        book = core.journal.Ledger(output, digest, proposal['identities'], fit_limit=600, diagnostic_limit=2)
        book.read('starts'); book.read('sweeps')
        kernel, build = base.explore.load_kernel(output/'kernel')
        tangent, tbuild = base.shape.load_tangent(output/'kernel')
        if build != manifest['value_kernel'] or tbuild != manifest['tangent_kernel']:
            raise ValueError('native build differs from qualified implementation')
        contexts = {r['task_id']: r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        originals = {r['segment_id']: r for r in base.load(core.BASELINE/'summary.json.gz')['results']}
        trial = base.load(TRIAL/'summary.json')
        cases = {c['case_id']: c for c in manifest['cases']}
        grid = {a.name: a for a in base.sensitivity.assumptions()}
        fits = base.load(output/'reused-results.json.gz')['results']
        for selected in base.load(output/'selection.json.gz')['selected']:
            sid = selected['segment']['segment_id']
            tasks = [t for t in proposal['tasks'] if t['segment_id'] == sid]
            if not tasks:
                continue
            # Extraction failures remain charged failures; never drop an interval.
            arrays, extraction_error = None, None
            try:
                values, times, gps, provenance = base.segments.extract_segment(Path(selected['source_path']), contexts[selected['task']], selected['segment'])
                if provenance != originals[sid]['provenance']:
                    raise ValueError('original extraction provenance differs')
                blocks = np.tile(np.diag([.3**2, .3**2, .7**2]), (len(gps), 1, 1))
                covariance = base.sensitivity.coordinate_covariance(times, gps[:, 0], gps[:, 2], blocks, grid['h1_v3_tau60'])
                arrays = (values, times, gps, provenance, covariance)
            except Exception as error:
                extraction_error = type(error).__name__+': '+str(error)
            for task in tasks:
                verify(output)
                identity = task['identity']
                target = output/(identity.replace('::', '-')+'.json')
                fit = saved_fit(output, identity, digest, book)
                started = identity in {r['identity'] for r in book.read('starts')}
                if fit is None:
                    if started:
                        fit = interrupted_fit(task, book)
                    elif extraction_error:
                        book.start(identity)
                        fit = dict(interrupted_fit(task, book), error='extraction failure: '+extraction_error)
                    else:
                        base.follow.atomic_json(output/'status.json', dict(state='fitting', identity=identity,
                            completed_new_fits=sum(t['identity'] in fits for t in proposal['tasks']),
                            maximum_starts=159, pid=os.getpid()))
                        fit = prior.fit_task_from_reference(output, task, reference_for(task, originals, trial),
                            cases[task['case_id']], arrays, (kernel, tangent), book)
                    fit.update(result_origin='new_recovery', start_source=task['start_source'])
                    verify(output)
                    base.save(target, fit, digest)
                fits[identity] = fit
        q = qualification(output, proposal, fits)
        recovered = comparisons(proposal, originals, fits, q)
        baseline_complete = [r for r in originals.values() if r['profile']['conditional_shape_preference'] != 'unresolved']
        combined = baseline_complete+recovered
        tally = {label: sum(r['profile']['conditional_shape_preference'] == label for r in combined)
                 for label in ('globe', 'flat', 'unresolved', 'ambiguous')}
        summary = dict(version=VERSION, state='complete', results=fits, comparisons=recovered,
            original_completed_segment_ids=[r['segment_id'] for r in baseline_complete], combined_tally=tally,
            qualification=q, starts=len(book.read('starts')), reused_results=len(proposal['reused_identities']),
            native_sweeps=len(book.read('sweeps')), scientific_decision='abstain')
        base.follow.atomic_json(output/'summary.json', summary)
        base.follow.atomic_json(output/'completion.json', dict(state='complete', manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'), starts=summary['starts'], native_sweeps=summary['native_sweeps'],
            journal_hashes={n: base.il.sha256(output/n) for n in ('starts.jsonl', 'sweeps.jsonl')}))
        base.follow.atomic_json(output/'status.json', dict(state='complete', starts=summary['starts'],
            native_sweeps=summary['native_sweeps'], combined_tally=tally))


def publish(output):
    manifest = verify(output)
    complete = base.load(output/'completion.json')
    if complete['manifest_sha256'] != base.il.sha256(output/'manifest.json') or complete['summary_sha256'] != base.il.sha256(output/'summary.json'):
        raise ValueError('completion hash mismatch')
    summary = base.load(output/'summary.json')
    proposal = manifest['proposal']
    book = core.journal.Ledger(output, complete['manifest_sha256'], proposal['identities'], fit_limit=600, diagnostic_limit=2)
    if (len(book.read('starts')) != 159 or set(summary['results']) != set(proposal['identities']+proposal['reused_identities'])
            or summary['starts'] != complete['starts'] or summary['starts'] != 159
            or summary['native_sweeps'] != complete['native_sweeps'] or summary['native_sweeps'] != len(book.read('sweeps'))):
        raise ValueError('incomplete recovery accounting')
    shared.clock.residuals.check_hashes({str(output/n): h for n, h in complete['journal_hashes'].items()})
    names = ['manifest.json', 'proposal.json', 'selection.json.gz', 'reused-results.json.gz', 'summary.json',
             'completion.json', 'starts.jsonl', 'sweeps.jsonl', 'authorization.json']
    for identity, fit in summary['results'].items():
        if identity in proposal['identities']:
            if (fit['fit_native_sweeps'] != book.count(identity, 'fit')
                    or fit['diagnostic_native_sweeps'] != book.count(identity, 'diagnostic')):
                raise ValueError('saved fit charge mismatch')
        for key, digest_key in (('epoch_file', 'epoch_sha256'), ('linearization_file', 'linearization_sha256')):
            if key in fit:
                name = fit[key]
                if Path(name).name != name or base.il.sha256(output/name) != fit[digest_key]:
                    raise ValueError('saved fit artifact mismatch')
                names.append(name)
    GUIDE.mkdir(exist_ok=True)
    for name in set(names):
        shutil.copyfile(output/name, GUIDE/name)
    shutil.copytree(output/'source-freeze', GUIDE/'source-freeze', dirs_exist_ok=True)
    rows = [dict(identity=t['identity'], role=t['role'], origin=summary['results'][t['identity']]['result_origin'],
        converged=summary['results'][t['identity']]['converged'], model=t['model'], case_id=t['case_id'],
        fit_sweeps=summary['results'][t['identity']]['fit_native_sweeps']) for t in proposal['all_tasks']]
    shared.clock.residuals.atomic_bytes(GUIDE/'fits.csv', shared.clock.residuals.csv_bytes(rows))
    text = '# Remaining-stretch recovery results\n\n'
    text += f"Combined numerical findings: {summary['combined_tally']}.\n\n"
    text += 'Original results are preserved. New comparisons require six passing primary fits, '
    text += 'the predetermined repeat and passing controls. These are numerical preferences, '
    text += 'not calibrated detections or proof of global optima.\n\n'
    for row in summary['comparisons']:
        text += f"- `{row['segment_id']}`: {row['profile']['conditional_shape_preference']}.\n"
    (GUIDE/'RESULTS.md').write_text(text)
    names += ['fits.csv', 'RESULTS.md']
    base.follow.atomic_json(GUIDE/'evidence-receipt.json', dict(version=VERSION,
        artifacts={n: base.il.sha256(GUIDE/n) for n in set(names)}, scientific_decision='abstain'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--package-only', action='store_true')
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args()
    os.chdir(ROOT)
    output = args.output.resolve()
    if args.prepare_only:
        manifest = prepare(output)
        print('Prepared full recovery:', manifest['proposal']['maximum_starts'], 'new starts, 18 reused results')
    elif args.package_only:
        publish(output)
    elif args.detach:
        with shared.worker_lock(output) as lock:
            manifest = verify(output)
            prior.wrapper.record_limits(output, manifest)
            with (output/'worker.log').open('ab') as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--output', str(output),
                    '--lock-fd', str(lock.fileno())], pass_fds=(lock.fileno(),), start_new_session=True,
                    stdout=log, stderr=log)
            base.follow.atomic_json(output/'worker.json', dict(pid=child.pid,
                manifest_sha256=base.il.sha256(output/'manifest.json')))
            print('Detached full recovery worker', child.pid)
    else:
        run(output, args.lock_fd)
        publish(output)


if __name__ == '__main__':
    main()
