# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit and package the completed shape refinement, with no fits or predictions."""
import argparse
from collections import Counter
import csv
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from lll import ilvis0 as il, ilvis0_followup as follow, ilvis0_shape as shape
from lll import runtime


def load(path): return json.loads(Path(path).read_text())


def result_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def verified_result(path,digest):
    row=load(path)
    if row['manifest_sha256']!=digest or result_hash(row['result'])!=row['result_sha256']:
        raise ValueError('per-result integrity failure')
    return row['result']


def audit(source):
    """Audit frozen evidence and attempt budgets before emitting a report."""
    complete=load(source/'completion.json');manifest=load(source/'manifest.json')
    digest=il.sha256(source/'manifest.json')
    if (complete['state']!='complete' or complete['files']!=6
            or manifest['maximum_files']!=6 or manifest['primary_starts']!=72
            or manifest['maximum_starts']!=84 or manifest['maximum_starts_per_identity']!=2
            or manifest['maximum_evaluations_per_start']!=200
            or complete['manifest_sha256']!=digest
            or complete['summary_sha256']!=il.sha256(source/'summary.json.gz')):
        raise ValueError('completion/frozen scope mismatch')
    for name,expected in {**manifest['sources'],**manifest['inputs']}.items():
        if il.sha256(name)!=expected:raise ValueError('frozen source/input changed')
    if runtime.numerical_environment()!=manifest['environment']:
        raise ValueError('frozen numerical environment changed')
    tasks=manifest['tasks'];cases=manifest['cases']
    if len(tasks)!=6 or len(set(tasks))!=6 or len(cases)!=4 or len({c['case_id'] for c in cases})!=4:
        raise ValueError('missing/duplicate frozen tasks or cases')
    if {(c['constant_gyro_bias_bound_dph'],c['fit_earth_removal']) for c in cases}!={(b,p) for b in (.1,1.) for p in (False,True)}:
        raise ValueError('unexpected sensitivity grid')
    expected={t+'::'+c['case_id']+'::'+m for t in tasks for c in cases for m in shape.explore.MODELS}
    if set(manifest['identities'])!=expected or len(manifest['identities'])!=72:
        raise ValueError('frozen identity grid mismatch')
    starts=[json.loads(line) for line in (source/'starts.jsonl').read_text().splitlines()]
    if (not 72<=len(starts)<=84 or len(starts)!=complete['starts']
            or any(n>2 for n in Counter(r['identity'] for r in starts).values())
            or any(r['start']!=i+1 or r['manifest_sha256']!=digest or r['identity'] not in expected
                   or r['maximum_evaluations']!=200 for i,r in enumerate(starts))):
        raise ValueError('attempt accounting mismatch')
    with gzip.open(source/'summary.json.gz','rt') as stream:summary=json.load(stream)
    if (summary['state']!='complete' or len(summary['results'])!=6
            or {r['task'] for r in summary['results']}!=set(tasks)
            or summary['scientific_shape_decision']!='abstain'
            or summary['scientific_rotation_decision']!='abstain'
            or summary['originals_deleted']!=0):raise ValueError('invalid summary/promotion/deletion')
    seen=set();references=set();converged=0;failed=0
    for row in summary['results']:
        if verified_result(source/(row['task']+'.json'),digest)!=row or not row['original_preserved']:
            raise ValueError('per-file summary differs or original not preserved')
        if len(row['cases'])!=4 or {c['case_id'] for c in row['cases']}!={c['case_id'] for c in cases}:
            raise ValueError('per-file assumption cases incomplete')
        if row['profile']!=shape.hierarchical_profile(row['cases']):
            raise ValueError('shape/rotation hierarchy differs from recomputed profile')
        for case in row['cases']:
            if len(case['fits'])!=3:raise ValueError('incomplete model profiles')
            for fit in case['fits']:
                identity=row['task']+'::'+case['case_id']+'::'+fit['model']
                if identity not in expected or identity in seen:raise ValueError('unknown/duplicate fitted identity')
                seen.add(identity)
                if verified_result(source/(identity.replace('::','-')+'.json'),digest)!=fit:
                    raise ValueError('per-fit summary differs')
                charge=fit['start_charge'];n=charge['start']
                if not 1<=n<=len(starts) or charge!=starts[n-1] or charge['identity']!=identity or n in references:
                    raise ValueError('fit/start identity mismatch')
                references.add(n)
                if fit.get('scientific_eligible',False) or fit['scientific_decision']!='abstain':
                    raise ValueError('unjustified scientific promotion')
                if 'error' in fit:
                    failed+=1
                    if fit.get('converged'):raise ValueError('failed fit marked converged')
                else:
                    if (not isinstance(fit['evaluations'],int) or not 1<=fit['evaluations']<=200
                            or not math.isfinite(fit['residual_sum_squares']) or fit['residual_sum_squares']<0
                            or not math.isfinite(fit['exact_projected_gradient_relative'])):
                        raise ValueError('invalid fit budget or diagnostics')
                    if fit['converged']:
                        if not fit['solver_reported_success'] or fit['exact_projected_gradient_relative']>1e-4:
                            raise ValueError('false numerical convergence')
                        converged+=1
    if seen!=expected:raise ValueError('missing fit outcomes')
    for value in (summary,complete):
        if value['converged_fits']!=converged or value['failed_fits']!=failed or value['starts']!=len(starts):
            raise ValueError('completion counts differ from audited outcomes')
    return manifest,complete,summary,dict(fits=72,charged_starts=len(starts),
        unreferenced_interrupted_starts=len(starts)-len(references),converged_fits=converged,failed_fits=failed)


def package(root):
    source=root/'data/ilvis0-shape-refinement-20261008';dest=Path(__file__).resolve().parent
    manifest,complete,summary,counts=audit(source)
    rows=[];shape_rows=[];rotation_rows=[]
    for row in summary['results']:
        profile=row['profile']
        for contrast in profile['shape_profiles']:
            shape_rows.append(dict(filename=row['filename'],task=row['task'],case_id=contrast['case_id'],
                conditional_disc_minus_globe_cost=contrast['conditional_disc_minus_globe_cost'],
                unresolved_optimizations=';'.join(contrast['unresolved_optimizations']),
                conditional_shape_preference=profile['conditional_shape_preference'],scientific_decision='abstain'))
        for r in profile['rotation_diagnostics'] or []:
            rotation_rows.append(dict(filename=row['filename'],task=row['task'],**r,scientific_decision='abstain'))
        for case in row['cases']:
            for f in case['fits']:
                p=f.get('parameters',{})
                rows.append(dict(filename=row['filename'],task=row['task'],case_id=case['case_id'],model=f['model'],
                    converged=f.get('converged',False),evaluations=f.get('evaluations'),
                    cost=f.get('residual_sum_squares'),stationarity=f.get('exact_projected_gradient_relative'),
                    rms_neu_m=json.dumps(f.get('residual_rms_neu_m')),
                    fitted_constant_bias_dph=json.dumps([p.get('gyro_bias_'+a,0)*180/math.pi*3600 for a in ('x','y','z')]) if p else '',
                    earth_removal=p.get('earth_removal'),active_bounds=';'.join(f.get('active_bounds',[])),error=f.get('error','')))
    for name,values,fields in [
        ('fits.csv',rows,['filename','task','case_id','model','converged','evaluations','cost','stationarity',
            'rms_neu_m','fitted_constant_bias_dph','earth_removal','active_bounds','error']),
        ('shape.csv',shape_rows,['filename','task','case_id','conditional_disc_minus_globe_cost',
            'unresolved_optimizations','conditional_shape_preference','scientific_decision']),
        ('rotation.csv',rotation_rows,['filename','task','case_id','conditional_still_minus_rotating_cost','scientific_decision'])]:
        with (dest/name).open('w',newline='') as out:
            writer=csv.DictWriter(out,fieldnames=fields);writer.writeheader();writer.writerows(values)
    lines=['# Shape-first refinement results','',
        f"Six recordings, four matched assumption cases each: {counts['converged_fits']}/72 fits converged, "
        f"{counts['failed_fits']} failed. {counts['charged_starts']} starts were charged, including "
        f"{counts['unreferenced_interrupted_starts']} interrupted starts without a retained final fit.",'',
        'These are conditional local fits, not a calibrated detection or a guarantee of global minima. '
        'Constant fitted offsets are not measured time-varying IMU drift. The offset assumptions are '
        '±0.1 and ±1 degree/hour, each tested with zero or freely fitted common Earth-rate removal.','',
        '| Recording | Shape preference across all cases | Converged fits | Rotation diagnostics |',
        '|---|---|---:|---|']
    for row in summary['results']:
        p=row['profile'];n=sum(bool(f.get('converged')) for c in row['cases'] for f in c['fits'])
        lines.append(f"| {row['filename']} | {p['conditional_shape_preference']} | {n}/12 | "
            f"{'available conditionally' if p['rotation_diagnostics'] is not None else 'withheld'} |")
    lines += ['', '[Shape contrasts](shape.csv) are reported first. [Rotation contrasts](rotation.csv) '
        'contain only recordings whose shape comparisons consistently favor globe after convergence '
        'in every case. An empty rotation table means that stage remained withheld. '
        '[Fit details](fits.csv) preserve convergence, fitted constant offsets, boundary hits and failures.','',
        'All scientific decisions abstain. Instrument processing, calibration, clock and receiver '
        'uncertainty remain partly assumed. Fused navigation never serves as an independent '
        'observation. The six recordings are development cases, not six independent validation trials.','',
        'The original data and older freezes remain unchanged. No further fit, synthetic campaign '
        'or calibrated-policy promotion is performed by this report. See the '
        '[refinement methods and limitations](README.md) before interpreting a preference.','']
    (dest/'RESULTS.md').write_text('\n'.join(lines))
    for name in ('manifest.json','completion.json','summary.json.gz','starts.jsonl'):
        shutil.copyfile(source/name,dest/name)
    shutil.copytree(source/'source-freeze',dest/'source-freeze',dirs_exist_ok=True)
    receipt=dict(state='complete',audit=counts,scientific_shape_decision='abstain',scientific_rotation_decision='abstain',
        artifacts={name:il.sha256(dest/name) for name in ('manifest.json','completion.json','summary.json.gz',
            'starts.jsonl','fits.csv','shape.csv','rotation.csv','RESULTS.md','package_results.py')})
    follow.atomic_json(dest/'evidence-receipt.json',receipt)
    # Load current metadata at publication time to preserve the other worker's updates.
    readiness=root/'docs/research-next-stage-20261006/readiness.json';metadata=load(readiness)
    stage=metadata['ilvis0_physical_pipeline']['conditional_recorded_modeling']
    stage['shape_first_refinement'].update(state='complete',completion=complete,
        report='docs/ilvis0-refinement-20261008/RESULTS.md',additional_observed_starts=counts['charged_starts'],audit=counts)
    corpus=stage.get('corpus_completion')
    if corpus is not None:
        metadata['ilvis0_physical_pipeline']['earth_model_fit_attempts']=24+corpus['starts']+counts['charged_starts']
    for name,digest in receipt['artifacts'].items():
        metadata['artifact_sha256'][str((dest/name).relative_to(root))]=digest
    follow.atomic_json(readiness,metadata)
    follow.atomic_json(source/'package-status.json',dict(state='complete',evidence_receipt_sha256=il.sha256(dest/'evidence-receipt.json')))
    print(json.dumps(dict(state='complete',**counts)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--watch',action='store_true');parser.add_argument('--detach',action='store_true')
    args=parser.parse_args();root=Path(__file__).resolve().parents[2]
    source=root/'data/ilvis0-shape-refinement-20261008'
    if args.detach:
        with (root/'data/ilvis0-shape-package-20261008.log').open('ab',buffering=0) as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--watch'],cwd=root,
                stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True)
        print(json.dumps(dict(pid=child.pid)))
    else:
        with (source/'package.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);deadline=time.monotonic()+24*3600
            while args.watch and not (source/'completion.json').exists():
                status=load(source/'status.json');os.kill(status['pid'],0)
                if time.monotonic()>deadline:raise RuntimeError('24-hour packaging wait expired; worker untouched')
                time.sleep(30)
            package(root)
