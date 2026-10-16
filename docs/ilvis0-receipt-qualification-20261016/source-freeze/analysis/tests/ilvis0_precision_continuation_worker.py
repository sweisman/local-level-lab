# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded cost-only recovery; qualified arithmetic and original scientific gates preserved."""
import argparse
import copy
import fcntl
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import numpy as np

import ilvis0_shared_leg_probes as prior
from lll import ilvis0_precision_continuation_plan as planning, ilvis0_precision as arithmetic
from lll import ilvis0_solver_position as solver, ilvis0_boundary_diagnosis as track_audit

base=prior.base;ROOT=prior.ROOT
PARENT=ROOT/'docs/ilvis0-cost-precision-recovery-20261014'
PREPARATION=ROOT/'docs/ilvis0-budget-continuation-20261014/prepare_continuation.py'
VERSION='ilvis0-precision-continuation-worker-v1'
STAGE='budget'
OUTPUT=ROOT/'data'/planning.STAGES[STAGE][0]
GUIDE=ROOT/'docs'/planning.STAGES[STAGE][0]


def configure(stage):
    global STAGE,OUTPUT,GUIDE
    STAGE=stage;OUTPUT=ROOT/'data'/planning.STAGES[stage][0];GUIDE=ROOT/'docs'/planning.STAGES[stage][0]


def atomic_bytes(path,data):
    temporary=path.with_suffix(path.suffix+'.tmp')
    with temporary.open('wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    temporary.replace(path)


def retained_hashes(*inventories):
    known={}
    for inventory in inventories:
        for name,digest in inventory.items():
            if name in known and known[name]!=digest:
                raise ValueError('conflicting retained original hashes')
            known[name]=digest
    return known


def prepare():
    if (OUTPUT/'manifest.json').exists(): return verify()
    parent=base.load(PARENT/'manifest.json');summary=base.load(PARENT/'summary.json')
    complete=base.load(PARENT/'completion.json');receipt=base.load(PARENT/'evidence-receipt.json')
    prior.checks({str(PARENT/n):h for n,h in receipt['artifacts'].items()})
    if (complete['state']!='complete' or complete['manifest_sha256']!=prior.sha(PARENT/'manifest.json')
            or complete['summary_sha256']!=prior.sha(PARENT/'summary.json') or not summary['qualification']['controls_passed']):
        raise ValueError('completed parent and passing controls required')
    prior.checks(parent['sources']);prior.checks(parent['inputs'])
    reference=base.load(prior.RECOVERY/'summary.json')
    records={r['segment_id']:r for r in reference['comparisons']}
    original={r['segment_id']:r for r in base.load(prior.BASELINE/'summary.json.gz')['results']}
    selected={r['segment']['segment_id']:r for r in base.load(prior.BASELINE/'selection.json.gz')['selected']}
    parent_records={r['segment_id']:r for r in summary['comparisons']}
    parent_tasks={t['identity']:t for t in parent['plan']['tasks']}
    plan=planning.build(STAGE,summary,parent)
    _,starts,sweeps=planning.STAGES[STAGE]
    if plan['maximum_starts']!=starts or plan['maximum_native_sweeps']!=sweeps:
        raise ValueError('frozen continuation scope changed')
    if base.load(GUIDE/'selection.json')!=plan: raise ValueError('published selection mismatch')
    for task in plan['tasks']:
        sid=task['segment_id']
        if task['role']=='control': task['reference']=summary['results'][task['identity']]
        else:
            record=parent_records[sid] if STAGE=='budget' else records.get(sid,original[sid])
            task['reference']=next(f for c in record['cases'] if c['case_id']==task['case_id'] for f in c['fits'] if f['model']==task['model'])
        task['selected']=selected[sid];task['provenance']=original[sid]['provenance']
    _,meta=arithmetic.load_tangent(OUTPUT/'kernel')
    if meta!=parent['extended_kernel']: raise ValueError('qualified arithmetic changed')
    sources=dict(parent['sources'])
    for path in (Path(__file__),Path(planning.__file__),PREPARATION,
                 ROOT/'analysis/tests/test_ilvis0_precision_continuation_plan.py',ROOT/'analysis/tests/test_ilvis0_precision_continuation_worker.py'):
        sources[str(path.resolve())]=prior.sha(path)
    inputs=dict(parent['inputs'])
    for name in ('manifest.json','summary.json','completion.json','evidence-receipt.json','starts.jsonl','sweeps.jsonl'):
        inputs[str(PARENT/name)]=prior.sha(PARENT/name)
    for name in ('PLAN.md','selection.json','preparation-receipt.json','test-receipt.json'):
        inputs[str(GUIDE/name)]=prior.sha(GUIDE/name)
    reused={};reused_artifacts={}
    if STAGE=='budget':
        replacing={(t['segment_id'],t['case_id'],t['model']) for t in plan['tasks'] if t['role']=='primary'}
        for sid in plan['target_segment_ids']:
            for case in parent_records[sid]['cases']:
                for fit in case['fits']:
                    if (sid,case['case_id'],fit['model']) in replacing: continue
                    if not fit['converged']: raise ValueError('only passing parent primaries may be reused')
                    reused['::'.join((sid,case['case_id'],fit['model'],'primary'))]=fit
                    for nk,hk in (('epoch_file','epoch_sha256'),('linearization_file','linearization_sha256')):
                        name=fit[nk]
                        if Path(name).name!=name or prior.sha(PARENT/name)!=fit[hk]: raise ValueError('reused artifact mismatch')
                        inputs[str(PARENT/name)]=fit[hk];reused_artifacts[name]=fit[hk]
                        shutil.copyfile(PARENT/name,OUTPUT/name)
    else:
        budget=ROOT/'data'/planning.STAGES['budget'][0]/'manifest.json'
        inputs[str(budget)]=prior.sha(budget)
    originals={t['selected']['source_path']:prior.sha(Path(t['selected']['source_path'])) for t in plan['tasks']}
    known=retained_hashes(base.load(prior.RECOVERY/'manifest.json')['originals'],parent['originals'])
    for name,h in originals.items():
        if name not in known or known[name]!=h: raise ValueError('retained original mismatch')
    (OUTPUT/'source-freeze').mkdir(exist_ok=True)
    if len({Path(n).name for n in sources})!=len(sources): raise ValueError('source filename collision')
    for name in sources: shutil.copyfile(name,OUTPUT/'source-freeze'/Path(name).name)
    shutil.copyfile(OUTPUT/'kernel'/meta['source_file'],OUTPUT/'source-freeze'/meta['source_file'])
    value=dict(version=VERSION,stage=STAGE,plan=plan,sources=sources,inputs=inputs,originals=originals,
               reused_results=reused,reused_artifacts=reused_artifacts,
               extended_kernel=meta,ordinary_value_kernel=parent['ordinary_value_kernel'],
               environment=base.runtime.numerical_environment(),numerical_threads=4,cases=parent['cases'],
               scientific_decision='abstain',production_promotion=False)
    base.follow.atomic_json(OUTPUT/'manifest.json',value)
    return value


def verify():
    value=base.load(OUTPUT/'manifest.json');_,starts,sweeps=planning.STAGES[STAGE]
    if value['version']!=VERSION or value['stage']!=STAGE or value['plan']['maximum_starts']!=starts or value['plan']['maximum_native_sweeps']!=sweeps:
        raise ValueError('unexpected continuation freeze')
    for section in ('sources','inputs','originals'): prior.checks(value[section])
    base.runtime.check_environment(value['environment'])
    for name,h in value['sources'].items():
        if prior.sha(OUTPUT/'source-freeze'/Path(name).name)!=h: raise ValueError('source snapshot mismatch')
    for name,h in value['reused_artifacts'].items():
        if prior.sha(OUTPUT/name)!=h: raise ValueError('reused artifact mismatch')
    return value


def matched_cases(plan,results,reused):
    merged=dict(reused);merged.update(results)
    return {sid:[dict(case_id=c,fits=[merged['::'.join((sid,c,m,'primary'))] for m in planning.MODELS]) for c in planning.CASES]
            for sid in plan['target_segment_ids']}


class ChargedProblem(base.shape.TangentProblem):
    def __init__(self,*args,book,identity,maximum_evaluations,**kwargs):
        super().__init__(*args,**kwargs);self.book=book;self.identity=identity;self.phase='fit'
        self.maximum_evaluations=maximum_evaluations

    def residual_tangent(self,point,model):
        if self.phase=='fit' and self.book.count(self.identity,'fit')>=self.maximum_evaluations:
            raise base.estimator.EvaluationLimit('per-identity fit allowance exhausted')
        return self.book.call(self.identity,self.phase,'tangent',super().residual_tangent,point,model)

    def predict(self,point,model):
        # Diagnostics use the same extended arithmetic as the fitted objective.
        return self.book.call(self.identity,self.phase,'tangent',super().prediction_tangent,point,model)[0]


def qualify(plan,results):
    controls=[];repeats=[]
    for task in plan['tasks']:
        fit=results[task['identity']]
        if task['role']=='control':
            cost=fit.get('residual_sum_squares');reference=task['reference']['residual_sum_squares']
            difference=abs(cost-reference)/max(cost,reference,1.) if cost is not None else None
            passed=bool(fit['converged'] and difference is not None and difference<=plan['control_cost_relative_tolerance']
                        and max(fit.get('reference_track_change_rms_neu_m',[float('inf')]))<=plan['control_track_rms_tolerance_m'])
            controls.append(dict(identity=task['identity'],passed=passed,relative_cost_difference=difference))
        elif task['role']=='repeat':
            primary=results[task['identity'].rsplit('::',1)[0]+'::primary']
            if 'epoch_file' in fit and 'epoch_file' in primary:
                repeat=track_audit.compare_saved_predictions(OUTPUT,primary,fit)
                passed=repeat['qualified_repeatability']
                repeats.append(dict(identity=task['identity'],passed=passed,**repeat))
            else:
                repeats.append(dict(identity=task['identity'],passed=False))
    return dict(controls_passed=all(r['passed'] for r in controls),controls=controls,repeatability=repeats,
                qualified=all(f['converged'] for f in results.values()) and all(r['passed'] for r in controls+repeats),
                global_optima_proven=False,scientific_decision='abstain')


def publish():
    manifest=verify();complete=base.load(OUTPUT/'completion.json')
    if complete['summary_sha256']!=prior.sha(OUTPUT/'summary.json') or complete['manifest_sha256']!=prior.sha(OUTPUT/'manifest.json'):
        raise ValueError('paired completion hash mismatch')
    summary=base.load(OUTPUT/'summary.json')
    for name,digest in complete['journal_hashes'].items():
        if prior.sha(OUTPUT/name)!=digest:
            raise ValueError('paired journal hash mismatch')
    book=prior.journal.Ledger(OUTPUT,complete['manifest_sha256'],
        [t['identity'] for t in manifest['plan']['tasks']],fit_limit=200,diagnostic_limit=2)
    if len(book.read('starts'))!=manifest['plan']['maximum_starts'] or len(book.read('sweeps'))!=summary['native_sweeps']:
        raise ValueError('paired publication accounting mismatch')
    for task in manifest['plan']['tasks']:
        fit=summary['results'][task['identity']]
        if (fit['fit_native_sweeps']!=book.count(task['identity'],'fit')
                or fit['diagnostic_native_sweeps']!=book.count(task['identity'],'diagnostic')
                or fit['fit_native_sweeps']>task['maximum_evaluations']):
            raise ValueError('paired per-identity accounting mismatch')
    names=['manifest.json','summary.json','completion.json','starts.jsonl','sweeps.jsonl']
    for fit in summary['results'].values():
        for name_key,hash_key in (('epoch_file','epoch_sha256'),('linearization_file','linearization_sha256')):
            if name_key in fit:
                name=fit[name_key]
                if Path(name).name!=name or prior.sha(OUTPUT/name)!=fit[hash_key]:
                    raise ValueError('paired fit artifact mismatch')
                names.append(name)
    names.extend(manifest['reused_artifacts'])
    for name in names:
        shutil.copyfile(OUTPUT/name,GUIDE/name)
    shutil.copytree(OUTPUT/'source-freeze',GUIDE/'source-freeze',dirs_exist_ok=True)
    text='# Bounded precision continuation results\n\n'
    text+=f"Completed {summary['starts']} starts and {summary['native_sweeps']} sweeps. "
    text+=f"{sum(f['converged'] for f in summary['results'].values())}/{manifest['plan']['maximum_starts']} fits passed. "
    text+=f"Full qualification: {summary['qualification']['qualified']}.\n\n"
    for comparison in summary['comparisons']:
        text+=f"- `{comparison['segment_id']}`: {comparison['profile']['conditional_shape_preference']}.\n"
    text+='\nOriginal results remain preserved. A result requires every primary fit, its repeat and both controls. '
    text+='These are numerical preferences; no statistical calibration or production promotion follows.\n'
    (GUIDE/'RESULTS.md').write_text(text);names.append('RESULTS.md')
    base.follow.atomic_json(GUIDE/'evidence-receipt.json',dict(artifacts={n:prior.sha(GUIDE/n) for n in names},scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            raise ValueError('completed precision recovery cannot resume')
        manifest=prepare();plan=manifest['plan'];digest=prior.sha(OUTPUT/'manifest.json')
        book=prior.journal.Ledger(OUTPUT,digest,[t['identity'] for t in plan['tasks']],fit_limit=200,diagnostic_limit=2)
        extended,meta=arithmetic.load_tangent(OUTPUT/'kernel')
        ordinary_value,vmeta=base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        if meta!=manifest['extended_kernel']:
            raise ValueError('paired arithmetic binary mismatch')
        if vmeta!=manifest['ordinary_value_kernel']:
            raise ValueError('paired reference value kernel mismatch')
        contexts={r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        assumptions={a.name:a for a in base.sensitivity.assumptions()};cases={c['case_id']:c for c in manifest['cases']}
        results={};arrays={}
        for task in plan['tasks']:
            verify();identity=task['identity'];sid=task['segment_id'];target=OUTPUT/(identity.replace('::','-')+'.json')
            saved=base.cached(target,digest)
            if saved is not None:
                results[identity]=saved;continue
            begin=time.monotonic();fit=dict(converged=False,identity=identity,role=task['role'],model=task['model'],case_id=task['case_id'])
            if identity in {r['identity'] for r in book.read('starts')}:
                fit.update(error='interrupted charged start; no retry')
            else:
                book.start(identity)
                base.follow.atomic_json(OUTPUT/'status.json',dict(state='fitting',pid=os.getpid(),identity=identity,completed=len(results),maximum_starts=plan['maximum_starts']))
                try:
                    if sid not in arrays:
                        chosen=task['selected']
                        values,times,gps,provenance=base.segments.extract_segment(Path(chosen['source_path']),contexts[chosen['task']],chosen['segment'])
                        if provenance!=task['provenance']:
                            raise ValueError('paired extraction provenance mismatch')
                        blocks=np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
                        covariance=base.sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,assumptions['h1_v3_tau60'])
                        arrays[sid]=(values,times,gps,covariance)
                    values,times,gps,covariance=arrays[sid];case=cases[task['case_id']]
                    seed,_=base.corpus.initialize(times,gps,values,task['model'])
                    problem=ChargedProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),times,gps,covariance,seed,
                        base.estimator.Bounds(case['limits']),fit_earth_removal=case['profile'],kernel=ordinary_value,tangent_kernel=extended,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.,book=book,identity=identity,
                        maximum_evaluations=task['maximum_evaluations'])
                    reference=task['reference'];point=np.array(reference['normalized_parameters'])
                    if list(problem.bounds.active)!=reference['active_parameters']:
                        raise ValueError('paired parameter order mismatch')
                    start=np.clip(point+np.where(point>=0,-.01,.01),-1,1) if task['role']=='repeat' else point
                    fit.update(solver.fit_candidate(problem,task['model'],start=start,maximum_evaluations=task['maximum_evaluations']))
                    initial_difference=abs(fit['initial_cost']-reference['residual_sum_squares'])/max(reference['residual_sum_squares'],1.)
                    if task['role']!='repeat' and initial_difference>1e-6:
                        raise ValueError('paired initial objective failed reproduction')
                    if fit['evaluations']!=book.count(identity,'fit'):
                        raise ValueError('paired fit accounting mismatch')
                    local=fit.pop('local_linearization');name=identity.replace('::','-')+'-linearization.json.gz'
                    atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(local,sort_keys=True,allow_nan=False).encode(),mtime=0))
                    fit.update(linearization_file=name,linearization_sha256=prior.sha(OUTPUT/name))
                    problem.phase='diagnostic'
                    prediction=problem.predict(np.array(fit['normalized_parameters']),task['model'])
                    old_prediction=book.call(identity,'diagnostic','value',
                        lambda u,m:base.explore.ConditionalProblem.predict(problem,u,m),point,task['model'])
                    errors=prior.physical_difference(prediction,gps,gps)
                    change=prior.physical_difference(prediction,old_prediction,gps)
                    fit.update(track_rms_neu_m=np.sqrt(np.mean(errors**2,axis=0)).tolist(),
                               reference_track_change_rms_neu_m=np.sqrt(np.mean(change**2,axis=0)).tolist())
                    name=identity.replace('::','-')+'-epochs.json.gz'
                    atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(dict(times_s=times.tolist(),errors_neu_m=errors.tolist()),sort_keys=True).encode(),mtime=0))
                    fit.update(epoch_file=name,epoch_sha256=prior.sha(OUTPUT/name))
                except Exception as error:
                    fit.update(converged=False,error=type(error).__name__+': '+str(error))
            fit.update(elapsed_s=time.monotonic()-begin,fit_native_sweeps=book.count(identity,'fit'),
                       diagnostic_native_sweeps=book.count(identity,'diagnostic'),scientific_decision='abstain')
            if fit['fit_native_sweeps']>task['maximum_evaluations']:
                raise ValueError('per-identity fitting allowance exceeded')
            base.save(target,fit,digest);results[identity]=fit
            print(json.dumps(dict(completed=len(results),identity=identity,passed=fit['converged'])),flush=True)
        qualification=qualify(plan,results);repeats={r['identity'].split('::')[0]:r['passed'] for r in qualification['repeatability']}
        comparisons=[]
        case_rows=matched_cases(plan,results,manifest['reused_results'])
        for sid in plan['target_segment_ids']:
            paired=case_rows[sid]
            profile=base.shape.hierarchical_profile(paired)
            if not qualification['controls_passed'] or not repeats[sid]:
                profile.update(conditional_shape_preference='unresolved',rotation_diagnostics=None,
                               rotation_withheld_reason='paired control or scheduled repeat failed')
            comparisons.append(dict(segment_id=sid,cases=paired,profile=profile))
        native=len(book.read('sweeps'))
        if native>plan['maximum_native_sweeps'] or len(book.read('starts'))!=manifest['plan']['maximum_starts']:
            raise ValueError('paired finite accounting mismatch')
        summary=dict(version=VERSION,state='complete',results=results,comparisons=comparisons,qualification=qualification,
                     starts=plan['maximum_starts'],native_sweeps=native,reused_primary_count=len(manifest['reused_results']),scientific_decision='abstain')
        base.follow.atomic_json(OUTPUT/'summary.json',summary)
        base.follow.atomic_json(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,
            summary_sha256=prior.sha(OUTPUT/'summary.json'),journal_hashes={n:prior.sha(OUTPUT/n) for n in ('starts.jsonl','sweeps.jsonl')}))
        base.follow.atomic_json(OUTPUT/'status.json',dict(state='complete',starts=plan['maximum_starts'],native_sweeps=native))
    publish()


def sequence():
    configure('budget');OUTPUT.mkdir(exist_ok=True)
    coordinator=OUTPUT/'coordinator.lock'
    with coordinator.open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state=OUTPUT/'coordinator-status.json'
        for stage in ('budget','remaining'):
            configure(stage);OUTPUT.mkdir(exist_ok=True)
            base.follow.atomic_json(state,dict(state='running',stage=stage,pid=os.getpid(),threads=4))
            if stage=='remaining':
                first=ROOT/'data'/planning.STAGES['budget'][0]
                seal=base.load(first/'completion.json')
                if (seal['state']!='complete' or prior.sha(first/'summary.json')!=seal['summary_sha256']
                        or not base.load(first/'summary.json')['qualification']['controls_passed']):
                    base.follow.atomic_json(state,dict(state='blocked',reason='budget-stage control qualification failed'));return
                base.follow.atomic_json(OUTPUT/'execution-gate.json',dict(
                    preceding_completion_sha256=prior.sha(first/'completion.json'),preceding_summary_sha256=seal['summary_sha256'],
                    controls_passed=True,changes_target_selection=False))
            if (OUTPUT/'completion.json').exists():
                verify();seal=base.load(OUTPUT/'completion.json')
                if prior.sha(OUTPUT/'summary.json')!=seal['summary_sha256']: raise ValueError('completed summary mismatch')
            else: run()
        base.follow.atomic_json(state,dict(state='complete',stages=['budget','remaining']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=tuple(planning.STAGES),default='budget')
    parser.add_argument('--sequence',action='store_true');parser.add_argument('--detach',action='store_true')
    parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--package-only',action='store_true')
    args=parser.parse_args();configure(args.stage);OUTPUT.mkdir(exist_ok=True)
    if args.stage=='remaining' and not (args.sequence or args.prepare_only or args.package_only):
        raise ValueError('remaining stage must follow checked budget stage through --sequence')
    if args.prepare_only:
        for stage in ('budget','remaining') if args.sequence else (args.stage,):
            configure(stage);OUTPUT.mkdir(exist_ok=True)
            with (OUTPUT/'worker.lock').open('a+') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);prepare()
    elif args.package_only: publish()
    elif args.detach:
        if not args.sequence and (OUTPUT/'completion.json').exists():
            raise ValueError('completed stage cannot relaunch')
        coordinator=ROOT/'data'/planning.STAGES['budget'][0]/'coordinator.lock'
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX)
            with coordinator.open('a+') as lock:
                try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError: print('Continuation sequence already running.');return
            for stage in ('budget','remaining'):
                path=ROOT/'data'/planning.STAGES[stage][0]/'worker.lock';path.parent.mkdir(exist_ok=True)
                with path.open('a+') as lock:
                    try: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError: print('Continuation worker already running.');return
            if all((ROOT/'data'/planning.STAGES[s][0]/'completion.json').exists() for s in ('budget','remaining')):
                raise ValueError('completed sequence cannot relaunch')
            flags=['--sequence'] if args.sequence else ['--stage',args.stage]
            with (OUTPUT/'worker.log').open('a') as log:
                child=subprocess.Popen([sys.executable,str(ROOT/'analysis/tests/run_numerical.py'),'--threads','4','--',
                    sys.executable,str(Path(__file__).resolve()),*flags],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(pid=child.pid,state='launched',sequence=args.sequence)))
    elif args.sequence: sequence()
    else:
        if STAGE=='remaining': raise ValueError('remaining stage must follow checked budget stage through --sequence')
        run()


if __name__=='__main__': main()
