# SPDX-License-Identifier: AGPL-3.0-or-later
"""Twenty-four saved-parameter predictions, no optimization or automatic expansion."""
import argparse
import csv
import fcntl
import gzip
import io
import json
import math
import os
from pathlib import Path
import shutil
import time

import numpy as np
import ilvis0_segment_worker as base
from lll import ilvis0_residuals as stats, ilvis0_saved_audit as audit

VERSION = 'ilvis0-saved-parameter-residual-pass-v1'
TARGETS = ('570b37d23af5e245dd461051', 'b4e44ddc0f130ecd45674c78')
CLOCKS = ('nominal_200Hz', 'header_elapsed')
OUTPUT = Path('data/ilvis0-residual-diagnostic-20261010')
GUIDE = Path('docs/ilvis0-residual-diagnostic-20261010')
BASELINE = Path('docs/ilvis0-highspeed-segments-20261008')
TRIAL = Path('docs/ilvis0-solver-trial-20261010')


def check_hashes(hashes):
    for name, wanted in hashes.items():
        if base.il.sha256(name) != wanted:
            raise ValueError('source/input hash mismatch: '+str(name))


def journal(path, digest, identities):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows) > len(identities) or len({r['identity'] for r in rows}) != len(rows)
            or any(r['number'] != i+1 or r['manifest_sha256'] != digest or r['identity'] not in identities
                   for i, r in enumerate(rows))):
        raise ValueError('invalid prediction journal')
    return rows


def charge(path, identity, digest, identities):
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        rows = journal(path, digest, identities)
        if identity not in identities:
            raise ValueError('prediction outside frozen scope')
        if any(r['identity'] == identity for r in rows):
            raise ValueError('prediction already charged; no retry')
        if len(rows) >= len(identities):
            raise ValueError('prediction allowance exhausted')
        row = dict(number=len(rows)+1, identity=identity, manifest_sha256=digest)
        stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return row


def check_reproduction(fit, clock, physical, primary):
    if clock == 'nominal_200Hz' and not math.isclose(float(np.sum(primary**2)),
            fit['residual_sum_squares'], rel_tol=1e-6, abs_tol=1e-9):
        raise ValueError('saved nominal cost does not reproduce')
    field = 'residual_rms_neu_m' if clock == 'nominal_200Hz' else 'header_fixed_parameter_rms_neu_m'
    if not np.allclose(np.sqrt(np.mean(physical**2, axis=0)), fit[field], rtol=1e-6, atol=1e-8):
        raise ValueError('saved physical RMS does not reproduce')


def verify(output):
    manifest = base.load(output/'manifest.json')
    if (manifest['version'] != VERSION or manifest['targets'] != list(TARGETS)
            or manifest['maximum_predictions'] != 24 or manifest['maximum_optimizer_starts'] != 0
            or len(manifest['identities']) != 24 or len(set(manifest['identities'])) != 24):
        raise ValueError('diagnostic freeze scope changed')
    check_hashes(manifest['inputs']); check_hashes(manifest['sources'])
    base.runtime.check_environment(manifest['environment'])
    for name, digest in manifest['sources'].items():
        if base.il.sha256(output/'source-freeze'/Path(name).name) != digest:
            raise ValueError('diagnostic source snapshot changed')
    return manifest


def prepare(output):
    if (output/'manifest.json').exists():
        return verify(output)
    for directory in (BASELINE, TRIAL):
        audit.verify_artifacts(directory, base.load(directory/'evidence-receipt.json'))
    old = base.load(BASELINE/'manifest.json'); trial = base.load(TRIAL/'manifest.json')
    base.runtime.check_environment(old['environment'])
    check_hashes(old['sources']); check_hashes(trial['inputs'])
    sources = dict(old['sources'])
    for path in (Path(__file__), Path(stats.__file__), Path(audit.__file__),
                 Path('analysis/tests/test_ilvis0_residuals.py'),
                 Path('analysis/tests/test_ilvis0_residual_diagnostic.py')):
        sources[str(path.resolve())] = base.il.sha256(path)
    inputs = dict(trial['inputs'])
    for path in (BASELINE/'public-summary-receipt.json', TRIAL/'evidence-receipt.json',
                 TRIAL/'manifest.json', TRIAL/'selection.json.gz', GUIDE/'PLAN.md'):
        inputs[str(path.resolve())] = base.il.sha256(path)
    selected = base.load(TRIAL/'selection.json.gz')['selected']
    summary = base.load(BASELINE/'summary.json.gz')
    results = {r['segment_id']: r for r in summary['results']}
    cases = base.load(BASELINE/'fit-manifest.json')['cases']
    identities = [sid+'::'+case['case_id']+'::'+model+'::'+clock for sid in TARGETS
                  for case in cases for model in base.explore.MODELS for clock in CLOCKS]
    if {r['segment']['segment_id'] for r in selected} != set(TARGETS):
        raise ValueError('trial targets changed')
    for row in selected:
        if row['segment'] != results[row['segment']['segment_id']]['segment']:
            raise ValueError('baseline/trial interval mismatch')
    (output/'source-freeze').mkdir(exist_ok=True)
    for name in sources:
        shutil.copyfile(name, output/'source-freeze'/Path(name).name)
    manifest = dict(version=VERSION, targets=list(TARGETS), identities=identities,
                    maximum_predictions=24, maximum_optimizer_starts=0, cases=cases,
                    environment=old['environment'], sources=sources, inputs=inputs,
                    value_kernel=old['value_kernel'], baseline_parameters_only=True,
                    scientific_decision='abstain', held_out_validation=False)
    base.follow.atomic_json(output/'manifest.json', manifest)
    return verify(output)


def csv_bytes(rows):
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
    writer.writeheader(); writer.writerows(rows)
    return stream.getvalue().encode()


def atomic_bytes(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('wb') as stream:
        stream.write(value); stream.flush(); os.fsync(stream.fileno())
    os.replace(temporary, path)


def covariates(times, gps):
    # Reference globe metric used only for descriptive receiver motion covariates.
    rates = np.column_stack([np.gradient(gps[:, 0], times),
                            np.gradient(np.unwrap(gps[:, 1]), times)])
    radius = 6378137.+gps[:, 2]
    north = rates[:, 0]*radius; east = rates[:, 1]*radius*np.cos(gps[:, 0])
    course = np.unwrap(np.arctan2(east, north))
    return dict(receiver_coordinate_speed_proxy_kmh=np.hypot(north, east)*3.6,
                receiver_course_rate_proxy_deg_s=np.degrees(np.gradient(course, times)),
                latitude_deg=np.degrees(gps[:, 0]), receiver_height_m=gps[:, 2],
                elapsed_s=times-times[0])


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        manifest = prepare(output); digest = base.il.sha256(output/'manifest.json')
        if (output/'completion.json').exists():
            raise ValueError('completed residual pass is frozen; package only')
        kernel, build = base.explore.load_kernel(output/'kernel')
        if build != manifest['value_kernel']:
            raise ValueError('native build differs from original; no predictions launched')
        selected = base.load(TRIAL/'selection.json.gz')['selected']
        previous = {r['segment_id']: r for r in base.load(BASELINE/'summary.json.gz')['results']}
        contexts = {r['task_id']: r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        grid = {a.name: a for a in base.sensitivity.assumptions()}; results = []
        for row in selected:
            segment = row['segment']; sid = segment['segment_id']
            values, times, gps, provenance = base.segments.extract_segment(
                Path(row['source_path']), contexts[row['task']], segment)
            if provenance != previous[sid]['provenance']:
                raise ValueError('extracted native provenance changed')
            blocks = np.tile(np.diag([.3**2, .3**2, .7**2]), (len(gps), 1, 1))
            covs = {name: base.sensitivity.coordinate_covariance(times, gps[:, 0], gps[:, 2], blocks, grid[name])
                    for name in ('h1_v3_tau60', 'h10_v30_tau300')}
            metric = np.column_stack((1/(6378137.+gps[:, 2]),
                      1/((6378137.+gps[:, 2])*np.cos(gps[:, 0])), np.ones(len(gps))))
            cov = covariates(times, gps)
            for case in manifest['cases']:
                old_case = next(c for c in previous[sid]['cases'] if c['case_id'] == case['case_id'])
                for model in base.explore.MODELS:
                    fit = next(f for f in old_case['fits'] if f['model'] == model)
                    audit.parameter_rows(fit, case['limits'], profile=case['profile'])
                    seed, _ = base.corpus.initialize(times, gps, values, model)
                    for clock in CLOCKS:
                        verify(output)
                        identity = sid+'::'+case['case_id']+'::'+model+'::'+clock
                        name = identity.replace('::', '-'); target = output/(name+'.json')
                        cached = base.cached(target, digest)
                        if cached is not None:
                            if 'residual_file' in cached:
                                check_hashes({str(output/cached['residual_file']): cached['residual_sha256']})
                            results.append(cached); continue
                        charges = journal(output/'predictions.jsonl', digest, manifest['identities'])
                        if any(r['identity'] == identity for r in charges):
                            result = dict(identity=identity, state='failed', error='interrupted charged prediction; no retry',
                                          scientific_decision='abstain')
                            base.save(target, result, digest); results.append(result); continue
                        dt = np.full(len(values), .005) if clock == 'nominal_200Hz' else values[:, 2]
                        kwargs = dict(fit_earth_removal=case['profile'], kernel=kernel,
                            clock_hypothesis=clock, processing_hypothesis='unsubtracted_increment_hypothesis',
                            maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
                        problem = base.explore.ConditionalProblem(values[:, 9:12], values[:, 12:15], dt,
                            times, gps, covs['h1_v3_tau60'], seed, base.estimator.Bounds(case['limits']), **kwargs)
                        conservative = base.explore.ConditionalProblem(values[:, 9:12], values[:, 12:15], dt,
                            times, gps, covs['h10_v30_tau300'], seed, base.estimator.Bounds(case['limits']), **kwargs)
                        if list(problem.bounds.active) != fit['active_parameters']:
                            raise ValueError('saved parameter order changed')
                        charged = charge(output/'predictions.jsonl', identity, digest, manifest['identities'])
                        base.follow.atomic_json(output/'status.json', dict(state='predicting', identity=identity,
                            pid=os.getpid(), charged_predictions=charged['number'], maximum_predictions=24))
                        begin = time.monotonic()
                        try:
                            prediction = problem.predict(np.array(fit['normalized_parameters']), model)
                            delta = prediction-gps; delta[:, 1] = (delta[:, 1]+math.pi)%(2*math.pi)-math.pi
                            physical = delta/metric
                            primary = problem.whiten(delta).reshape(-1, 3)
                            generous = conservative.whiten(delta).reshape(-1, 3)
                            check_reproduction(fit, clock, physical, primary)
                            report = stats.summarize(times, physical, primary, generous, cov)
                            epochs = []
                            for i in range(len(times)):
                                e = dict(epoch=i, time_utc_week_s=float(times[i]+provenance['first_interval_start_utc_s']),
                                    latitude_rad=float(gps[i, 0]), longitude_rad=float(gps[i, 1]), receiver_height_m=float(gps[i, 2]))
                                for j, axis in enumerate(('north', 'east', 'up')):
                                    e[axis+'_coordinate_residual'] = float(delta[i, j])
                                    e[axis+'_residual_m'] = float(physical[i, j])
                                    e[axis+'_primary_innovation'] = float(primary[i, j])
                                    e[axis+'_conservative_innovation'] = float(generous[i, j])
                                for key, vector in cov.items():
                                    e[key] = float(vector[i])
                                epochs.append(e)
                            residual_file = name+'.csv.gz'
                            atomic_bytes(output/residual_file, gzip.compress(csv_bytes(epochs), mtime=0))
                            result = dict(identity=identity, state='complete', segment_id=sid, filename=row['filename'],
                                case_id=case['case_id'], model=model, clock=clock, baseline_status=audit.fit_status(fit),
                                imu_type=segment['imu_type'], duration_s=segment['duration_s'],
                                median_ground_speed_kmh=segment['median_receiver_ground_speed_kmh'],
                                source_sha256=provenance['source_sha256'], residual_file=residual_file,
                                residual_sha256=base.il.sha256(output/residual_file), report=report,
                                cost=float(np.sum(primary**2)), conservative_cost=float(np.sum(generous**2)),
                                native_predictions=1, optimizer_starts=0, elapsed_s=time.monotonic()-begin,
                                scientific_decision='abstain', baseline_reproduced=True)
                            base.save(target, result, digest); results.append(result)
                        except Exception as error:
                            base.save(target, dict(identity=identity, state='failed', scientific_decision='abstain',
                                      error=type(error).__name__+': '+str(error)), digest)
                            raise
                        print(json.dumps(dict(identity=identity, charged_predictions=charged['number'],
                                              elapsed_s=result['elapsed_s'])), flush=True)
        verify(output)
        base.follow.atomic_json(output/'summary.json', dict(version=VERSION, results=results,
            charged_predictions=len(journal(output/'predictions.jsonl', digest, manifest['identities'])),
            optimizer_starts=0, scientific_decision='abstain'))
        base.follow.atomic_json(output/'completion.json', dict(state='complete', manifest_sha256=digest,
            summary_sha256=base.il.sha256(output/'summary.json'), optimizer_starts=0))


def publish(output):
    manifest = verify(output); completion = base.load(output/'completion.json')
    digest = base.il.sha256(output/'manifest.json')
    if completion['manifest_sha256'] != digest or completion['summary_sha256'] != base.il.sha256(output/'summary.json'):
        raise ValueError('completion hash mismatch')
    summary = base.load(output/'summary.json')
    if summary['charged_predictions'] != len(journal(output/'predictions.jsonl', digest, manifest['identities'])):
        raise ValueError('charged prediction count mismatch')
    rows = []
    GUIDE.mkdir(parents=True, exist_ok=True)
    for result in summary['results']:
        if result['state'] != 'complete':
            continue
        check_hashes({str(output/result['residual_file']): result['residual_sha256']})
        shutil.copyfile(output/result['residual_file'], GUIDE/result['residual_file'])
        for axis in result['report']['axes']:
            lag = axis['autocorrelation'][0]
            rows.append(dict(identity=result['identity'], filename=result['filename'], segment_id=result['segment_id'],
                imu_type=result['imu_type'], duration_s=result['duration_s'], median_ground_speed_kmh=result['median_ground_speed_kmh'],
                model=result['model'], case_id=result['case_id'], clock=result['clock'], baseline_status=result['baseline_status'],
                axis=axis['axis'], epochs=result['report']['epochs'], physical_rms_m=axis['physical']['rms'],
                physical_mean_m=axis['physical']['mean'], primary_rms=axis['primary']['rms'],
                primary_centered_rms=axis['primary']['centered_rms'], primary_absolute_p95=axis['primary']['absolute_p95'],
                primary_absolute_max=axis['primary']['absolute_max'], primary_lag1_correlation=lag['primary'],
                conservative_rms=axis['conservative']['rms'], conservative_lag1_correlation=lag['conservative'],
                speed_proxy_rank_correlation=axis['associations']['receiver_coordinate_speed_proxy_kmh'],
                course_rate_proxy_rank_correlation=axis['associations']['receiver_course_rate_proxy_deg_s']))
    if rows:
        atomic_bytes(GUIDE/'diagnostics.csv', csv_bytes(rows))
    for name in ('manifest.json', 'summary.json', 'completion.json', 'predictions.jsonl'):
        shutil.copyfile(output/name, GUIDE/name)
    shutil.copytree(output/'source-freeze', GUIDE/'source-freeze', dirs_exist_ok=True)
    artifacts = [r['residual_file'] for r in summary['results'] if r['state'] == 'complete']
    artifacts += ['manifest.json', 'summary.json', 'completion.json', 'predictions.jsonl']
    if rows:
        artifacts.append('diagnostics.csv')
    base.follow.atomic_json(GUIDE/'evidence-receipt.json', dict(version=VERSION,
        manifest_sha256=digest, optimizer_starts=0, charged_predictions=summary['charged_predictions'],
        scientific_decision='abstain', artifacts={name: base.il.sha256(GUIDE/name) for name in artifacts}))
    print('Published saved-parameter residual diagnostics; zero optimizer starts.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    parser.add_argument('--package-only', action='store_true')
    args = parser.parse_args()
    if not args.package_only:
        run(args.output)
    publish(args.output)


if __name__ == '__main__':
    main()
