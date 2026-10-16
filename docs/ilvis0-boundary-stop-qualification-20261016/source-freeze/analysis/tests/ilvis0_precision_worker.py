# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite fixed-endpoint precision comparison; no optimizer starts."""
import fcntl
import json
from pathlib import Path
import shutil
import time

import numpy as np

import ilvis0_shared_leg_probes as prior
from lll import ilvis0_precision as arithmetic, ilvis0_precision_probes as probes

base=prior.base
ROOT=prior.ROOT
OUTPUT=ROOT/'data/ilvis0-shared-leg-precision-20261014'
GUIDE=ROOT/'docs/ilvis0-shared-leg-precision-20261014'
VERSION='ilvis0-fixed-precision-worker-v1'


def prepare():
    if (OUTPUT/'manifest.json').exists():
        return verify()
    complete=base.load(prior.OUTPUT/'completion.json')
    if (complete['state']!='complete' or complete['manifest_sha256']!=prior.sha(prior.OUTPUT/'manifest.json')
            or complete['summary_sha256']!=prior.sha(prior.OUTPUT/'summary.json')):
        raise ValueError('sealed six-endpoint dependency required')
    original=base.load(prior.OUTPUT/'manifest.json')
    previous=base.load(prior.OUTPUT/'summary.json')
    if len(previous['results'])!=6 or any(r['status']!='complete' for r in previous['results']):
        raise ValueError('all predetermined endpoint checks required')
    prior.checks(original['sources']);prior.checks(original['inputs']);prior.checks(original['originals'])
    controls=base.load(GUIDE/'control-receipt.json')
    prior.checks(controls['sources'])
    if controls['passed']!=11 or controls['observed_fit_starts']!=0:
        raise ValueError('precision control qualification required')
    sources=dict(original['sources'])
    for path in (Path(__file__),Path(arithmetic.__file__),Path(probes.__file__),
                 ROOT/'analysis/tests/test_ilvis0_precision.py',ROOT/'analysis/tests/test_ilvis0_precision_probes.py'):
        sources[str(path.resolve())]=prior.sha(path)
    inputs=dict(original['inputs'])
    for path in (prior.OUTPUT/'completion.json',prior.OUTPUT/'manifest.json',prior.OUTPUT/'summary.json',
                 GUIDE/'PLAN.md',GUIDE/'control-receipt.json'):
        inputs[str(path)]=prior.sha(path)
    _,kernel_meta=arithmetic.load_tangent(OUTPUT/'kernel')
    (OUTPUT/'source-freeze').mkdir(exist_ok=True)
    for name in sources:
        shutil.copyfile(name,OUTPUT/'source-freeze'/Path(name).name)
    shutil.copyfile(OUTPUT/'kernel'/kernel_meta['source_file'],OUTPUT/'source-freeze'/kernel_meta['source_file'])
    endpoints={r['identity']:r for r in previous['results']}
    tasks=[dict(t,frozen_correction=endpoints[t['identity']]['normalized_correction']) for t in original['tasks']]
    value=dict(version=VERSION,tasks=tasks,inputs=inputs,sources=sources,originals=original['originals'],
               environment=base.runtime.numerical_environment(),numerical_threads=4,
               maximum_native_evaluations=84,maximum_evaluations_per_identity=14,
               observed_fit_starts=0,retries=0,extended_kernel=kernel_meta,
               ordinary_kernel=original['tangent_kernel'],value_kernel=original['value_kernel'])
    base.follow.atomic_json(OUTPUT/'manifest.json',value)
    return value


def verify():
    manifest=base.load(OUTPUT/'manifest.json')
    if manifest['version']!=VERSION or manifest['maximum_native_evaluations']!=84:
        raise ValueError('unexpected precision freeze')
    for name in ('sources','inputs','originals'):
        prior.checks(manifest[name])
    base.runtime.check_environment(manifest['environment'])
    for name,digest in manifest['sources'].items():
        if prior.sha(OUTPUT/'source-freeze'/Path(name).name)!=digest:
            raise ValueError('precision source snapshot mismatch')
    meta=manifest['extended_kernel']
    if prior.sha(OUTPUT/'source-freeze'/meta['source_file'])!=meta['source_sha256']:
        raise ValueError('generated precision source snapshot mismatch')
    return manifest


def run():
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            raise ValueError('completed precision diagnostic cannot resume')
        manifest=prepare();digest=prior.sha(OUTPUT/'manifest.json')
        book=prior.journal.Ledger(OUTPUT,digest,[t['identity'] for t in manifest['tasks']],fit_limit=1,diagnostic_limit=14)
        kernel,kmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        ordinary,ometa=base.shape.load_tangent(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        extended,emeta=arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta!=manifest['value_kernel'] or ometa!=manifest['ordinary_kernel'] or emeta!=manifest['extended_kernel']:
            raise ValueError('precision kernel mismatch')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={c['case_id']:c for c in base.primary_cases()}
        assumptions={a.name:a for a in base.sensitivity.assumptions()}
        results=[]
        for task in manifest['tasks']:
            verify();identity=task['identity'];target=OUTPUT/(identity.replace('::','-')+'.json')
            saved=base.cached(target,digest)
            if saved is not None:
                results.append(saved);continue
            begin=time.monotonic()
            if identity in {r['identity'] for r in book.read('starts')}:
                result=dict(identity=identity,status='interrupted',retry=False)
            else:
                book.start(identity)
                base.follow.atomic_json(OUTPUT/'status.json',dict(state='precision_checks',identity=identity,completed=len(results),total=6))
                try:
                    chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:
                        raise ValueError('saved extraction provenance mismatch')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                    covariance=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumptions['h1_v3_tau60'])
                    initial,_=base.corpus.initialize(times,gps,values,task['model'])
                    problem=base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,initial,
                        base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=ordinary,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    if list(problem.bounds.active)!=task['reference']['active_parameters']:
                        raise ValueError('saved parameter order mismatch')
                    call=lambda fn,*args:book.call(identity,'diagnostic','tangent',fn,*args)
                    result=probes.inspect_endpoint(problem,np.asarray(task['reference']['normalized_parameters']),task['model'],
                        task['frozen_correction'],ordinary,extended,call)
                    relative=abs(result['ordinary_center_cost']-task['reference']['residual_sum_squares'])/max(task['reference']['residual_sum_squares'],1.)
                    if relative>1e-6:
                        raise ValueError('ordinary central objective did not reproduce')
                    result.update(identity=identity,status='complete',original_converged=task['reference']['converged'])
                except Exception as error:
                    result=dict(identity=identity,status='error',error=type(error).__name__+': '+str(error))
            result.update(native_evaluations=book.count(identity,'diagnostic'),observed_fit_starts=0,elapsed_s=time.monotonic()-begin)
            base.save(target,result,digest);results.append(result)
            print(json.dumps(dict(completed=len(results),identity=identity,status=result['status'],elapsed_s=result['elapsed_s'])),flush=True)
        sweeps=book.read('sweeps')
        if len(sweeps)>84 or any(r['phase']!='diagnostic' for r in sweeps):
            raise ValueError('finite precision accounting mismatch')
        summary=dict(version=VERSION,state='complete',results=results,native_evaluations=len(sweeps),
                     observed_fit_starts=0,scientific_decision='abstain',original_labels_changed=False)
        base.follow.atomic_json(OUTPUT/'summary.json',summary)
        base.follow.atomic_json(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=prior.sha(OUTPUT/'summary.json'),journal_hashes={n:prior.sha(OUTPUT/n) for n in ('starts.jsonl','sweeps.jsonl')}))
        base.follow.atomic_json(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(sweeps)))
        names=('manifest.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl')
        for name in names:
            shutil.copyfile(OUTPUT/name,GUIDE/name)
        shutil.copyfile(OUTPUT/'source-freeze'/emeta['source_file'],GUIDE/emeta['source_file'])
        base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(
            artifacts={n:prior.sha(GUIDE/n) for n in (*names,emeta['source_file'])},
            observed_fit_starts=0,native_evaluations=len(sweeps),scientific_decision='abstain'))


if __name__=='__main__':
    run()
