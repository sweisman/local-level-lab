# SPDX-License-Identifier: AGPL-3.0-or-later
"""Queued six-file shape refinement; no synthetic studies or calibrated decisions."""
import argparse
import fcntl
import gzip
import hashlib
import importlib.util
import json
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
from lll import ilvis0_shape as shape, ilvis0_refinement as refinement
from lll import ilvis0_gps_sensitivity as sensitivity, ilvis0_observation as observation, runtime

MAX_STARTS = 84  # 72 primary, 12 interruption retries; max2 per identity, never reset.


def load(path):
    if str(path).endswith('.gz'):
        with gzip.open(path, 'rt') as stream: return json.load(stream)
    return json.loads(Path(path).read_text())


def result_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save(path, value, digest):
    follow.atomic_json(path, dict(manifest_sha256=digest, result=value, result_sha256=result_hash(value)))


def cached(path, digest):
    if not path.exists(): return None
    row = load(path)
    if row['manifest_sha256'] != digest or row['result_sha256'] != result_hash(row['result']):
        raise ValueError('refinement result integrity failure')
    return row['result']


def charge(path, identity, digest, tasks):
    with path.open('a+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX); stream.seek(0)
        rows = [json.loads(line) for line in stream]
        if any(r['start'] != i+1 or r['manifest_sha256'] != digest or r['identity'] not in tasks
               or r['maximum_evaluations'] != 200 for i,r in enumerate(rows)):
            raise ValueError('incompatible refinement attempt ledger')
        if identity not in tasks or len(rows) >= MAX_STARTS or sum(r['identity']==identity for r in rows) >= 2:
            raise ValueError('finite refinement allowance exhausted')
        row = dict(start=len(rows)+1, identity=identity, manifest_sha256=digest, maximum_evaluations=200)
        stream.write(json.dumps(row, sort_keys=True)+'\n'); stream.flush(); os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY|os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)
    return row


def import_worker(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def run(root, output, predecessor):
    if output.exists() and not (output/'manifest.json').exists():
        raise ValueError('unmarked refinement output')
    output.mkdir(parents=True, exist_ok=True)
    with (output/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (output/'completion.json').exists(): raise ValueError('completed refinement is frozen')
        old = root/'data/ilvis0-exploratory-20261008'
        evidence = root/'docs/ilvis0-exploratory-20261008'
        receipt = load(evidence/'evidence-receipt.json')
        for name, digest in receipt['artifacts'].items():
            if il.sha256(evidence/name) != digest: raise ValueError('prior six-file evidence changed')
        old_manifest = load(old/'manifest.json'); tasks = old_manifest['tasks']
        if len(tasks) != 6 or len(set(tasks)) != 6: raise ValueError('original six representatives required')
        prior = root/'data/ilvis0-forward-20261007'
        old_worker_path = root/'analysis/tests/ilvis0_exploratory_worker.py'
        diagnostic_path = root/'analysis/tests/ilvis0_corpus_modeling_worker.py'
        old_worker = import_worker(old_worker_path); diagnostics = import_worker(diagnostic_path)
        sources = [Path(m.__file__) for m in (ap,il,follow,installation,forward,estimator,explore,
            shape,refinement,sensitivity,observation,runtime)]
        # Include transitive imported science sources, runner/tests and both kernels.
        sources += [root/'analysis/lll/ilvis0_native.c',root/'analysis/lll/ilvis0_tangent.cpp',
            root/'analysis/lll/ilvis0_corpus_modeling.py',root/'analysis/lll/models.py',
            Path(__file__),old_worker_path,diagnostic_path,root/'analysis/tests/test_ilvis0_shape.py',
            root/'analysis/tests/test_ilvis0_shape_worker.py']
        inputs = [evidence/'evidence-receipt.json',old/'manifest.json',old/'completion.json',
            predecessor/'manifest.json',prior/'summary.json',root/'data/ilvis0-ready/records.jsonl']
        for task in tasks:
            inputs += [prior/(task+'-factors.json.gz'), root/'data/ilvis0-observation-20261007'/(task+'.json'),old/(task+'.json')]
        kernel, build = explore.load_kernel(output/'kernel')
        tangent, derivative_build = shape.load_tangent(output/'kernel')
        cases = [dict(case_id=f'bias{bias:g}_'+('profiled_removal' if profile else 'unsubtracted'),
            constant_gyro_bias_bound_dph=bias,fit_earth_removal=profile,limits=shape.instrument_limits(bias))
            for bias in shape.BIAS_CASES_DPH for profile in (False,True)]
        identities = [task+'::'+case['case_id']+'::'+model for task in tasks for case in cases for model in explore.MODELS]
        manifest = dict(version=shape.VERSION,
            authorization='Now go: instrument-informed refinement, shape first, rotation only after shape',
            sources={str(p):il.sha256(p) for p in sources},inputs={str(p):il.sha256(p) for p in inputs},
            environment=runtime.numerical_environment(),value_kernel=build,tangent_kernel=derivative_build,
            tasks=tasks,identities=identities,cases=cases,maximum_files=6,primary_starts=72,
            maximum_starts=MAX_STARTS,maximum_starts_per_identity=2,maximum_evaluations_per_start=200,
            selection='exact original six representatives and prior complete raw runs; no outcome-dependent replacements',
            covariance='h1_v3_tau60; conservative h10_v30_tau300 fixed-parameter check only',
            clock='nominal200Hz fit; header fixed-parameter sensitivity',
            bias_interpretation='constant residual calibration offset, NOT measured time-varying drift; limits are sensitivity hypotheses',
            comparison_order=['globe_family_vs_flat','rotation_only_given_consistent_globe_shape_preference'],
            predecessor_manifest_sha256=il.sha256(predecessor/'manifest.json'),
            synthetic_campaigns_allowed=False,original_deletion_allowed=False,scientific_eligible=False)
        path = output/'manifest.json'
        if path.exists():
            if load(path) != manifest: raise ValueError('refinement freeze changed')
        else:
            follow.atomic_json(path,manifest); (output/'source-freeze').mkdir()
            for p in sources: shutil.copyfile(p,output/'source-freeze'/p.name)
        digest = il.sha256(path)
        def verify():
            for name, expected in {**manifest['sources'],**manifest['inputs']}.items():
                if il.sha256(name) != expected: raise ValueError('frozen refinement input/source changed')
            if runtime.numerical_environment() != manifest['environment']:
                raise ValueError('refinement numerical environment changed')
        # No numerical overlap with the existing two-thread corpus worker.
        deadline = time.monotonic()+12*3600
        follow.atomic_json(output/'status.json',dict(state='queued',pid=os.getpid(),predecessor=str(predecessor)))
        while not (predecessor/'completion.json').exists():
            verify()
            if time.monotonic() > deadline: raise ValueError('predecessor not complete after12h; queued freeze can resume')
            time.sleep(30)
        completion = load(predecessor/'completion.json')
        if completion['state'] != 'complete' or completion['manifest_sha256'] != manifest['predecessor_manifest_sha256']:
            raise ValueError('predecessor completion mismatch')
        if il.sha256(predecessor/'summary.json.gz') != completion['summary_sha256']:
            raise ValueError('predecessor summary changed')
        # Only ordinary deterministic solver controls, never synthetic campaigns.
        subprocess.run([sys.executable,'-m','pytest','-q','analysis/tests/test_ilvis0_shape.py',
            'analysis/tests/test_ilvis0_shape_worker.py'],
            cwd=root,check=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2'))
        grid = {a.name:a for a in sensitivity.assumptions()}
        prior_rows = {r['task_id']:r for r in load(prior/'summary.json')['results']}
        results = []
        for task in tasks:
            verify(); target = output/(task+'.json'); record = cached(target,digest)
            if record is not None: results.append(record); continue
            original = load(old/(task+'.json'))
            factors = load(prior/(task+'-factors.json.gz'))['factors']
            timing = load(root/'data/ilvis0-observation-20261007'/(task+'.json'))['provenance']['timing']
            # Exact documented source path frozen by original native preparation.
            # Read the ledger only for the six already documented tasks.
            ledger = root/'data/ilvis0-ready/records.jsonl'
            source_record = next((json.loads(line) for line in ledger.read_text().splitlines()
                                  if json.loads(line)['task_id']==task),None)
            if source_record is None: raise ValueError('documented source record missing')
            values,times,gps,provenance = old_worker.prepare(follow.source_path(root/'data/ilvis0-ready',source_record),
                prior_rows[task]['provenance']['source_sha256'],factors,timing['gps_minus_utc_s'])
            if provenance != original['provenance']: raise ValueError('original six-file observation selection changed')
            blocks = np.tile(np.diag([.3**2,.3**2,.7**2]),(len(gps),1,1))
            covs = {name:sensitivity.coordinate_covariance(times,gps[:,0],gps[:,2],blocks,grid[name])
                    for name in ('h1_v3_tau60','h10_v30_tau300')}
            metric = np.column_stack((1/(6378137.+gps[:,2]),1/((6378137.+gps[:,2])*np.cos(gps[:,0])),np.ones(len(gps))))
            case_results = []
            for case in cases:
                fits = []
                for model in explore.MODELS:
                    identity = task+'::'+case['case_id']+'::'+model
                    fit_path = output/(identity.replace('::','-')+'.json'); fit = cached(fit_path,digest)
                    if fit is not None: fits.append(fit); continue
                    seed, force = old_worker.initial(times,gps,values,model)
                    kwargs = dict(fit_earth_removal=case['fit_earth_removal'],kernel=kernel,tangent_kernel=tangent,
                        clock_hypothesis='nominal_200Hz',processing_hypothesis='unsubtracted_increment_hypothesis',
                        maximum_interval_s=.0075,gravity_mps2=9.81,disc_radius_m=6371000.)
                    problem = shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),
                        times,gps,covs['h1_v3_tau60'],seed,estimator.Bounds(case['limits']),**kwargs)
                    start = np.zeros(len(problem.bounds.active))
                    for i,name in enumerate(problem.bounds.active):
                        if name.startswith('accel_gain'): start[i] = np.clip((force/9.81-1)/case['limits'][name],-.9,.9)
                        if name=='earth_removal': start[i] = -1.
                    follow.atomic_json(output/'status.json',dict(state='fitting',pid=os.getpid(),task=task,
                        case_id=case['case_id'],model=model,completed=len(results),total=6))
                    charged = charge(output/'starts.jsonl',identity,digest,identities); begin = time.monotonic()
                    try:
                        fit = shape.fit_shape_candidate(problem,model,start=start)
                        conservative = shape.TangentProblem(values[:,9:12],values[:,12:15],np.full(len(values),.005),
                            times,gps,covs['h10_v30_tau300'],seed,estimator.Bounds(case['limits']),**kwargs)
                        try:
                            header = shape.TangentProblem(values[:,9:12],values[:,12:15],values[:,2],times,gps,
                                covs['h1_v3_tau60'],seed,estimator.Bounds(case['limits']),
                                **dict(kwargs,clock_hypothesis='header_elapsed'))
                        except ValueError as error:
                            header = None; fit['header_sensitivity_error'] = str(error)
                        fit.update(diagnostics.recorded_diagnostics(problem,conservative,header,
                            np.array(fit['normalized_parameters']),model,metric))
                        fit['evaluations'] += fit['diagnostic_predictions']
                        if fit['evaluations'] > 200: raise ValueError('evaluation allowance exceeded')
                    except (ValueError,FloatingPointError) as error:
                        fit = dict(model=model,error=str(error),scientific_decision='abstain')
                    fit.update(start_charge=charged,elapsed_s=time.monotonic()-begin,case_id=case['case_id'])
                    verify(); save(fit_path,fit,digest); fits.append(fit)
                case_results.append(dict(case_id=case['case_id'],fits=fits))
            record = dict(task=task,filename=original.get('filename',task),provenance=provenance,
                cases=case_results,profile=shape.hierarchical_profile(case_results),original_preserved=True)
            verify(); save(target,record,digest); results.append(record)
            print(json.dumps(dict(completed=len(results),task=task,
                shape_preference=record['profile']['conditional_shape_preference'],
                converged=sum(f.get('converged',False) for c in case_results for f in c['fits']))),flush=True)
        summary = dict(version=shape.VERSION,state='complete',results=results,files=len(results),
            starts=len((output/'starts.jsonl').read_text().splitlines()),
            converged_fits=sum(bool(f.get('converged')) for r in results for c in r['cases'] for f in c['fits']),
            failed_fits=sum('error' in f for r in results for c in r['cases'] for f in c['fits']),
            scientific_shape_decision='abstain',scientific_rotation_decision='abstain',originals_deleted=0)
        verify(); observation.gzip_json(output/'summary.json.gz',summary)
        compact = {k:v for k,v in summary.items() if k!='results'}
        compact.update(manifest_sha256=digest,summary_sha256=il.sha256(output/'summary.json.gz'))
        follow.atomic_json(output/'completion.json',compact);follow.atomic_json(output/'status.json',compact)
        report = ['# Six-file shape-first sensitivity results','',
            'These are conditional local fits. No calibrated shape or rotation detection is claimed.','',
            '| Recording | Shape preference across four cases | Converged fits | Rotation diagnostics |',
            '|---|---|---:|---|']
        for r in results:
            p=r['profile']; count=sum(bool(f.get('converged')) for c in r['cases'] for f in c['fits'])
            report.append(f"| {r['filename']} | {p['conditional_shape_preference']} | {count}/12 | {'available conditionally' if p['rotation_diagnostics'] is not None else 'withheld'} |")
        (output/'RESULTS.md').write_text('\n'.join(report)+'\n')
        print(json.dumps(compact),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('data/ilvis0-shape-refinement-20261008'))
    parser.add_argument('--predecessor',type=Path,default=Path('data/ilvis0-corpus-modeling-v2-20261008'))
    parser.add_argument('--detach',action='store_true');args=parser.parse_args()
    root=Path(__file__).resolve().parents[2];output=args.output.resolve()
    if args.detach:
        output.parent.mkdir(parents=True,exist_ok=True)
        with (output.parent/(output.name+'.log')).open('ab',buffering=0) as log:
            child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--output',str(output),
                '--predecessor',str(args.predecessor.resolve())],cwd=root,stdin=subprocess.DEVNULL,
                stdout=log,stderr=log,start_new_session=True,close_fds=True)
        print(json.dumps(dict(pid=child.pid,log=str(output.parent/(output.name+'.log')))))
    else: run(root,output,args.predecessor.resolve())
