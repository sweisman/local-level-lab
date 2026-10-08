# SPDX-License-Identifier: AGPL-3.0-or-later
"""Conditional analysis of 232 documented keepers; interrupted starts remain charged."""
import argparse
import csv
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np
from lll import applanix as ap, ilvis0 as il, ilvis0_followup as follow
from lll import ilvis0_installation as installation, ilvis0_forward as forward
from lll import ilvis0_estimator as estimator, ilvis0_exploratory as explore
from lll import ilvis0_corpus_modeling as modeling, ilvis0_gps_sensitivity as sensitivity
from lll import ilvis0_observation as observation, runtime

MAX_STARTS=764  # 696 primary starts, at most 68 interruption retries; never reset.


def load(path):return json.loads(Path(path).read_text())


def result_hash(result):
    return hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def save(path,result,manifest_hash):
    follow.atomic_json(path,dict(manifest_sha256=manifest_hash,result=result,result_sha256=result_hash(result)))


def cached(path,manifest_hash):
    if not path.exists():return None
    record=load(path)
    if record['manifest_sha256']!=manifest_hash or record['result_sha256']!=result_hash(record['result']):
        raise ValueError('cached corpus result hash mismatch')
    return record['result']


def charge(path,identity,manifest_hash,tasks,prior_records=()):
    with path.open('a+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX);stream.seek(0);records=[json.loads(line) for line in stream]
        if any(r['start']!=i+1 or r['manifest_sha256']!=manifest_hash or r['identity'] not in tasks
               or r['maximum_evaluations']!=200 for i,r in enumerate(records)):
            raise ValueError('corrupt/incompatible corpus start ledger')
        all_records=records+list(prior_records)
        if identity not in tasks or len(all_records)>=MAX_STARTS or sum(r['identity']==identity for r in all_records)>=2:
            raise ValueError('finite corpus attempt allowance exhausted')
        record=dict(start=len(records)+1,identity=identity,manifest_sha256=manifest_hash,maximum_evaluations=200)
        stream.write(json.dumps(record,sort_keys=True)+'\n');stream.flush();os.fsync(stream.fileno())
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return record


def recorded_diagnostics(problem,conservative,header,point,model,metric):
    prediction=problem.predict(point,model)
    delta=prediction-problem.gps;delta[:,1]=(delta[:,1]+math.pi)%(2*math.pi)-math.pi
    d=delta/metric;z=conservative.whiten(prediction-problem.gps)
    result=dict(residual_rms_neu_m=np.sqrt(np.mean(d*d,axis=0)).tolist(),
        residual_max_abs_neu_m=np.max(abs(d),axis=0).tolist(),
        conservative_fixed_parameter_cost=float(z@z),diagnostic_predictions=1)
    if header is not None:
        h=header.predict(point,model)-problem.gps
        h[:,1]=(h[:,1]+math.pi)%(2*math.pi)-math.pi;h=h/metric
        result.update(header_fixed_parameter_rms_neu_m=np.sqrt(np.mean(h*h,axis=0)).tolist(),diagnostic_predictions=2)
    return result


def run(root,output,prior_attempts=None):
    if output.exists() and not (output/'manifest.json').exists():raise ValueError('unmarked corpus output')
    output.mkdir(parents=True,exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists():raise ValueError('completed corpus study is frozen')
        evidence=root/'docs/ilvis0-exploratory-20261008'
        receipt=load(evidence/'evidence-receipt.json')
        if receipt['state']!='complete' or receipt['files']!=6:raise ValueError('completed six-file evidence required')
        for name,digest in receipt['artifacts'].items():
            if il.sha256(evidence/name)!=digest:raise ValueError('six-file evidence changed')
        with (evidence/'corpus-inventory.csv').open(newline='') as stream:inventory=list(csv.DictReader(stream))
        if len(inventory)!=232 or len({r['task'] for r in inventory})!=232:raise ValueError('expected 232 distinct kept tasks')
        contexts_path=root/'data/ilvis0-followup-20261007/summary.json'
        contexts={r['task_id']:r for r in load(contexts_path)['results']}
        # Six representatives first; remaining tasks follow catalog/date order.
        inventory.sort(key=lambda r:(r['six_file_fit_completed']!='True',r['embedded_dates'],r['filename']))
        sources=[Path(m.__file__) for m in (ap,il,follow,installation,forward,estimator,explore,modeling,sensitivity,observation,runtime)]
        sources += [Path(explore.__file__).with_name('ilvis0_native.c'),Path(__file__),root/'analysis/tests/test_ilvis0_corpus_modeling.py',root/'analysis/lll/models.py']
        tasks=[r['task']+'::'+m for r in inventory for m in explore.MODELS]
        inputs=[evidence/'evidence-receipt.json',evidence/'manifest.json',evidence/'comparison.csv',
                evidence/'corpus-inventory.csv',contexts_path]
        prior_records=[]
        if prior_attempts is not None:
            prior_manifest=load(prior_attempts/'manifest.json');prior_digest=il.sha256(prior_attempts/'manifest.json')
            prior_records=[json.loads(line) for line in (prior_attempts/'starts.jsonl').read_text().splitlines()]
            if any(r['start']!=i+1 or r['manifest_sha256']!=prior_digest or r['identity'] not in tasks
                   or r['maximum_evaluations']!=200 for i,r in enumerate(prior_records)):
                raise ValueError('invalid carried-forward attempt journal')
            inputs += [prior_attempts/'manifest.json',prior_attempts/'starts.jsonl',prior_attempts/'interruption.json']
        kernel,build=explore.load_kernel(output/'kernel')
        manifest=dict(version=modeling.VERSION,authorization='Proceed with six, then whole kept set; conditional assumptions documented',
            sources={str(p):il.sha256(p) for p in sources},inputs={str(p):il.sha256(p) for p in inputs},
            environment=runtime.numerical_environment(),build=build,inventory=inventory,tasks=tasks,
            maximum_files=232,primary_starts=696,maximum_starts=MAX_STARTS,maximum_starts_per_identity=2,
            runner_revision=2,carried_forward_starts=prior_records,maximum_new_starts=MAX_STARTS-len(prior_records),
            maximum_evaluations_per_start=200,maximum_window_seconds=600,
            selection='longest complete native/GPS-supported run <=600s, earliest tie; dynamical motion not level-flight promotion',
            scales={str(k):list(v) for k,v in modeling.SCALES.items()},limits=explore.LIMITS,
            processing='common conventional Earth-rate removal fraction in [0,1], no modeled onboard transport subtraction',
            covariance_assumptions=['h1_v3_tau60','h10_v30_tau300'],clock='nominal200Hz fit; header fixed-parameter sensitivity',
            gravity_mps2=9.81,disc_radius_m=6371000.,scientific_eligible=False,
            original_deletion_allowed=False,synthetic_campaigns_allowed=False)
        path=output/'manifest.json'
        if path.exists():
            if load(path)!=manifest:raise ValueError('source/input/environment freeze changed')
        else:
            follow.atomic_json(path,manifest);(output/'source-freeze').mkdir()
            for p in sources:shutil.copyfile(p,output/'source-freeze'/p.name)
        digest=il.sha256(path)
        def verify():
            for name,expected in {**manifest['sources'],**manifest['inputs']}.items():
                if il.sha256(name)!=expected:raise ValueError('frozen corpus source/input changed')
            if runtime.numerical_environment()!=manifest['environment']:raise ValueError('numerical environment changed')
        grid={a.name:a for a in sensitivity.assumptions()};results=[]
        for entry in inventory:
            verify();task=entry['task'];destination=output/(task+'.json');record=cached(destination,digest)
            if record is not None:results.append(record);continue
            follow.atomic_json(output/'status.json',dict(state='preparing',task=task,completed=len(results),total=232,pid=os.getpid()))
            context=contexts.get(task)
            try:
                if context is None or context['inspection']['source_sha256']!=entry['source_sha256']:
                    raise ValueError('source/configuration metadata unavailable or mismatched')
                values,times,gps,provenance=modeling.extract(Path(entry['source_path']),context)
            except (ValueError,KeyError) as error:
                record=dict(task=task,filename=entry['filename'],state='unsupported',reason=str(error),
                            scientific_decision='abstain',original_preserved=True)
                save(destination,record,digest);results.append(record);continue
            blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            covs={name:sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[name])
                  for name in manifest['covariance_assumptions']}
            metric=np.column_stack((1/(6378137.+gps[:,2]),1/((6378137.+gps[:,2])*np.cos(gps[:,0])),np.ones(len(gps))))
            fits=[]
            for model in explore.MODELS:
                identity=task+'::'+model;target=output/(task+'-'+model+'.json');fit=cached(target,digest)
                if fit is not None:fits.append(fit);continue
                seed,force=modeling.initialize(times,gps,values,model)
                kwargs=dict(clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                    maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,kernel=kernel)
                problem=explore.ConditionalProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,
                    covs['h1_v3_tau60'],seed,estimator.Bounds(explore.LIMITS),**kwargs)
                start=np.zeros(len(problem.bounds.active))
                for i,name in enumerate(problem.bounds.active):
                    if name.startswith('accel_gain'):start[i]=np.clip((force/9.81-1)/explore.LIMITS[name],-.9,.9)
                    if name=='earth_removal':start[i]=-1.
                follow.atomic_json(output/'status.json',dict(state='fitting',task=task,model=model,completed=len(results),total=232,pid=os.getpid()))
                charged=charge(output/'starts.jsonl',identity,digest,tasks,prior_records);begin=time.monotonic()
                try:
                    fit=modeling.bounded_fit(problem,model,maximum_evaluations=200,start=start)
                    point=np.array(fit['normalized_parameters'])
                    conservative=explore.ConditionalProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,
                        covs['h10_v30_tau300'],seed,estimator.Bounds(explore.LIMITS),**kwargs)
                    try:
                        header=explore.ConditionalProblem(values[:,9:12],values[:,12:15],values[:,2],times,gps,
                            covs['h1_v3_tau60'],seed,estimator.Bounds(explore.LIMITS),**dict(kwargs,clock_hypothesis='header_elapsed'))
                    except ValueError as error:
                        header=None;fit['header_sensitivity_error']=str(error)
                    fit.update(recorded_diagnostics(problem,conservative,header,point,model,metric))
                    fit['evaluations']+=fit['diagnostic_predictions']
                    if fit['evaluations']>200:raise ValueError('evaluation allowance exceeded')
                except (ValueError,FloatingPointError) as error:
                    fit=dict(model=model,error=str(error),scientific_eligible=False,scientific_decision='abstain')
                fit.update(start_charge=charged,elapsed_s=time.monotonic()-begin)
                verify();save(target,fit,digest);fits.append(fit)
            record=dict(task=task,filename=entry['filename'],state='fitted',provenance=provenance,fits=fits,
                        scientific_decision='abstain',original_preserved=True)
            verify();save(destination,record,digest);results.append(record)
            follow.atomic_json(output/'status.json',dict(state='running',completed=len(results),total=232,pid=os.getpid(),
                fitted_files=sum(r['state']=='fitted' for r in results),converged_fits=sum(bool(f.get('converged')) for r in results for f in r.get('fits',[]))))
            print(json.dumps(dict(completed=len(results),filename=entry['filename'],rms=[f.get('residual_rms_neu_m') for f in fits],
                                 converged=[f.get('converged') for f in fits])),flush=True)
        summary=dict(version=modeling.VERSION,state='complete',files=len(results),results=results,
            fitted_files=sum(r['state']=='fitted' for r in results),unsupported_files=sum(r['state']=='unsupported' for r in results),
            converged_fits=sum(bool(f.get('converged')) for r in results for f in r.get('fits',[])),
            failed_fits=sum('error' in f for r in results for f in r.get('fits',[])),
            starts=(sum(1 for _ in (output/'starts.jsonl').open()) if (output/'starts.jsonl').exists() else 0)+len(prior_records),
            carried_forward_starts=len(prior_records),
            scientific_decision='abstain',scientific_eligibility_changes=0,originals_deleted=0)
        verify();observation.gzip_json(output/'summary.json.gz',summary)
        compact={k:v for k,v in summary.items() if k!='results'}
        compact.update(manifest_sha256=digest,summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json',compact);follow.atomic_json(output/'status.json',compact)
        print(json.dumps(compact),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-corpus-modeling-v2-20261008'))
    parser.add_argument('--detach',action='store_true')
    parser.add_argument('--prior-attempts',type=Path,default=Path('data/ilvis0-corpus-modeling-20261008'))
    args=parser.parse_args();root=Path(__file__).resolve().parents[2];output=args.output.resolve()
    if args.detach:
        output.parent.mkdir(parents=True,exist_ok=True)
        # Child takes the flock; parent never changes the frozen study output.
        with (output.parent/(output.name+'.log')).open('ab',buffering=0) as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--output',str(output),
                '--prior-attempts',str(args.prior_attempts.resolve())],
                stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True,close_fds=True,cwd=root)
        print(json.dumps(dict(pid=child.pid,log=str(output.parent/(output.name+'.log')))))
    else:run(root,output,args.prior_attempts.resolve())
