# SPDX-License-Identifier: AGPL-3.0-or-later
"""Durable short software controls and cached flight characterization; no Earth fits."""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

import numpy as np

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_forward as forward
from lll import ilvis0_estimator as estimator, ilvis0_estimator_controls as controls
from lll import ilvis0_observation as observation, models, runtime


def load(path):
    with gzip.open(path, 'rt') if str(path).endswith('.gz') else Path(path).open() as source:
        return json.load(source)


def result_hash(result):
    return hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()


def characterize_factors(report, artifact):
    forward.verify_factor_report(report, artifact, report['task_id'], report['provenance']['source_sha256'])
    factors = load(artifact)['factors']
    fixes = {}
    for factor in factors:
        for fix in (factor['receiver_start'], factor['receiver_end']):
            if fix:
                time = fix['utc_week_s']
                if time in fixes and fixes[time] != fix:
                    # Endpoint association offsets may differ; original receiver
                    # observation identity/values must nevertheless agree exactly.
                    for key in ('nmea_sentence', 'latitude_deg', 'longitude_deg', 'orthometric_height_m'):
                        if fixes[time][key] != fix[key]:
                            raise ValueError('inconsistent duplicate receiver observation')
                fixes[time] = fix
    fixes = [fixes[t] for t in sorted(fixes)]
    heights = [f['orthometric_height_m'] for f in fixes if f['orthometric_height_m'] is not None]
    speeds = []
    for first, second in zip(fixes, fixes[1:]):
        dt = second['utc_week_s']-first['utc_week_s']
        if not 0 < dt <= 2:
            continue
        phi = np.deg2rad((first['latitude_deg']+second['latitude_deg'])/2)
        h = (first['ellipsoid_height_m']+second['ellipsoid_height_m'])/2 if (
            first['ellipsoid_height_m'] is not None and second['ellipsoid_height_m'] is not None) else 0.
        rm, rn = models.radii(phi)
        dphi = np.deg2rad(second['latitude_deg']-first['latitude_deg'])
        dlambda = np.deg2rad(second['longitude_deg']-first['longitude_deg'])
        dlambda = (dlambda+np.pi)%(2*np.pi)-np.pi
        speeds.append(np.hypot((rm+h)*dphi, (rn+h)*np.cos(phi)*dlambda)/dt)
    def stats(values):
        return dict(zip(('min', 'median', 'max'), map(float, np.percentile(values, [0, 50, 100])))) if values else None
    return dict(task_id=report['task_id'], filename=report['filename'], receiver_fixes=len(fixes),
        gps_height_above_mean_sea_level_m=stats(heights), gps_ground_speed_mps=stats(speeds),
        speed_method='adjacent actual GPS positions <=2 seconds; conditional globe metric with altitude',
        altitude_above_terrain_known=False, airspeed_known=False, whole_flight_summary=False,
        processing_independence_established=False, calibration_bounds_established=False,
        receiver_covariance_established=False, clock_hypothesis_established=False,
        prior_marginal_scale_failure=(report['task_id']=='f166954fecd1d93111ee'),
        pairwise_decisions={name:'abstain' for name in ('rotating__still_globe', 'rotating_globe__disc', 'still_globe__disc')},
        empirical_earth_fit_attempts=0, source_sha256=report['provenance']['source_sha256'])


def run(root, output):
    output.mkdir(parents=True, exist_ok=True)
    lock = (output/'worker.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    prior = root/'docs/ilvis0-forward-20261007'
    old_manifest = load(prior/'manifest.json')
    sources = {str(Path(p)):il.sha256(Path(p)) for p in old_manifest['sources']}
    for path in (Path(estimator.__file__), Path(controls.__file__), Path(__file__),
                 root/'analysis/tests/test_ilvis0_estimator.py', Path(runtime.__file__)):
        sources[str(path)] = il.sha256(path)
    if any(sources[p] != digest for p, digest in old_manifest['sources'].items()):
        raise ValueError('frozen forward dependency changed; do not reuse completed preparation')
    summary = load(prior/'summary.json.gz')
    artifacts = {r['task_id']: prior/'factors'/f"{r['task_id']}-factors.json.gz" for r in summary['results']}
    inputs = {str(p):il.sha256(p) for p in [prior/'manifest.json', prior/'summary.json.gz',
        root/'docs/ilvis0-followup-20261007/summary.json.gz', *artifacts.values()]}
    manifest = dict(version=estimator.VERSION, sources=sources, inputs=inputs,
        environment=runtime.numerical_environment(), cases=controls.CASES,
        scope='five short analytic software controls, pairwise software design and cached route summaries',
        maximum_control_starts=10, maximum_evaluations_per_control=160,
        observed_earth_fit_attempts=0, scientific_eligibility_changes=0)
    manifest_path = output/'manifest.json'
    if manifest_path.exists():
        if load(manifest_path) != manifest:
            raise ValueError('source/input/environment changed; use a new identified output')
        if (output/'completion.json').exists():
            raise ValueError('completed controls are frozen; do not resume')
    else:
        follow.atomic_json(manifest_path, manifest)
        snapshots = output/'source-freeze'
        snapshots.mkdir()
        for p in sources:
            shutil.copyfile(p, snapshots/Path(p).name)
    def verify():
        if any(il.sha256(Path(p)) != digest for p, digest in {**sources, **inputs}.items()):
            raise ValueError('frozen source/input changed during control execution')
        if runtime.numerical_environment() != manifest['environment']:
            raise ValueError('numerical environment changed')
    results = {}
    for name in controls.CASES:
        verify()
        target = output/f'{name}.json'
        if target.exists():
            saved = load(target)
            if saved['manifest_sha256'] != il.sha256(manifest_path) or saved['case'] != name or (
                saved.get('result_sha256') != result_hash(saved['result'])):
                raise ValueError('corrupt or incompatible completed control')
            results[name] = saved['result']
            continue
        # A separate development ledger, not the empirical Earth-start ledger.
        journal_path = output/'control-starts.jsonl'
        with journal_path.open('a+') as journal:
            journal.seek(0)
            rows = [json.loads(line) for line in journal]
            if any(r.get('manifest_sha256') != il.sha256(manifest_path) or r.get('start') != i+1
                   or r.get('case') not in controls.CASES for i, r in enumerate(rows)):
                raise ValueError('corrupt control start journal')
            if len(rows) >= 10 or sum(r['case']==name for r in rows) >= 2:
                raise ValueError('bounded control retry allowance exhausted')
            journal.write(json.dumps(dict(start=len(rows)+1, case=name,
                manifest_sha256=il.sha256(manifest_path)), sort_keys=True)+'\n')
            journal.flush()
            os.fsync(journal.fileno())
            directory = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        follow.atomic_json(output/'status.json', dict(state='running', case=name, completed=list(results)))
        result = estimator.fit_control(controls.problem_for(name), 'flat_still', maximum_evaluations=160)
        case = controls.CASES[name]
        if case['truth']:
            passed = result['converged'] and result['nuisance_fully_observable'] and all(
                abs(result['parameters'][k]-v) <= case['tolerance'] for k,v in case['truth'].items())
        else:
            passed = not result['nuisance_fully_observable']
        result.update(control_passed=passed, truth=case['truth'], recovery_tolerance=case['tolerance'])
        verify()
        follow.atomic_json(target, dict(manifest_sha256=il.sha256(manifest_path), case=name,
                                       result=result, result_sha256=result_hash(result)))
        results[name] = result
    flights = [characterize_factors(r, artifacts[r['task_id']]) for r in summary['results']]
    windows = [w for r in load(root/'docs/ilvis0-followup-20261007/summary.json.gz')['results'] for w in r['performance']]
    aggregates = {}
    for key in ('altitude_m', 'speed_mps', 'latitude_deg', 'horizontal_globe_transport_deg_h'):
        aggregates[key] = dict(min=min(w[key]['min'] for w in windows),
            max=max(w[key]['max'] for w in windows),
            median_of_window_medians=float(np.median([w[key]['median'] for w in windows])))
    report = dict(version=estimator.VERSION, state='complete', controls=results,
        control_failures=sum(not r['control_passed'] for r in results.values()),
        pairwise_software_design=controls.controlled_pairwise_design(), flights=flights,
        previous_candidate_windows=dict(count=len(windows), statistics=aggregates,
            context='fused navigation motion context; overlapping instruments; not full flight population'),
        observed_earth_fit_attempts=0, scientific_eligibility_changes=0, originals_deleted=0)
    verify()
    observation.gzip_json(output/'summary.json.gz', report)
    follow.atomic_json(output/'completion.json', dict(version=estimator.VERSION, state='complete',
        controls=len(results), control_failures=report['control_failures'], files=len(flights),
        summary_sha256=il.sha256(output/'summary.json.gz'), manifest_sha256=il.sha256(manifest_path),
        observed_earth_fit_attempts=0, scientific_eligibility_changes=0, originals_deleted=0))
    follow.atomic_json(output/'status.json', dict(state='complete', controls=len(results)))
    fcntl.flock(lock, fcntl.LOCK_UN)
    lock.close()
    print(json.dumps(load(output/'completion.json'), sort_keys=True))
    if report['control_failures']:
        raise ValueError('one or more controls failed; preserve failed evidence')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/ilvis0-estimator-20261007'))
    args = parser.parse_args()
    run(Path(__file__).resolve().parents[2], args.output.resolve())
