# SPDX-License-Identifier: AGPL-3.0-or-later
"""Approved two-stretch, twelve-start solver trial; no extension or retry reserve."""
import argparse
from collections import Counter
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import ilvis0_segment_worker as base
from lll import ilvis0_solver_refinement as solver

VERSION = 'ilvis0-matched-solver-trial-v1'
MAXIMUM_STARTS = 12
MAXIMUM_PER_IDENTITY = 1
MAXIMUM_EVALUATIONS = 200
TARGETS = ('570b37d23af5e245dd461051', 'b4e44ddc0f130ecd45674c78')
DEFAULT_OUTPUT = Path('data/ilvis0-solver-trial-20261010')
GUIDE = Path('docs/ilvis0-solver-trial-20261010')
BASELINE = Path('docs/ilvis0-highspeed-segments-20261008')


def identities():
    return [sid+'::'+case['case_id']+'::'+model
            for sid in TARGETS for case in base.primary_cases() for model in base.explore.MODELS]


def journal(path, digest):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows) > MAXIMUM_STARTS or len({r['identity'] for r in rows}) != len(rows)
            or any(r['start'] != i+1 or r['manifest_sha256'] != digest
                   or r['identity'] not in identities() or r['maximum_evaluations'] != 200
                   for i, r in enumerate(rows))):
        raise ValueError('incompatible or over-budget trial journal')
    return rows


def charge(path, identity, digest):
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        rows = journal(path, digest)
        if identity not in identities():
            raise ValueError('unapproved trial identity')
        if any(r['identity'] == identity for r in rows):
            raise ValueError('trial identity already charged; no retry authorized')
        if len(rows) >= MAXIMUM_STARTS:
            raise ValueError('trial allowance exhausted')
        row = dict(start=len(rows)+1, identity=identity, manifest_sha256=digest, maximum_evaluations=200)
        stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return row


def initial_point(problem, force, limits):
    point = np.zeros(len(problem.bounds.active))
    for i, name in enumerate(problem.bounds.active):
        if name.startswith('accel_gain'):
            point[i] = np.clip((force/9.81-1)/limits[name], -.9, .9)
        if name == 'earth_removal':
            point[i] = -1.
    return point


def verify(output):
    manifest = base.load(output/'manifest.json')
    if (manifest['identities'] != identities() or manifest['maximum_starts'] != 12
            or manifest['maximum_per_identity'] != 1 or manifest['maximum_evaluations'] != 200
            or manifest['solver_policy'] != solver.POLICY):
        raise ValueError('frozen solver trial scope changed')
    for name, digest in {**manifest['sources'], **manifest['inputs']}.items():
        if base.il.sha256(name) != digest:
            raise ValueError('frozen trial source/input mismatch: '+name)
    for name, digest in manifest['sources'].items():
        if base.il.sha256(output/'source-freeze'/Path(name).name) != digest:
            raise ValueError('trial source snapshot mismatch')
    if base.runtime.numerical_environment() != manifest['environment']:
        raise ValueError('frozen trial numerical environment changed')
    if base.il.sha256(output/'selection.json.gz') != manifest['selection_sha256']:
        raise ValueError('trial selected geometry changed')
    for name, key in (('value', 'value_kernel'), ('tangent', 'tangent_kernel')):
        build = manifest[key]
        prefix = 'native-' if name == 'value' else 'tangent-'
        if base.il.sha256(output/'kernel'/(prefix+build['source_sha256']+'.so')) != build['binary_sha256']:
            raise ValueError('trial native binary changed')
    return manifest


def prepare(root, output):
    if (output/'manifest.json').exists():
        return verify(output)
    if (output/'starts.jsonl').exists():
        raise ValueError('unmarked trial start journal')
    output.mkdir(parents=True, exist_ok=True)
    old = root/BASELINE
    receipt = base.load(old/'evidence-receipt.json')
    if receipt['state'] != 'complete':
        raise ValueError('completed audited baseline required')
    for name, digest in receipt['artifacts'].items():
        if Path(name).name != name or base.il.sha256(old/name) != digest:
            raise ValueError('baseline publication integrity mismatch')
    selection = base.load(old/'selection.json.gz'); previous = base.load(old/'manifest.json')
    if base.runtime.numerical_environment() != previous['environment']:
        raise ValueError('trial must match baseline numerical environment and two-thread settings')
    selected = {r['segment']['segment_id']: r for r in selection['selected']}
    rows = [selected[sid] for sid in TARGETS]
    if any(r['segment']['imu_type'] != 21 for r in rows) or rows[0]['segment']['signature'] != rows[1]['segment']['signature']:
        raise ValueError('approved observable control matching changed')
    # Preserve the exact whole intervals; no selector or residual-dependent rescanning.
    tasks = {r['task'] for r in rows}
    chosen = dict(selected=rows, records=[r for r in selection['records'] if r['task'] in tasks],
                  baseline_selection_sha256=base.il.sha256(old/'selection.json.gz'))
    base.observation.gzip_json(output/'selection.json.gz', chosen)
    sources = dict(previous['sources'])
    additions = [Path(__file__), Path(solver.__file__), root/'analysis/lll/inference_policy.py',
                 root/'analysis/tests/test_ilvis0_solver_refinement.py', root/'analysis/tests/test_ilvis0_solver_trial.py']
    for path in additions:
        sources[str(path.resolve())] = base.il.sha256(path)
    for name, digest in previous['sources'].items():
        if base.il.sha256(name) != digest:
            raise ValueError('baseline scientific implementation changed')
    inputs = {str(old/name): base.il.sha256(old/name) for name in
              ('manifest.json', 'fit-manifest.json', 'selection.json.gz', 'summary.json.gz',
               'completion.json', 'evidence-receipt.json')}
    contexts = root/'data/ilvis0-followup-20261007/summary.json'
    inputs[str(contexts)] = base.il.sha256(contexts)
    for row in rows:
        inputs[row['source_path']] = base.il.sha256(row['source_path'])
    kernel, value_build = base.explore.load_kernel(output/'kernel')
    tangent, tangent_build = base.shape.load_tangent(output/'kernel')
    manifest = dict(version=VERSION, solver_version=solver.VERSION, solver_policy=solver.POLICY,
        identities=identities(), maximum_starts=12, maximum_per_identity=1, maximum_evaluations=200,
        authorization='Approved two-stretch 12-fit matched development trial; no retries or expansion',
        sources=sources, inputs=inputs, environment=base.runtime.numerical_environment(),
        selection_sha256=base.il.sha256(output/'selection.json.gz'), cases=base.primary_cases(),
        value_kernel=value_build, tangent_kernel=tangent_build,
        baseline_summary_sha256=base.il.sha256(old/'summary.json.gz'), baseline_directory=str(old),
        initial_point='original force-derived accelerometer gains, zero remaining coordinates, Earth removal zero',
        covariance='unchanged h1_v3_tau60; h10_v30_tau300 fixed-parameter diagnostic',
        clock='nominal_200Hz with header_elapsed fixed-parameter diagnostic',
        control=TARGETS[0], unresolved_diagnostic=TARGETS[1], synthetic_campaigns_allowed=False,
        original_deletion_allowed=False, scientific_decision='abstain')
    (output/'source-freeze').mkdir(exist_ok=True)
    for name in sources:
        shutil.copyfile(name, output/'source-freeze'/Path(name).name)
    base.follow.atomic_json(output/'manifest.json', manifest)
    base.follow.atomic_json(output/'status.json', dict(state='prepared', charged_starts=0, total=12))
    verify(output)
    return manifest


def compare_stretch(old, new):
    result = dict(baseline_shape=old['profile']['conditional_shape_preference'],
                  new_shape=new['profile']['conditional_shape_preference'], rotation_comparison=None)
    if result['baseline_shape'] == result['new_shape'] == 'globe':
        result['rotation_comparison'] = dict(baseline=old['profile']['rotation_diagnostics'],
                                             refined=new['profile']['rotation_diagnostics'])
    return result


def run(root, output, lock_fd=None):
    output.mkdir(parents=True, exist_ok=True)
    lock = os.fdopen(lock_fd, 'a') if lock_fd is not None else (output/'worker.lock').open('a')
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists():
            raise ValueError('completed solver trial is frozen; packaging only')
        manifest = prepare(root, output); digest = base.il.sha256(output/'manifest.json')
        selected = base.load(output/'selection.json.gz')['selected']
        contexts = {r['task_id']: r for r in base.load(root/'data/ilvis0-followup-20261007/summary.json')['results']}
        kernel = base.explore.load_kernel(output/'kernel')[0]
        tangent = base.shape.load_tangent(output/'kernel')[0]
        grid = {a.name: a for a in base.sensitivity.assumptions()}; results = []
        for selected_row in selected:
            verify(output); segment = selected_row['segment']; sid = segment['segment_id']
            result = base.cached(output/(sid+'.json'), digest)
            if result is not None:
                results.append(result); continue
            base.follow.atomic_json(output/'status.json', dict(state='preparing_segment', pid=os.getpid(),
                segment_id=sid, charged_starts=len(journal(output/'starts.jsonl', digest)), total=12))
            values, times, gps, provenance = base.segments.extract_segment(
                Path(selected_row['source_path']), contexts[selected_row['task']], segment)
            blocks = np.tile(np.diag([.3**2, .3**2, .7**2]), (len(gps), 1, 1))
            covs = {name: base.sensitivity.coordinate_covariance(times, gps[:, 0], gps[:, 2], blocks, grid[name])
                    for name in ('h1_v3_tau60', 'h10_v30_tau300')}
            metric = np.column_stack((1/(6378137.+gps[:, 2]),
                      1/((6378137.+gps[:, 2])*np.cos(gps[:, 0])), np.ones(len(gps))))
            cases = []
            for case in manifest['cases']:
                fits = []
                for model in base.explore.MODELS:
                    verify(output); identity = sid+'::'+case['case_id']+'::'+model
                    target = output/(identity.replace('::', '-')+'.json')
                    fit = base.cached(target, digest)
                    if fit is not None:
                        fits.append(fit); continue
                    prior_charge = next((r for r in journal(output/'starts.jsonl', digest) if r['identity'] == identity), None)
                    if prior_charge is not None:
                        fit = dict(model=model, case_id=case['case_id'], start_charge=prior_charge,
                            error='interrupted charged start has no durable result; no retry authorized',
                            converged=False, scientific_decision='abstain')
                        base.save(target, fit, digest); fits.append(fit); continue
                    seed, force = base.corpus.initialize(times, gps, values, model)
                    kwargs = dict(fit_earth_removal=case['profile'], kernel=kernel, tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz', processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
                    problem = base.shape.TangentProblem(values[:, 9:12], values[:, 12:15], np.full(len(values), .005),
                        times, gps, covs['h1_v3_tau60'], seed, base.estimator.Bounds(case['limits']), **kwargs)
                    point = initial_point(problem, force, case['limits'])
                    charged = charge(output/'starts.jsonl', identity, digest); begin = time.monotonic()
                    base.follow.atomic_json(output/'status.json', dict(state='fitting', pid=os.getpid(),
                        identity=identity, charged_starts=charged['start'], total=12))
                    try:
                        fit = solver.fit_candidate(problem, model, start=point, maximum_evaluations=200)
                        conservative = base.shape.TangentProblem(values[:, 9:12], values[:, 12:15], np.full(len(values), .005),
                            times, gps, covs['h10_v30_tau300'], seed, base.estimator.Bounds(case['limits']), **kwargs)
                        header = base.shape.TangentProblem(values[:, 9:12], values[:, 12:15], values[:, 2], times, gps,
                            covs['h1_v3_tau60'], seed, base.estimator.Bounds(case['limits']),
                            **dict(kwargs, clock_hypothesis='header_elapsed'))
                        fit.update(base.diagnostics(problem, conservative, header, np.array(fit['normalized_parameters']),
                            model, metric, segment['diagnostic_sections'], provenance['first_interval_start_utc_s']))
                        fit['evaluations'] += fit['diagnostic_predictions']
                        if fit['evaluations'] > 200:
                            raise ValueError('trial evaluation allowance exceeded')
                    except Exception as error:
                        fit = dict(model=model, error=type(error).__name__+': '+str(error), converged=False,
                                   scientific_decision='abstain')
                    fit.update(start_charge=charged, case_id=case['case_id'], elapsed_s=time.monotonic()-begin)
                    verify(output); base.save(target, fit, digest); fits.append(fit)
                    print(json.dumps(dict(identity=identity, converged=fit['converged'],
                        evaluations=fit.get('evaluations'), charged_starts=charged['start'])), flush=True)
                cases.append(dict(case_id=case['case_id'], fits=fits))
            result = dict(segment_id=sid, task=selected_row['task'], filename=selected_row['filename'],
                          provenance=provenance, cases=cases, profile=base.shape.hierarchical_profile(cases))
            verify(output); base.save(output/(sid+'.json'), result, digest); results.append(result)
        summary = dict(version=VERSION, state='complete', results=results,
                       starts=len(journal(output/'starts.jsonl', digest)), scientific_decision='abstain')
        verify(output); base.observation.gzip_json(output/'summary.json.gz', summary)
        completion = dict(state='complete', starts=summary['starts'], maximum_starts=12,
            manifest_sha256=digest, summary_sha256=base.il.sha256(output/'summary.json.gz'), scientific_decision='abstain')
        base.follow.atomic_json(output/'completion.json', completion)
        base.follow.atomic_json(output/'status.json', completion)
        publish(root, output)


def publish(root, output):
    """Validate saved receipts and produce matched tables; never invokes a model."""
    manifest = verify(output); digest = base.il.sha256(output/'manifest.json')
    completion = base.load(output/'completion.json'); starts = journal(output/'starts.jsonl', digest)
    if (completion['state'] != 'complete' or completion['manifest_sha256'] != digest
            or completion['starts'] != len(starts)
            or completion['summary_sha256'] != base.il.sha256(output/'summary.json.gz')):
        raise ValueError('trial completion integrity mismatch')
    summary = base.load(output/'summary.json.gz'); baseline = base.load(root/BASELINE/'summary.json.gz')
    originals = {r['segment_id']: r for r in baseline['results']}
    if len(summary['results']) != 2 or {r['segment_id'] for r in summary['results']} != set(TARGETS):
        raise ValueError('trial stretch result grid mismatch')
    rows = []; comparisons = []; seen = []
    for result in summary['results']:
        sid = result['segment_id']; old = originals[sid]
        if base.cached(output/(sid+'.json'), digest) != result or result['profile'] != base.shape.hierarchical_profile(result['cases']):
            raise ValueError('trial stretch receipt/profile mismatch')
        old_fits = {(c['case_id'], f['model']): f for c in old['cases'] for f in c['fits']}
        for case in result['cases']:
            for fit in case['fits']:
                identity = sid+'::'+case['case_id']+'::'+fit['model']; seen.append(identity)
                if (base.cached(output/(identity.replace('::', '-')+'.json'), digest) != fit
                        or fit['start_charge'] not in starts or fit['start_charge']['identity'] != identity
                        or fit.get('evaluations', 0) > 200):
                    raise ValueError('trial fit receipt/charge mismatch')
                prior = old_fits[case['case_id'], fit['model']]
                cost = fit.get('residual_sum_squares'); old_cost = prior.get('residual_sum_squares')
                rows.append(dict(segment_id=sid, filename=result['filename'], case_id=case['case_id'], model=fit['model'],
                    baseline_converged=prior['converged'], refined_converged=fit['converged'], baseline_cost=old_cost,
                    refined_cost=cost, refined_minus_baseline_cost=None if cost is None else cost-old_cost,
                    baseline_evaluations=prior['evaluations'], refined_evaluations=fit.get('evaluations'),
                    stationarity=fit.get('exact_projected_gradient_relative'), stability=fit.get('stability_verified'),
                    termination=fit.get('termination'), elapsed_s=fit.get('elapsed_s'), error=fit.get('error', '')))
        comparisons.append(dict(segment_id=sid, **compare_stretch(old, result)))
    if sorted(seen) != sorted(identities()) or len(starts) != 12:
        raise ValueError('trial identity/charge completeness mismatch')
    dest = root/GUIDE; dest.mkdir(parents=True, exist_ok=True)
    base.write_csv(dest/'matched-fits.csv', rows, list(rows[0]))
    base.follow.atomic_json(dest/'comparison.json', dict(comparisons=comparisons, scientific_decision='abstain'))
    lines = ['# Matched solver refinement results', '',
        f"All {len(starts)} approved starts are accounted for. The old and new fits use the same "
        'selected stretches and physical assumptions, with a separately frozen stopping method.', '',
        f"Numerically completed fits: baseline {sum(r['baseline_converged'] for r in rows)}/12; "
        f"refinement {sum(r['refined_converged'] for r in rows)}/12. Completion is not model support.", '',
        '| Stretch | Baseline shape | Refined shape |', '|---|---|---|']
    for r in comparisons:
        lines.append(f"| {r['segment_id']} | {r['baseline_shape']} | {r['new_shape']} |")
    lines += ['', 'Shape outcomes are conditional numerical comparisons, not calibrated detections. '
        'Rotation is reported only when the complete shape comparison consistently favors globe. '
        'Unknown calibration, clock, onboard processing and receiver uncertainty remain unresolved.', '',
        'The [matched fit table](matched-fits.csv) includes every cost, stopping result and failure. '
        'Cost changes in unfinished fits are optimization diagnostics; they do not rank physical models. '
        'No retries, corpus expansion or production promotion are authorized.', '']
    (dest/'RESULTS.md').write_text('\n'.join(lines))
    for name in ('manifest.json', 'selection.json.gz', 'summary.json.gz', 'completion.json', 'starts.jsonl'):
        shutil.copyfile(output/name, dest/name)
    shutil.copytree(output/'source-freeze', dest/'source-freeze', dirs_exist_ok=True)
    names = ['RESULTS.md', 'matched-fits.csv', 'comparison.json', 'manifest.json', 'selection.json.gz',
             'summary.json.gz', 'completion.json', 'starts.jsonl']
    base.follow.atomic_json(dest/'evidence-receipt.json', dict(state='complete', scientific_decision='abstain',
        artifacts={name: base.il.sha256(dest/name) for name in names}))
    base.follow.atomic_json(output/'package-status.json', dict(state='complete', receipt_sha256=base.il.sha256(dest/'evidence-receipt.json')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--package-only', action='store_true')
    parser.add_argument('--lock-fd', type=int)
    args = parser.parse_args(); root = Path(__file__).resolve().parents[2]; output = args.output.resolve()
    if sum((args.detach, args.prepare_only, args.package_only)) > 1:
        parser.error('choose one execution mode')
    if args.package_only:
        publish(root, output); return
    if args.detach or args.prepare_only:
        output.mkdir(parents=True, exist_ok=True)
        with (output/'worker.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (output/'completion.json').exists():
                raise ValueError('completed solver trial is frozen')
            prepare(root, output)
            if args.prepare_only:
                print('Trial frozen; zero observed starts.'); return
            with (output/'worker.log').open('ab', buffering=0) as log:
                child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--output', str(output),
                    '--lock-fd', str(lock.fileno())], cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                    start_new_session=True, close_fds=True, pass_fds=(lock.fileno(),))
            base.follow.atomic_json(output/'worker.json', dict(pid=child.pid, manifest_sha256=base.il.sha256(output/'manifest.json')))
            print(json.dumps(dict(state='launched', pid=child.pid, maximum_starts=12)))
    else:
        try:
            run(root, output, args.lock_fd)
        except Exception as error:
            if (output/'manifest.json').exists() and not (output/'completion.json').exists():
                base.follow.atomic_json(output/'status.json', dict(state='stopped', pid=os.getpid(),
                    error=type(error).__name__+': '+str(error)))
            raise


if __name__ == '__main__':
    main()
