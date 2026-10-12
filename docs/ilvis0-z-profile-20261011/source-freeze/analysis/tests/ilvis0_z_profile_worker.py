# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separately budgeted joint calibration grid. Preparation/publication never fit data."""
import argparse
import fcntl
from html import escape
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
import ilvis0_integration_trial as infrastructure
from lll import ilvis0_integration_audit as audit
from lll import ilvis0_z_profile as profile

base = infrastructure.clock.base
ROOT = infrastructure.ROOT
REFERENCE = infrastructure.REFERENCE
TARGET = audit.TARGET
OUTPUT = Path('data/ilvis0-z-profile-20261011')
GUIDE = Path('docs/ilvis0-z-profile-20261011')
PLAN = Path('docs/ilvis0-integration-audit-20261011/PROFILE_PLAN.md')
VERSION = 'ilvis0-joint-z-profile-worker-v1'


def identities():
    return audit.profile_scope()['identities']


def coordinate(identity):
    if identity not in identities(): raise ValueError('outside fixed profile grid')
    parts = identity.split('::')
    return int(parts[3][4:]), int(parts[4][4:])


def scope():
    return dict(version=VERSION, identities=identities(), cases=[base.primary_cases()[0]],
        maximum_starts=27, maximum_per_identity=1, maximum_evaluations_per_start=200,
        maximum_native_sweeps=5400, retry_reserve=0, clock='header_elapsed',
        integration='original', initialization='zero_free_coordinates_then_frozen_stages',
        optimizer='frozen_original_fit_shape_candidate', numerical_threads=2)


def result_path(output, identity):
    coordinate(identity)
    return output/(identity.replace('::', '-')+'.json')


def journal(path, digest):
    rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    if (len(rows)>27 or len({r['identity'] for r in rows})!=len(rows) or
        any(r['number']!=i+1 or r['identity'] not in identities() or
            r['manifest_sha256']!=digest or r['maximum_evaluations']!=200 for i,r in enumerate(rows))):
        raise ValueError('invalid profile start journal')
    return rows


def charge(path, identity, digest):
    coordinate(identity)
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        rows = journal(path, digest)
        if len(rows)>=27 or any(r['identity']==identity for r in rows):
            raise ValueError('identity already charged or allowance spent; no retry')
        row = dict(number=len(rows)+1, identity=identity, manifest_sha256=digest, maximum_evaluations=200)
        stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return row


def verify(output):
    manifest = base.load(output/'manifest.json')
    if any(manifest.get(k)!=v for k,v in scope().items()):
        raise ValueError('profile freeze scope changed')
    infrastructure.clock.residuals.check_hashes(manifest['sources'])
    infrastructure.clock.residuals.check_hashes(manifest['inputs'])
    base.runtime.check_environment(manifest['environment'])
    for name, digest in manifest['sources'].items():
        if base.il.sha256(infrastructure.snapshot_path(output, name))!=digest:
            raise ValueError('profile source snapshot changed')
    if base.il.sha256(output/'selection.json.gz')!=manifest['selection_sha256']:
        raise ValueError('profile selection changed')
    return manifest


def prepare(output):
    output.mkdir(parents=True, exist_ok=True)
    if (output/'manifest.json').exists(): return verify(output)
    old = infrastructure.clock.verify(infrastructure.clock.OUTPUT)
    base.runtime.check_environment(old['environment'])
    infrastructure.clock.audit.verify_artifacts(REFERENCE, base.load(REFERENCE/'evidence-receipt.json'))
    done = base.load(REFERENCE/'completion.json')
    reference = base.load(REFERENCE/'summary.json')
    if (done['state']!='complete' or done['starts']!=6 or
        done['manifest_sha256']!=base.il.sha256(REFERENCE/'manifest.json') or
        done['summary_sha256']!=base.il.sha256(REFERENCE/'summary.json') or
        any(infrastructure.clock.audit.fit_status(f)!='converged' for c in reference['cases'] for f in c['fits'])):
        raise ValueError('reference is not the unchanged completed comparison')
    expected = {(c['case_id'],m) for c in base.primary_cases() for m in base.explore.MODELS}
    keys = [(c['case_id'],f['model']) for c in reference['cases'] for f in c['fits']]
    if len(keys)!=6 or set(keys)!=expected: raise ValueError('reference identities changed')
    sources, inputs = dict(old['sources']), dict(old['inputs'])
    for p in (Path(__file__), Path(infrastructure.__file__), Path(profile.__file__), Path(audit.__file__),
              Path(infrastructure.candidate.__file__), Path('analysis/lll/ilvis0_geographic_controls.py'),
              Path('analysis/tests/test_ilvis0_z_profile.py'), Path('analysis/tests/test_ilvis0_z_profile_worker.py')):
        sources[str(p.resolve())] = base.il.sha256(p)
    for p in (PLAN, GUIDE/'README.md', REFERENCE/'evidence-receipt.json', REFERENCE/'completion.json',
              REFERENCE/'manifest.json', REFERENCE/'summary.json', REFERENCE/'selection.json.gz'):
        inputs[str(p.resolve())] = base.il.sha256(p)
    shutil.copyfile(REFERENCE/'selection.json.gz', output/'selection.json.gz')
    for name in sources:
        dest = infrastructure.snapshot_path(output, name); dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, dest)
    base.follow.atomic_json(output/'manifest.json', dict(**scope(), sources=sources, inputs=inputs,
        environment=old['environment'], value_kernel=old['value_kernel'], tangent_kernel=old['tangent_kernel'],
        selection_sha256=base.il.sha256(output/'selection.json.gz'),
        reference_sha256=base.il.sha256(REFERENCE/'summary.json'), scientific_decision='abstain'))
    return verify(output)


def checked_cache(output, identity, digest):
    charged = any(r['identity']==identity for r in journal(output/'starts.jsonl', digest))
    fit = base.cached(result_path(output, identity), digest)
    if fit is not None:
        if not charged: raise ValueError('uncharged saved profile')
        if fit.get('residual_file'):
            p = output/fit['residual_file']
            if p.resolve().parent!=output.resolve(): raise ValueError('residual outside profile directory')
            infrastructure.clock.residuals.check_hashes({str(p): fit['residual_sha256']})
        return fit
    if charged:
        fit = dict(identity=identity, model=identity.split('::')[2], converged=False,
            error='interrupted charged start; no retry', evaluations=None,
            charged_native_sweep_allowance=200, scientific_decision='abstain')
        base.save(result_path(output, identity), fit, digest)
        return fit
    return None


def fit_one(output, identity, values, times, gps, provenance, covs, metric, kernel, tangent):
    case = scope()['cases'][0]; model = identity.split('::')[2]
    gain, bias = coordinate(identity); result = {}; budget = None
    try:
        seed, _ = base.corpus.initialize(times, gps, values, model)
        args = (values[:,9:12], values[:,12:15], values[:,2], times, gps)
        kwargs = dict(fit_earth_removal=False, kernel=kernel, tangent_kernel=tangent,
            clock_hypothesis='header_elapsed', processing_hypothesis='unsubtracted_increment_hypothesis',
            maximum_interval_s=.0075, gravity_mps2=9.81, disc_radius_m=6371000.)
        problem = base.shape.TangentProblem(*args, covs['h1_v3_tau60'], seed,
            base.estimator.Bounds(case['limits']), **kwargs)
        fixed = profile.FixedProblem(problem, {'gyro_gain_z': gain/2., 'gyro_bias_z': float(bias)})
        budget = infrastructure.NativeBudget(fixed)
        result = base.shape.fit_shape_candidate(budget, model,
            start=np.zeros(len(fixed.bounds.active)), maximum_evaluations=200)
        point = np.array(result['normalized_parameters']); full = fixed.expand(point)
        result.update(fixed.diagnostics(point, model))
        if not math.isclose(result['saved_stationarity'], result['exact_projected_gradient_relative'], rel_tol=1e-8, abs_tol=1e-15):
            raise ValueError('free diagnostic stationarity disagrees with fitter')
        prediction = budget.predict(problem, full, model)
        # Diagnostic only: no optimization under the nominal clock.
        nominal = base.shape.TangentProblem(values[:,9:12], values[:,12:15], np.full(len(values), .005),
            times, gps, covs['h1_v3_tau60'], seed, base.estimator.Bounds(case['limits']),
            **dict(kwargs, clock_hypothesis='nominal_200Hz'))
        nominal_prediction = budget.predict(nominal, full, model)
        delta = prediction-gps; delta[:,1] = (delta[:,1]+math.pi)%(2*math.pi)-math.pi
        nominal_delta = nominal_prediction-gps
        nominal_delta[:,1] = (nominal_delta[:,1]+math.pi)%(2*math.pi)-math.pi
        physical = delta/metric; primary = problem.whiten(delta).reshape(-1,3)
        if not math.isclose(float(np.sum(primary**2)), result['residual_sum_squares'], rel_tol=1e-6, abs_tol=1e-9):
            raise ValueError('profile value/tangent objective disagreement')
        rows = []
        for i, t in enumerate(times):
            row = dict(epoch=i, time_utc_week_s=float(t+provenance['first_interval_start_utc_s']))
            for j, axis in enumerate(('north','east','up')):
                row[axis+'_residual_m'] = float(physical[i,j])
                row[axis+'_coordinate_residual'] = float(delta[i,j])
                row[axis+'_primary_innovation'] = float(primary[i,j])
            rows.append(row)
        name = identity.replace('::','-')+'.csv.gz'
        residuals = infrastructure.clock.residuals
        residuals.atomic_bytes(output/name, residuals.gzip.compress(residuals.csv_bytes(rows), mtime=0))
        result.update(residual_file=name, residual_sha256=base.il.sha256(output/name),
            residual_rms_neu_m=np.sqrt(np.mean(physical**2, axis=0)).tolist(),
            nominal_fixed_parameter_rms_neu_m=np.sqrt(np.mean((nominal_delta/metric)**2, axis=0)).tolist())
    except Exception as error:
        result.update(converged=False, error=type(error).__name__+': '+str(error))
    result.update(identity=identity, model=model, case_id=case['case_id'],
        fixed_z_gain_percent=gain, fixed_z_bias_dph=bias, evaluations=budget.used if budget else 0,
        actual_tangent_sweeps=budget.tangents if budget else 0, diagnostic_predictions=budget.values if budget else 0,
        maximum_evaluations=200, scientific_decision='abstain', scientific_eligible=False)
    return result


def grid_svg(table, *, increases=False):
    """Nine observed grid nodes, without interpolated contours or unfinished minima."""
    values = {}
    for model in audit.MODELS:
        good = [r['cost'] for r in table if r['model']==model and r['status']=='converged' and r['cost'] is not None]
        reference = min(good) if good else None
        for r in table:
            if r['model']==model:
                cost = r['cost']
                value = (cost-reference if increases else cost) if r['status']=='converged' and reference is not None else None
                values[(model,r['gain_percent'],r['bias_dph'])] = (r,value)
    largest = max((v for _,v in values.values() if v is not None), default=0.)
    denominator = math.log1p(max(largest,0.)) or 1.
    title = 'Cost increase above each completed grid minimum' if increases else 'Absolute achieved cost at fixed Z corrections'
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="400" viewBox="0 0 1050 400">',
        '<rect width="1050" height="400" fill="white"/>',
        f'<text x="20" y="28" font-family="sans-serif" font-size="18">{title}</text>']
    for panel,model in enumerate(audit.MODELS):
        left = 30+panel*345
        lines.append(f'<text x="{left}" y="62" font-family="sans-serif" font-size="15">{escape(model)}</text>')
        for gain in (-2,0,2):
            y = 85+(2-gain)//2*70
            lines.append(f'<text x="{left}" y="{y+30}" font-family="sans-serif" font-size="12">{gain:+d}%</text>')
            for bias in (-1,0,1):
                x = left+38+(bias+1)*90
                r,value = values[(model,gain,bias)]
                color = '#eeeeee' if value is None else f'hsl(210, 65%, {95-45*math.log1p(max(value,0.))/denominator:.1f}%)'
                label = f'{value:.5g}' if value is not None else (f"{r['cost']:.5g} / {r['status']}" if r['cost'] is not None else r['status'])
                lines.append(f'<rect x="{x}" y="{y}" width="88" height="68" fill="{color}" stroke="#666"/>')
                lines.append(f'<text x="{x+4}" y="{y+35}" font-family="sans-serif" font-size="9">{escape(label)}</text>')
                if gain==-2:
                    lines.append(f'<text x="{x+35}" y="325" font-family="sans-serif" font-size="12">{bias:+d}</text>')
        lines.append(f'<text x="{left+40}" y="350" font-family="sans-serif" font-size="12">Z offset (degrees/hour); rows: Z gain</text>')
    lines.append('<text x="20" y="382" font-family="sans-serif" font-size="12">Common logarithmic color scale; gray = unfinished (raw achieved cost). Grid nodes are not confidence contours.</text>')
    lines.append('</svg>')
    return '\n'.join(lines)+'\n'


def run(output, lock_fd=None):
    output.mkdir(parents=True, exist_ok=True)
    lock = os.fdopen(lock_fd,'a') if lock_fd is not None else (output/'worker.lock').open('a')
    with lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists(): raise ValueError('completed profile is frozen; package only')
        manifest = prepare(output); digest = base.il.sha256(output/'manifest.json')
        kernel, build = base.explore.load_kernel(output/'kernel')
        tangent, tangent_build = base.shape.load_tangent(output/'kernel')
        if build!=manifest['value_kernel'] or tangent_build!=manifest['tangent_kernel']:
            raise ValueError('profile native build differs from reference')
        chosen = base.load(output/'selection.json.gz')['selected'][0]
        contexts = {r['task_id']: r for r in base.load('data/ilvis0-followup-20261007/summary.json')['results']}
        values,times,gps,provenance = base.segments.extract_segment(
            Path(chosen['source_path']), contexts[chosen['task']], chosen['segment'])
        reference = base.load(REFERENCE/'summary.json')
        if provenance!=reference['provenance']: raise ValueError('profile extraction changed')
        blocks = np.tile(np.diag([.3**2,.3**2,.7**2]), (len(gps),1,1))
        assumption = next(a for a in base.sensitivity.assumptions() if a.name=='h1_v3_tau60')
        covs = {'h1_v3_tau60': base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumption)}
        metric = np.column_stack((1/(6378137.+gps[:,2]), 1/((6378137.+gps[:,2])*np.cos(gps[:,0])), np.ones(len(gps))))
        fits = []
        for identity in identities():
            verify(output)
            fit = checked_cache(output, identity, digest)
            if fit is None:
                charged = charge(output/'starts.jsonl', identity, digest); begin = time.monotonic()
                base.follow.atomic_json(output/'status.json', dict(state='fitting', identity=identity,
                    pid=os.getpid(), charged_starts=charged['number'], maximum_starts=27))
                fit = fit_one(output,identity,values,times,gps,provenance,covs,metric,kernel,tangent)
                fit.update(start_charge=charged, elapsed_s=time.monotonic()-begin)
                verify(output); base.save(result_path(output,identity), fit, digest)
                print(json.dumps(dict(identity=identity, converged=fit['converged'], error=fit.get('error'))), flush=True)
            fits.append(fit)
        rows = [dict(case_id=f'z_gain{a:+d}_offset{b:+d}',
            fits=[f for f in fits if coordinate(f['identity'])==(a,b)]) for a in (-2,0,2) for b in (-1,0,1)]
        summary = dict(version=VERSION,state='complete',starts=len(journal(output/'starts.jsonl',digest)),
            fits=fits,cases=rows,profile=base.shape.hierarchical_profile(rows),provenance=provenance,
            unrestricted_reference=reference,scientific_decision='abstain')
        if summary['starts']!=27: raise ValueError('incomplete profile start ledger')
        base.follow.atomic_json(output/'summary.json',summary)
        base.follow.atomic_json(output/'completion.json',dict(state='complete',starts=27,
            manifest_sha256=digest,summary_sha256=base.il.sha256(output/'summary.json'),scientific_decision='abstain'))
        base.follow.atomic_json(output/'status.json',dict(state='complete',pid=os.getpid(),charged_starts=27,
            converged=sum(infrastructure.clock.audit.fit_status(f)=='converged' for f in fits)))


def publish(output):
    manifest=verify(output); digest=base.il.sha256(output/'manifest.json')
    done=base.load(output/'completion.json')
    if (done['state']!='complete' or done['starts']!=27 or len(journal(output/'starts.jsonl',digest))!=27 or
        done['manifest_sha256']!=digest or done['summary_sha256']!=base.il.sha256(output/'summary.json')):
        raise ValueError('profile completion mismatch')
    summary=base.load(output/'summary.json')
    if [f['identity'] for f in summary['fits']]!=identities(): raise ValueError('profile identities differ')
    names=['manifest.json','selection.json.gz','summary.json','completion.json','starts.jsonl']
    table=[]
    for f in summary['fits']:
        if checked_cache(output,f['identity'],digest)!=f: raise ValueError('saved profile differs from summary')
        if f.get('residual_file'): names.append(f['residual_file'])
        gain,bias=coordinate(f['identity']); rms=f.get('residual_rms_neu_m')
        table.append(dict(identity=f['identity'],model=f['model'],gain_percent=gain,bias_dph=bias,
            status=infrastructure.clock.audit.fit_status(f),cost=f.get('residual_sum_squares'),
            horizontal_rms_m=math.hypot(*rms[:2]) if rms else None,vertical_rms_m=rms[2] if rms else None,
            stationarity=f.get('exact_projected_gradient_relative'),active_free_bounds=len(f.get('active_bounds',[])),
            native_sweeps=f.get('evaluations'),error=f.get('error')))
    GUIDE.mkdir(parents=True,exist_ok=True)
    for name in names: shutil.copyfile(output/name,GUIDE/name)
    shutil.copytree(output/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    with (GUIDE/'profiles.csv').open('w',newline='') as stream:
        import csv
        writer=csv.DictWriter(stream,fieldnames=list(table[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(table)
    names.append('profiles.csv')
    for name, increases in (('profile-grid.svg',False),('profile-increases.svg',True)):
        (GUIDE/name).write_text(grid_svg(table,increases=increases)); names.append(name)
    lines=['# Joint Z-axis profile results','',
        'Completed 27 charged starts on one recording and one processing case. All failures remain recorded.',
        'IMU means inertial measurement unit. The fixed gain/offset grid tests calibration sensitivity, not instrument drift.',
        '', '| Model | Gain (%) | Offset (degrees/hour) | Status | Achieved cost |', '|---|---:|---:|---|---:|']
    for row in table:
        cost=f"{row['cost']:.6g}" if row['cost'] is not None else 'unavailable'
        lines.append(f"| {row['model']} | {row['gain_percent']} | {row['bias_dph']} | {row['status']} | {cost} |")
    lines+=['',f"Complete-grid shape preference: **{summary['profile']['conditional_shape_preference']}**.",
        'Unfinished points give upper bounds on their unknown best fits; they do not complete a profile surface.',
        '', '![Absolute achieved cost](profile-grid.svg)', '',
        '![Increases above the completed grid minima](profile-increases.svg)', '',
        'Figures show the nine grid nodes without interpolating unfinished points. Gray nodes retain raw achieved costs.',
        'The coarse grid cannot establish a global optimum or calibrated confidence region.',
        'Model names specify background fields, not their cause. Other processing cases, clocks and recordings remain untested.',
        '', '[Preparation and reproduction instructions](README.md). All scientific decisions abstain.']
    (GUIDE/'RESULTS.md').write_text('\n'.join(lines)+'\n'); names.append('RESULTS.md')
    artifacts={n:base.il.sha256(GUIDE/n) for n in names}
    for name in manifest['sources']:
        p=infrastructure.snapshot_path(GUIDE,name); artifacts[str(p.relative_to(GUIDE))]=base.il.sha256(p)
    base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(version=VERSION,artifacts=artifacts,scientific_decision='abstain'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare-only','package-only','run','detach'): actions.add_argument('--'+name,action='store_true')
    parser.add_argument('--lock-fd',type=int); args=parser.parse_args()
    if args.lock_fd is not None and not args.run: parser.error('--lock-fd requires --run')
    if args.package_only: publish(OUTPUT); return
    if args.run: run(OUTPUT,args.lock_fd); publish(OUTPUT); return
    OUTPUT.mkdir(parents=True,exist_ok=True)
    with (OUTPUT/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists(): raise ValueError('completed profile is frozen')
        prepare(OUTPUT)
        if args.prepare_only:
            print('Prepared 27-identity profile freeze; zero starts charged.'); return
        with (OUTPUT/'worker.log').open('ab') as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--run','--lock-fd',str(lock.fileno())],
                cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                pass_fds=(lock.fileno(),),start_new_session=True)
        base.follow.atomic_json(OUTPUT/'worker.json',dict(pid=child.pid,
            manifest_sha256=base.il.sha256(OUTPUT/'manifest.json'),maximum_starts=27))
    print('Profile worker launched with inherited exclusive lock.')


if __name__=='__main__': main()
