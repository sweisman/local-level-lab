# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite native endpoint diagnostics; no optimization or scientific promotion."""
import fcntl
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from scipy.optimize import lsq_linear

import ilvis0_segment_worker as base
from lll import ilvis0_sweep_journal as journal
from lll.ilvis0_solver_position import physical_metric
from lll.ilvis0_solver_refinement import projected_stationarity

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT/'data/ilvis0-shared-leg-probes-20261014'
GUIDE = ROOT/'docs/ilvis0-shared-leg-probes-20261014'
RECOVERY = ROOT/'docs/ilvis0-position-recovery-20261013'
BASELINE = ROOT/'docs/ilvis0-highspeed-segments-20261008'
AUDIT = ROOT/'docs/ilvis0-shared-leg-diagnosis-20261014'
VERSION = 'ilvis0-shared-leg-native-probes-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checks(hashes):
    for name, digest in hashes.items():
        if sha(Path(name)) != digest:
            raise ValueError('frozen source/input mismatch: '+name)


def prepare():
    manifest = OUTPUT/'manifest.json'
    if manifest.exists():
        return verify()
    receipt = base.load(AUDIT/'evidence-receipt.json')
    checks({str(AUDIT/name):digest for name,digest in receipt['artifacts'].items()})
    parent = base.load(RECOVERY/'manifest.json')
    checks(parent['sources'])
    prior = base.load(RECOVERY/'summary.json')
    old = {r['segment_id']:r for r in base.load(BASELINE/'summary.json.gz')['results']}
    recovered = {r['segment_id']:r for r in prior['comparisons']}
    selected = {r['segment']['segment_id']:r for r in base.load(BASELINE/'selection.json.gz')['selected']}
    diagnosis = base.load(AUDIT/'diagnosis.json')
    tasks = []
    for pair in diagnosis['pairs']:
        if pair['priority_pair'] != 'True':
            continue
        ids = (pair['left_segment_id'], pair['right_segment_id'])
        unfinished = [r for r in diagnosis['focus_fits']
                      if r['segment_id'] in ids and r['role']=='primary' and not r['converged']]
        if len(unfinished) != 1:
            raise ValueError('exactly one priority failure per pair required')
        target = unfinished[0]
        for sid in ids:
            record = recovered.get(sid, old[sid])
            fit = next(f for c in record['cases'] if c['case_id']==target['case_id']
                       for f in c['fits'] if f['model']==target['model'])
            task = dict(identity='::'.join((sid,target['case_id'],target['model'],'probe')),
                        segment_id=sid, case_id=target['case_id'], model=target['model'],
                        selected=selected[sid], reference=fit, provenance=old[sid]['provenance'])
            tasks.append(task)
    if len(tasks)!=6 or len({t['identity'] for t in tasks})!=6:
        raise ValueError('six immutable diagnostic identities required')
    inputs = {str(p):sha(p) for p in (RECOVERY/'manifest.json', RECOVERY/'summary.json',
              RECOVERY/'completion.json', BASELINE/'summary.json.gz', BASELINE/'selection.json.gz',
              AUDIT/'diagnosis.json', AUDIT/'evidence-receipt.json', GUIDE/'PLAN.md',
              ROOT/'data/ilvis0-followup-20261007/summary.json')}
    originals = {t['selected']['source_path']:sha(Path(t['selected']['source_path'])) for t in tasks}
    # Storage hashes fingerprint gzip containers; extraction separately verifies
    # the decoded original hash in the preserved measurement provenance.
    for name,digest in originals.items():
        if name in parent['originals'] and digest!=parent['originals'][name]:
            raise ValueError('retained compressed original hash mismatch')
    sources = dict(parent['sources'])
    for p in (Path(__file__),ROOT/'analysis/tests/test_ilvis0_shared_leg_probes.py'):
        sources[str(p.resolve())]=sha(p)
    (OUTPUT/'source-freeze').mkdir(exist_ok=True)
    for name in sources:
        shutil.copyfile(name,OUTPUT/'source-freeze'/Path(name).name)
    value = dict(version=VERSION, tasks=tasks, inputs=inputs, originals=originals, sources=sources,
                 environment=base.runtime.numerical_environment(), numerical_threads=4,
                 maximum_diagnostic_identities=6, maximum_evaluations_per_identity=10,
                 maximum_native_evaluations=60, observed_fit_starts=0,
                 execution_authority='approved shared-leg investigation', retries=0,
                 value_kernel=parent['value_kernel'], tangent_kernel=parent['tangent_kernel'])
    base.follow.atomic_json(manifest,value)
    return value


def verify():
    value=base.load(OUTPUT/'manifest.json')
    if value['version']!=VERSION or value['maximum_native_evaluations']!=60:
        raise ValueError('unexpected diagnostic scope')
    checks(value['sources']); checks(value['inputs']); checks(value['originals'])
    base.runtime.check_environment(value['environment'])
    return value


def physical_difference(one,two,gps):
    delta=np.asarray(one)-np.asarray(two)
    delta[:,1]=(delta[:,1]+np.pi)%(2*np.pi)-np.pi
    return delta*physical_metric(gps)


def probe_endpoint(problem,point,model,call):
    """Exactly ten native calls: four center checks and six fixed probes."""
    center,jac,boundaries=call('tangent',problem.prediction_tangent,point,model)
    repeated,_,_=call('tangent',problem.prediction_tangent,point,model)
    value=call('value',problem.predict,point,model)
    value_repeat=call('value',problem.predict,point,model)
    residual=problem.whiten(center-problem.gps)
    from scipy.linalg import solve_triangular
    whitened_jac=solve_triangular(problem.cholesky,jac,lower=True)
    local=lsq_linear(whitened_jac,-residual,bounds=(-1-point,1-point),method='bvls',tol=1e-10,max_iter=100)
    if not local.success or not np.all(np.isfinite(local.x)):
        raise ValueError('bounded affine correction unfinished')
    def cost(coordinates):
        r=problem.whiten(coordinates-problem.gps)
        return float(r@r)
    def stats(difference):
        return dict(rms_neu_m=np.sqrt(np.mean(difference**2,axis=0)).tolist(),
                    maximum_neu_m=np.max(abs(difference),axis=0).tolist())
    central_cost=cost(center); central_value_cost=cost(value)
    result=dict(center_tangent_cost=central_cost,center_value_cost=central_value_cost,
                center_value_tangent_cost_relative_difference=abs(central_cost-central_value_cost)/max(central_cost,central_value_cost,1.),
                tangent_repeat=stats(physical_difference(repeated,center,problem.gps)),
                value_repeat=stats(physical_difference(value_repeat,value,problem.gps)),
                value_tangent_difference=stats(physical_difference(value,center,problem.gps)),
                endpoint_stationarity=projected_stationarity(point,residual,whitened_jac)[0],
                boundary_epochs=boundaries,normalized_correction=local.x.tolist(),probes=[])
    for fraction in (1.,.5,.25):
        proposed=np.clip(point+fraction*local.x,-1,1)
        prediction,new_jac,_=call('tangent',problem.prediction_tangent,proposed,model)
        plain=call('value',problem.predict,proposed,model)
        error=problem.whiten(prediction-problem.gps)
        fresh_jac=solve_triangular(problem.cholesky,new_jac,lower=True)
        predicted=residual+whitened_jac@(proposed-point)
        tangent_cost=cost(prediction); value_cost=cost(plain)
        result['probes'].append(dict(fraction=fraction,tangent_cost=tangent_cost,value_cost=value_cost,
            tangent_cost_relative_change=abs(tangent_cost-central_cost)/max(tangent_cost,central_cost,1.),
            value_cost_relative_change=abs(value_cost-central_value_cost)/max(value_cost,central_value_cost,1.),
            affine_predicted_cost=float(predicted@predicted),
            fresh_stationarity=projected_stationarity(proposed,error,fresh_jac)[0],
            tangent_position_change=stats(physical_difference(prediction,center,problem.gps)),
            value_position_change=stats(physical_difference(plain,value,problem.gps)),
            value_tangent_difference=stats(physical_difference(plain,prediction,problem.gps))))
    return result


def run():
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            raise ValueError('completed diagnostic cannot resume')
        manifest=prepare(); digest=sha(OUTPUT/'manifest.json')
        book=journal.Ledger(OUTPUT,digest,[t['identity'] for t in manifest['tasks']],fit_limit=1,diagnostic_limit=10)
        kernel,build=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent,tbuild=base.shape.load_tangent(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        if build!=manifest['value_kernel'] or tbuild!=manifest['tangent_kernel']:
            raise ValueError('native implementation differs from saved recovery')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases={c['case_id']:c for c in base.primary_cases()}
        assumptions={a.name:a for a in base.sensitivity.assumptions()}
        results=[]
        for task in manifest['tasks']:
            verify()
            identity=task['identity'];target=OUTPUT/(identity.replace('::','-')+'.json')
            saved=base.cached(target,digest)
            if saved is not None:
                results.append(saved); continue
            if identity in {r['identity'] for r in book.read('starts')}:
                result=dict(identity=identity,status='interrupted',retry=False)
            else:
                book.start(identity)
                try:
                    chosen=task['selected'];case=cases[task['case_id']]
                    values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                    if provenance!=task['provenance']:
                        raise ValueError('saved extraction provenance mismatch')
                    blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                    covariance=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumptions['h1_v3_tau60'])
                    initial,_=base.corpus.initialize(times,gps,values,task['model'])
                    problem=base.shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,initial,
                        base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    if list(problem.bounds.active)!=task['reference']['active_parameters']:
                        raise ValueError('saved parameter order mismatch')
                    call=lambda kind,function,*args:book.call(identity,'diagnostic',kind,function,*args)
                    result=probe_endpoint(problem,np.asarray(task['reference']['normalized_parameters']),task['model'],call)
                    result.update(identity=identity,status='complete',reference_cost=task['reference']['residual_sum_squares'])
                    difference=abs(result['center_tangent_cost']-result['reference_cost'])/max(result['reference_cost'],1.)
                    if difference>1e-6:
                        raise ValueError('saved central objective failed reproduction')
                except Exception as error:
                    result=dict(identity=identity,status='error',error=type(error).__name__+': '+str(error))
            result.update(native_evaluations=book.count(identity,'diagnostic'),observed_fit_starts=0)
            base.save(target,result,digest);results.append(result)
            base.follow.atomic_json(OUTPUT/'status.json',dict(state='diagnostic',completed=len(results),total=6,identity=identity))
            print(json.dumps(dict(completed=len(results),identity=identity,status=result['status'])),flush=True)
        sweeps=book.read('sweeps')
        if any(r['phase']!='diagnostic' for r in sweeps) or len(sweeps)>60:
            raise ValueError('diagnostic accounting mismatch')
        summary=dict(version=VERSION,state='complete',results=results,native_evaluations=len(sweeps),
                     observed_fit_starts=0,scientific_decision='abstain',original_labels_changed=False)
        base.follow.atomic_json(OUTPUT/'summary.json',summary)
        base.follow.atomic_json(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=sha(OUTPUT/'summary.json'),journal_hashes={n:sha(OUTPUT/n) for n in ('starts.jsonl','sweeps.jsonl')}))
        base.follow.atomic_json(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(sweeps)))
        for name in ('manifest.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl'):
            shutil.copyfile(OUTPUT/name,GUIDE/name)
        receipt=dict(artifacts={n:sha(GUIDE/n) for n in ('manifest.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl')},
                     observed_fit_starts=0,native_evaluations=len(sweeps),scientific_decision='abstain')
        base.follow.atomic_json(GUIDE/'evidence-receipt.json',receipt)


if __name__=='__main__':
    run()
