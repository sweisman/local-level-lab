# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately approved six-start header-clock trial; original nominal fits stay frozen."""
import argparse
import fcntl
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import ilvis0_segment_worker as base
import ilvis0_residual_diagnostic as residuals
from lll import ilvis0_saved_audit as audit, ilvis0_residuals as stats

VERSION = 'ilvis0-matched-header-clock-trial-v1'
TARGET = '570b37d23af5e245dd461051'
OUTPUT = Path('data/ilvis0-clock-trial-20261010')
GUIDE = Path('docs/ilvis0-clock-trial-20261010')
BASELINE = Path('docs/ilvis0-highspeed-segments-20261008')
TRIAL = Path('docs/ilvis0-solver-trial-20261010')


def identities():
    return [TARGET+'::'+case['case_id']+'::'+model for case in base.primary_cases() for model in base.explore.MODELS]


def journal(path, digest):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows) > 6 or len({r['identity'] for r in rows}) != len(rows)
            or any(r['number'] != i+1 or r['identity'] not in identities() or r['manifest_sha256'] != digest
                   or r['maximum_evaluations'] != 200 for i, r in enumerate(rows))):
        raise ValueError('invalid clock-trial start journal')
    return rows


def charge(path, identity, digest):
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        rows = journal(path, digest)
        if identity not in identities() or len(rows) >= 6:
            raise ValueError('outside approved six-start scope')
        if any(r['identity'] == identity for r in rows):
            raise ValueError('clock identity already charged; no retry')
        row = dict(number=len(rows)+1, identity=identity, manifest_sha256=digest, maximum_evaluations=200)
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
    if (manifest['version'] != VERSION or manifest['identities'] != identities()
            or manifest['cases'] != base.primary_cases() or manifest['maximum_starts'] != 6
            or manifest['maximum_evaluations_per_start'] != 200
            or manifest['maximum_per_identity'] != 1 or manifest['clock'] != 'header_elapsed'
            or manifest['optimizer'] != 'frozen_original_fit_shape_candidate'):
        raise ValueError('clock trial freeze scope changed')
    residuals.check_hashes(manifest['sources']); residuals.check_hashes(manifest['inputs'])
    base.runtime.check_environment(manifest['environment'])
    for name, digest in manifest['sources'].items():
        if base.il.sha256(output/'source-freeze'/Path(name).name) != digest:
            raise ValueError('clock trial source snapshot changed')
    if base.il.sha256(output/'selection.json.gz') != manifest['selection_sha256']:
        raise ValueError('clock trial selected interval changed')
    return manifest


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    if (output/'manifest.json').exists():
        return verify(output)
    for directory in (BASELINE, TRIAL):
        audit.verify_artifacts(directory, base.load(directory/'evidence-receipt.json'))
    old = base.load(BASELINE/'manifest.json'); base.runtime.check_environment(old['environment'])
    residuals.check_hashes(old['sources'])
    sources = dict(old['sources'])
    for path in (Path(__file__), Path(residuals.__file__), Path(audit.__file__), Path(stats.__file__),
                 Path('analysis/tests/test_ilvis0_clock_trial.py')):
        sources[str(path.resolve())] = base.il.sha256(path)
    chosen = next(r for r in base.load(TRIAL/'selection.json.gz')['selected'] if r['segment']['segment_id'] == TARGET)
    prior = next(r for r in base.load(BASELINE/'summary.json.gz')['results'] if r['segment_id'] == TARGET)
    if chosen['segment'] != prior['segment'] or any(not f['converged'] for c in prior['cases'] for f in c['fits']):
        raise ValueError('clock target is not the unchanged completed control')
    inputs = [Path(chosen['source_path']), Path('data/ilvis0-followup-20261007/summary.json'), GUIDE/'PLAN.md',
              BASELINE/'manifest.json', BASELINE/'fit-manifest.json', BASELINE/'summary.json.gz',
              BASELINE/'evidence-receipt.json', TRIAL/'selection.json.gz', TRIAL/'evidence-receipt.json']
    base.observation.gzip_json(output/'selection.json.gz', dict(selected=[chosen]))
    (output/'source-freeze').mkdir(exist_ok=True)
    for name in sources:
        shutil.copyfile(name, output/'source-freeze'/Path(name).name)
    manifest = dict(version=VERSION, identities=identities(), maximum_starts=6, maximum_per_identity=1,
        maximum_evaluations_per_start=200, clock='header_elapsed', cases=base.primary_cases(),
        optimizer='frozen_original_fit_shape_candidate', original_initialization_reused=True,
        environment=old['environment'], sources=sources,
        inputs={str(p.resolve()): base.il.sha256(p) for p in inputs},
        selection_sha256=base.il.sha256(output/'selection.json.gz'),
        value_kernel=old['value_kernel'], tangent_kernel=old['tangent_kernel'], scientific_decision='abstain')
    base.follow.atomic_json(output/'manifest.json', manifest)
    return verify(output)


def run(output, lock_fd=None):
    output.mkdir(parents=True, exist_ok=True)
    lock = os.fdopen(lock_fd, 'a') if lock_fd is not None else (output/'worker.lock').open('a')
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest = prepare(output); digest = base.il.sha256(output/'manifest.json')
        if (output/'completion.json').exists():
            raise ValueError('completed clock trial is frozen; package only')
        kernel, build = base.explore.load_kernel(output/'kernel')
        tangent, tangent_build = base.shape.load_tangent(output/'kernel')
        if build != manifest['value_kernel'] or tangent_build != manifest['tangent_kernel']:
            raise ValueError('native build differs from baseline')
        row = base.load(output/'selection.json.gz')['selected'][0]; segment = row['segment']
        contexts = {r['task_id']: r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        values, times, gps, provenance = base.segments.extract_segment(Path(row['source_path']), contexts[row['task']], segment)
        old = next(r for r in base.load(BASELINE/'summary.json.gz')['results'] if r['segment_id'] == TARGET)
        if provenance != old['provenance']:
            raise ValueError('native extraction provenance changed')
        blocks = np.tile(np.diag([.3**2, .3**2, .7**2]), (len(gps), 1, 1))
        grid = {a.name: a for a in base.sensitivity.assumptions()}
        covs = {n: base.sensitivity.coordinate_covariance(times, gps[:, 0], gps[:, 2], blocks, grid[n])
                for n in ('h1_v3_tau60', 'h10_v30_tau300')}
        metric = np.column_stack((1/(6378137.+gps[:, 2]), 1/((6378137.+gps[:, 2])*np.cos(gps[:, 0])), np.ones(len(gps))))
        cases = []
        for case in manifest['cases']:
            fits = []
            for model in base.explore.MODELS:
                verify(output); identity = TARGET+'::'+case['case_id']+'::'+model
                target = output/(identity.replace('::', '-')+'.json')
                fit = base.cached(target, digest)
                if fit is not None:
                    if fit.get('residual_file'):
                        residuals.check_hashes({str(output/fit['residual_file']): fit['residual_sha256']})
                    fits.append(fit); continue
                if any(r['identity'] == identity for r in journal(output/'starts.jsonl', digest)):
                    fit = dict(model=model, case_id=case['case_id'], converged=False,
                        error='interrupted charged start; no retry', scientific_decision='abstain')
                    base.save(target, fit, digest); fits.append(fit); continue
                seed, force = base.corpus.initialize(times, gps, values, model)
                kwargs = dict(fit_earth_removal=case['profile'], kernel=kernel, tangent_kernel=tangent,
                    clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
                    maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
                problem = base.shape.TangentProblem(values[:, 9:12], values[:, 12:15], values[:, 2],
                    times, gps, covs['h1_v3_tau60'], seed, base.estimator.Bounds(case['limits']), **kwargs)
                generous = base.shape.TangentProblem(values[:, 9:12], values[:, 12:15], values[:, 2],
                    times, gps, covs['h10_v30_tau300'], seed, base.estimator.Bounds(case['limits']), **kwargs)
                nominal = base.shape.TangentProblem(values[:, 9:12], values[:, 12:15], np.full(len(values), .005),
                    times, gps, covs['h1_v3_tau60'], seed, base.estimator.Bounds(case['limits']),
                    **dict(kwargs, clock_hypothesis='nominal_200Hz'))
                charged = charge(output/'starts.jsonl', identity, digest); begin = time.monotonic()
                base.follow.atomic_json(output/'status.json', dict(state='fitting', identity=identity,
                    pid=os.getpid(), charged_starts=charged['number'], maximum_starts=6))
                try:
                    fit = base.shape.fit_shape_candidate(problem, model,
                        start=initial_point(problem, force, case['limits']), maximum_evaluations=200)
                    point = np.array(fit['normalized_parameters']); prediction = problem.predict(point, model)
                    fit['evaluations'] += 1
                    delta = prediction-gps; delta[:, 1] = (delta[:, 1]+math.pi)%(2*math.pi)-math.pi
                    physical = delta/metric; primary = problem.whiten(delta).reshape(-1, 3)
                    conservative = generous.whiten(delta).reshape(-1, 3)
                    if not math.isclose(float(np.sum(primary**2)), fit['residual_sum_squares'], rel_tol=1e-6, abs_tol=1e-9):
                        raise ValueError('value/tangent objective disagreement')
                    nominal_delta = nominal.predict(point, model)-gps; fit['evaluations'] += 1
                    nominal_delta[:, 1] = (nominal_delta[:, 1]+math.pi)%(2*math.pi)-math.pi
                    if fit['evaluations'] > 200:
                        raise ValueError('clock fit exceeded evaluation allowance')
                    epochs = []
                    for i in range(len(times)):
                        e = dict(epoch=i, time_utc_week_s=float(times[i]+provenance['first_interval_start_utc_s']))
                        for j, axis in enumerate(('north', 'east', 'up')):
                            e[axis+'_residual_m'] = float(physical[i, j])
                            e[axis+'_coordinate_residual'] = float(delta[i, j])
                            e[axis+'_primary_innovation'] = float(primary[i, j])
                            e[axis+'_conservative_innovation'] = float(conservative[i, j])
                        epochs.append(e)
                    name = identity.replace('::', '-')+'.csv.gz'
                    residuals.atomic_bytes(output/name, residuals.gzip.compress(residuals.csv_bytes(epochs), mtime=0))
                    fit.update(residual_file=name, residual_sha256=base.il.sha256(output/name),
                        residual_rms_neu_m=np.sqrt(np.mean(physical**2, axis=0)).tolist(),
                        nominal_fixed_parameter_rms_neu_m=np.sqrt(np.mean((nominal_delta/metric)**2, axis=0)).tolist(),
                        conservative_fixed_parameter_cost=float(np.sum(conservative**2)),
                        epoch_diagnostics=stats.summarize(times, physical, primary, conservative,
                                                         residuals.covariates(times, gps)),
                        clock_hypothesis='header_elapsed', diagnostic_predictions=2)
                except Exception as error:
                    fit = dict(model=model, converged=False, scientific_decision='abstain',
                               error=type(error).__name__+': '+str(error))
                fit.update(case_id=case['case_id'], start_charge=charged, elapsed_s=time.monotonic()-begin)
                verify(output); base.save(target, fit, digest); fits.append(fit)
                print(json.dumps(dict(identity=identity, converged=fit['converged'], error=fit.get('error'))), flush=True)
            cases.append(dict(case_id=case['case_id'], fits=fits))
        summary = dict(version=VERSION, state='complete', cases=cases, starts=len(journal(output/'starts.jsonl', digest)),
            nominal_reference=old, profile=base.shape.hierarchical_profile(cases), provenance=provenance,
            scientific_decision='abstain')
        base.follow.atomic_json(output/'summary.json', summary)
        base.follow.atomic_json(output/'completion.json', dict(state='complete', manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'), starts=summary['starts'], scientific_decision='abstain'))


def publish(output):
    verify(output); completion = base.load(output/'completion.json')
    if (completion['manifest_sha256'] != base.il.sha256(output/'manifest.json')
            or completion['summary_sha256'] != base.il.sha256(output/'summary.json')):
        raise ValueError('clock-trial completion mismatch')
    names = ['manifest.json', 'selection.json.gz', 'summary.json', 'completion.json', 'starts.jsonl']
    summary = base.load(output/'summary.json')
    names += [f['residual_file'] for c in summary['cases'] for f in c['fits'] if f.get('residual_file')]
    for name in names:
        shutil.copyfile(output/name, GUIDE/name)
    shutil.copytree(output/'source-freeze', GUIDE/'source-freeze', dirs_exist_ok=True)
    base.follow.atomic_json(GUIDE/'evidence-receipt.json', dict(version=VERSION, scientific_decision='abstain',
        artifacts={n:base.il.sha256(GUIDE/n) for n in names}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepare-only', action='store_true'); p.add_argument('--package-only', action='store_true')
    p.add_argument('--detach', action='store_true'); p.add_argument('--lock-fd', type=int)
    args = p.parse_args()
    if sum((args.prepare_only, args.package_only, args.detach)) > 1:
        p.error('choose one action')
    if args.prepare_only:
        prepare(OUTPUT); print('Prepared six-start clock freeze; no observed fits started.'); return
    if args.package_only:
        publish(OUTPUT); return
    if args.detach:
        prepare(OUTPUT)
        if (OUTPUT/'completion.json').exists():
            raise ValueError('completed clock trial is frozen')
        lock = (OUTPUT/'worker.lock').open('a'); fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        with (OUTPUT/'worker.log').open('ab') as log:
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--lock-fd', str(lock.fileno())],
                cwd=Path.cwd(), stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                pass_fds=(lock.fileno(),), start_new_session=True)
        lock.close()
        base.follow.atomic_json(OUTPUT/'worker.json', dict(pid=child.pid,
            manifest_sha256=base.il.sha256(OUTPUT/'manifest.json'), maximum_starts=6))
        print('Clock worker launched with inherited exclusive lock.'); return
    run(OUTPUT, args.lock_fd); publish(OUTPUT)


if __name__ == '__main__':
    main()
