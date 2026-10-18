# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite adjacent-boundary follow-up; preserves completed diagnostic workers."""
import argparse
import copy
from contextlib import ExitStack
import fcntl
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'data/ilvis0-boundary-followup-v3-20261016'
GUIDE = ROOT / 'docs/ilvis0-boundary-followup-20261016'
PARENT = ROOT / 'data/ilvis0-boundary-continuation-20261016'
ORIGINAL = ROOT / 'data/ilvis0-boundary-diagnostic-20261016'
QUALIFICATION = ROOT / 'data/ilvis0-boundary-followup-controls-v3-20261016'
QUALIFICATION_GUIDE = ROOT / 'docs/ilvis0-boundary-followup-controls-v3-20261016'
VERSION = 'ilvis0-adjacent-boundary-study-v3'
QUALIFICATION_TESTS = 65
_engine = None


def load(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    sys.path.insert(0, str(ROOT / 'analysis'))
    from lll.ilvis0_receipt_journal import durable_write, encoded
    durable_write(path, encoded(value), replace=True)


def engine():
    global _engine
    if _engine is None:
        sys.path.insert(0, str(ROOT / 'analysis'))
        sys.path.insert(0, str(ROOT / 'analysis/tests'))
        from lll.compute_budget import environment
        os.environ.update(environment(workers=1, threads=4, reserved=0))
        spec = importlib.util.spec_from_file_location('_neighbor_engine', ROOT / 'analysis/tests/ilvis0_precision_continuation_worker.py')
        _engine = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_engine)
    return _engine


def check_hashes(mapping):
    for name, digest in mapping.items():
        if sha(name) != digest: raise ValueError('frozen artifact changed: ' + name)


def sealed(directory, artifact='summary.json', key='summary_sha256', *, published=None):
    c = load(directory / 'completion.json')
    if c['state'] != 'complete' or c['manifest_sha256'] != sha(directory / 'manifest.json') or c[key] != sha(directory / artifact):
        raise ValueError('incomplete or changed dependency')
    public = directory if published is None else published
    for name, digest in load(public / 'evidence-receipt.json')['artifacts'].items():
        if '..' in Path(name).parts or Path(name).is_absolute() or sha(public/name) != digest:
            raise ValueError('invalid published dependency')
        if name in ('manifest.json','completion.json',artifact) and sha(directory/name) != digest:
            raise ValueError('runtime/public dependency mismatch')


def sources():
    values = dict(load(PARENT / 'manifest.json')['sources'])
    for name in ('analysis/lll/ilvis0_boundary_followup.py',
                 'analysis/tests/test_ilvis0_boundary_followup.py',
                 'analysis/tests/test_ilvis0_boundary_followup_worker.py',
                 'analysis/tests/ilvis0_boundary_followup_worker.py'):
        values[str(ROOT/name)] = sha(ROOT/name)
    check_hashes(values)
    return values


def snapshot(directory, values):
    for name, digest in values.items():
        target = directory / 'source-freeze' / Path(name).relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(name, target)
        if sha(target) != digest: raise ValueError('snapshot copy mismatch')


def scientific_inputs(values):
    # Task geometry, endpoint values and provenance are copied into the manifest.
    # These two living publication summaries are not read by the numerical job.
    mutable = {str(ROOT/'docs/ilvis0-current-findings-20261015'/name)
               for name in ('current-stretches.csv','findings-receipt.json')}
    return {name:digest for name,digest in values.items() if name not in mutable}


def qualify():
    QUALIFICATION.mkdir(exist_ok=True)
    QUALIFICATION_GUIDE.mkdir(exist_ok=True)
    with (QUALIFICATION / 'worker.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if any((QUALIFICATION/name).exists() for name in ('start.json', 'completion.json')):
            raise ValueError('charged software qualification cannot restart')
        values = sources()
        snapshot(QUALIFICATION, values)
        manifest = dict(sources=values, inputs={str(GUIDE/'PLAN.md'):sha(GUIDE/'PLAN.md')},
            tests=QUALIFICATION_TESTS, maximum_batches=1, retries=0, threads=4,
            maximum_software_callbacks=4096, maximum_affine_solves=512,
            native_predictions=0, observed_starts=0, original_files_read=0,
            environment={n:importlib.metadata.version(n) for n in ('numpy','scipy','pytest')},
            python=sys.version, timeout_s=120)
        write(QUALIFICATION/'manifest.json', manifest)
        write(QUALIFICATION/'start.json', dict(manifest_sha256=sha(QUALIFICATION/'manifest.json')))
        command = [sys.executable, str(ROOT/'analysis/tests/run_numerical.py'), '--threads', '4', '--',
            sys.executable, '-m', 'pytest', '-q', '--tb=short',
            str(ROOT/'analysis/tests/test_ilvis0_boundary_followup.py'),
            str(ROOT/'analysis/tests/test_ilvis0_boundary_followup_worker.py'),
            str(ROOT/'analysis/tests/test_ilvis0_boundary_stop.py'),
            '--junitxml='+str(QUALIFICATION/'tests.xml')]
        with (QUALIFICATION/'pytest.log').open('w') as log:
            from ilvis0_receipt_qualification_worker import run_batch
            rc = run_batch(command, log, manifest['timeout_s'])
        cases = list(ET.parse(QUALIFICATION/'tests.xml').iter('testcase'))
        result = dict(passed=rc == 0 and len(cases) == QUALIFICATION_TESTS and
            not any(c.find(tag) is not None for c in cases for tag in ('failure','error','skipped')),
            tests=len(cases), returncode=rc, observed_starts=0, native_predictions=0)
        check_hashes(values)
        write(QUALIFICATION/'result.json', result)
        write(QUALIFICATION/'completion.json', dict(state='complete',
            manifest_sha256=sha(QUALIFICATION/'manifest.json'), result_sha256=sha(QUALIFICATION/'result.json')))
        names = ('manifest.json','start.json','result.json','completion.json','tests.xml','pytest.log')
        for name in names: shutil.copyfile(QUALIFICATION/name, QUALIFICATION_GUIDE/name)
        shutil.copytree(QUALIFICATION/'source-freeze', QUALIFICATION_GUIDE/'source-freeze', dirs_exist_ok=True)
        (QUALIFICATION_GUIDE/'README.md').write_text('# Adjacent-boundary software controls\n\n'
            + f"{result['tests']} controls; qualification passed: {result['passed']}. "
            + 'No archival originals, native predictions or observed fits.\n')
        write(QUALIFICATION_GUIDE/'evidence-receipt.json', dict(artifacts={n:sha(QUALIFICATION_GUIDE/n)
              for n in (*names,'README.md')}))
        print(json.dumps(result))


def make_plan(parent, previous):
    tasks = parent['plan']['tasks']
    controls = [copy.deepcopy(t) for t in tasks if t['kind'] == 'control']
    selected = [copy.deepcopy(t) for t in tasks if t['kind'] != 'control'
        and t['task']['segment_id'] == 'bb8061a43b4f14b6262ceda1'
        and t['task']['case_id'] == 'bias1_unsubtracted' and t['task']['model'] == 'sphere_still']
    latest = {r['identity']:r for r in previous['results']}
    if len(controls) != 2 or len(selected) != 2 or len({t['identity'] for t in selected}) != 2:
        raise ValueError('exact target pair and two controls required')
    if {t['source_identity'].split('::')[-1] for t in selected} != {'primary','repeat'}:
        raise ValueError('primary and repeat both required')
    for item in controls + selected:
        if item['kind'] != 'control':
            old = latest.get(item['identity'])
            if old is None or old['status'] != 'complete' or old['reason'] != 'boundary_check_unresolved':
                raise ValueError('completed predeclared failed endpoint required')
            item['kind'] = 'neighbor'
            item['fit'].update(normalized_parameters=old['normalized_parameters'],
                                residual_sum_squares=old['residual_sum_squares'])
        item['previous_identity'] = item['identity']
        item['identity'] = item['source_identity'] + '::neighbor_followup'
        item['maximum_evaluations'] = 3 if item['kind'] == 'control' else 30
    return dict(version=VERSION, tasks=controls+selected, maximum_starts=4,
        maximum_local_joint_nuisance_starts=2, maximum_control_identities=2,
        maximum_native_evaluations=66, numerical_threads=4, retries=0)


def prepare():
    OUTPUT.mkdir(exist_ok=True)
    if (OUTPUT/'manifest.json').exists(): return verify()
    public_parent = ROOT/'docs'/PARENT.name
    sealed(PARENT, published=public_parent)
    sealed(QUALIFICATION_GUIDE, 'result.json', 'result_sha256')
    q = load(QUALIFICATION_GUIDE/'result.json')
    if not q['passed'] or q['tests'] != QUALIFICATION_TESTS: raise ValueError('software gate failed')
    parent = load(ORIGINAL/'manifest.json')
    plan = make_plan(parent, load(PARENT/'summary.json'))
    e = engine()
    values = sources()
    inputs = scientific_inputs(load(PARENT/'manifest.json')['inputs'])
    for directory, names in ((PARENT, ('manifest.json','summary.json','completion.json')),
        (public_parent, ('evidence-receipt.json',)),
        (QUALIFICATION_GUIDE, ('manifest.json','result.json','completion.json','evidence-receipt.json')),
        (GUIDE, ('PLAN.md',))):
        for name in names: inputs[str(directory/name)] = sha(directory/name)
    originals = {t['task']['selected']['source_path']:parent['originals'][t['task']['selected']['source_path']]
                 for t in plan['tasks']}
    _, extended = e.arithmetic.load_tangent(OUTPUT/'kernel')
    if extended != parent['extended_kernel']: raise ValueError('integration kernel changed')
    snapshot(OUTPUT, values)
    shutil.copyfile(OUTPUT/'kernel'/extended['source_file'], OUTPUT/'source-freeze'/extended['source_file'])
    manifest = dict(version=VERSION, plan=plan, sources=values, inputs=inputs, originals=originals,
        extended_kernel=extended, ordinary_value_kernel=parent['ordinary_value_kernel'],
        environment=e.base.runtime.numerical_environment(), original_labels_changed=False,
        scientific_decision='abstain', production_promotion=False)
    write(OUTPUT/'manifest.json', manifest)
    write(OUTPUT/'authorization.json', dict(scope='approved bounded diagnostic roadmap',
        manifest_sha256=sha(OUTPUT/'manifest.json'), maximum_starts=4,
        maximum_native_evaluations=66, numerical_threads=4, retries=0))
    return verify()


def verify(*, originals=True):
    value = load(OUTPUT/'manifest.json')
    if value['version'] != VERSION or value['plan']['maximum_starts'] != 4 or value['plan']['maximum_native_evaluations'] != 66:
        raise ValueError('finite scope changed')
    for section in ('sources','inputs', *(['originals'] if originals else [])): check_hashes(value[section])
    for name, digest in value['sources'].items():
        if sha(OUTPUT/'source-freeze'/Path(name).relative_to(ROOT)) != digest: raise ValueError('source snapshot changed')
    extended = value['extended_kernel']
    if sha(OUTPUT/'source-freeze'/extended['source_file']) != extended['source_sha256']:
        raise ValueError('generated integration snapshot changed')
    e = engine()
    e.base.runtime.check_environment(value['environment'])
    auth = load(OUTPUT/'authorization.json')
    if auth != dict(scope='approved bounded diagnostic roadmap', manifest_sha256=sha(OUTPUT/'manifest.json'),
                    maximum_starts=4, maximum_native_evaluations=66, numerical_threads=4, retries=0):
        raise ValueError('frozen allowance mismatch')
    return value


def publish():
    c = load(OUTPUT/'completion.json')
    if c['manifest_sha256'] != sha(OUTPUT/'manifest.json') or c['summary_sha256'] != sha(OUTPUT/'summary.json'):
        raise ValueError('completion mismatch')
    summary = load(OUTPUT/'summary.json')
    names = ['manifest.json','authorization.json','completion.json','summary.json','starts.jsonl','sweeps.jsonl','charges-index.json']
    for row in summary['results']:
        if row.get('linearization_file'):
            name = row['linearization_file']
            if Path(name).name != name or sha(OUTPUT/name) != row['linearization_sha256']: raise ValueError('native artifact changed')
            names.append(name)
    for name in names: shutil.copyfile(OUTPUT/name, GUIDE/name)
    for name, digest in load(OUTPUT/'charges-index.json').items():
        if '..' in Path(name).parts or Path(name).parts[0] != 'charges' or sha(OUTPUT/name) != digest:
            raise ValueError('charge receipt changed')
    shutil.copytree(OUTPUT/'charges', GUIDE/'charges', dirs_exist_ok=True)
    shutil.copytree(OUTPUT/'source-freeze', GUIDE/'source-freeze', dirs_exist_ok=True)
    text = '# Adjacent-boundary results\n\n'
    text += f"Completed {len(summary['results'])} identities / {summary['native_evaluations']} native calls. "
    text += 'Earlier findings are unchanged pending companion and repeat checks.\n\n'
    text += '| Endpoint | Passed | Calls | Outcome |\n|---|---|---:|---|\n'
    for row in summary['results']:
        text += f"| `{row['source_identity']}` | {row['passed']} | {row['native_evaluations']} | {row.get('reason',row['status'])} |\n"
    (GUIDE/'RESULTS.md').write_text(text)
    write(GUIDE/'evidence-receipt.json', dict(artifacts={n:sha(GUIDE/n) for n in (*names,'RESULTS.md')},
                                           scientific_decision='abstain'))


def run():
    OUTPUT.mkdir(exist_ok=True)
    with ExitStack() as stack:
        for directory in (OUTPUT, PARENT, ORIGINAL, QUALIFICATION):
            lock = stack.enter_context((directory/'worker.lock').open('a+'))
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists(): raise ValueError('completed study cannot restart')
        manifest = prepare()
        verify()
        e = engine(); base = e.base
        import numpy as np
        from lll import ilvis0_boundary_adapter as adapter, ilvis0_boundary_followup as candidate
        from lll import ilvis0_clock_brackets as clock, ilvis0_solver_position as position
        from lll.ilvis0_receipt_journal import Ledger
        tasks = manifest['plan']['tasks']; digest = sha(OUTPUT/'manifest.json')
        book = Ledger(OUTPUT, digest, [t['identity'] for t in tasks], fit_limit=1, diagnostic_limit=30)
        kernel, kmeta = base.explore.load_kernel(ROOT/'data/ilvis0-position-recovery-20261013/kernel')
        tangent, tmeta = e.arithmetic.load_tangent(OUTPUT/'kernel')
        if kmeta != manifest['ordinary_value_kernel'] or tmeta != manifest['extended_kernel']: raise ValueError('kernel/environment mismatch')
        contexts = {r['task_id']:r for r in base.load(ROOT/'data/ilvis0-followup-20261007/summary.json')['results']}
        cases = {c['case_id']:c for c in base.primary_cases()}
        assumption = {a.name:a for a in base.sensitivity.assumptions()}['h1_v3_tau60']
        results = []
        for item in tasks:
            verify(originals=False)
            identity = item['identity']; target = OUTPUT/(identity.replace('::','-')+'.json'); began = time.monotonic()
            saved = base.cached(target, digest)
            if saved is not None: results.append(saved); continue
            result = dict(identity=identity, source_identity=item['source_identity'], kind=item['kind'],
                          segment_id=item['task']['segment_id'], passed=False)
            if item['kind'] != 'control' and any(r['kind']=='control' and not r['passed'] for r in results):
                result.update(status='not_started', reason='control_failed_no_start')
            elif identity in {r['identity'] for r in book.read('starts')}:
                result.update(status='interrupted', reason='charged_identity_no_retry')
            else:
                book.start(identity)
                write(OUTPUT/'status.json', dict(state='checking_neighbors', pid=os.getpid(), identity=identity,
                    completed=len(results), total=4, allocated_numerical_threads=4, native_evaluations=len(book.read('sweeps'))))
                try:
                    task = item['task']; chosen = task['selected']; case = cases[task['case_id']]
                    values, times, gps, provenance = base.segments.extract_segment(Path(chosen['source_path']), contexts[chosen['task']], chosen['segment'])
                    if provenance != task['provenance']: raise ValueError('original extraction changed')
                    blocks = np.tile(np.diag([.3**2,.3**2,.7**2]), (len(gps),1,1))
                    covariance = base.sensitivity.coordinate_covariance(times, gps[:,0], gps[:,2], blocks, assumption)
                    initial, _ = base.corpus.initialize(times, gps, values, task['model'])
                    problem = base.shape.TangentProblem(values[:,9:12], values[:,12:15], np.full(len(values),.005),
                        times, gps, covariance, initial, base.estimator.Bounds(case['limits']), fit_earth_removal=case['profile'],
                        kernel=kernel, tangent_kernel=tangent, clock_hypothesis='nominal_200Hz',
                        processing_hypothesis='unsubtracted_increment_hypothesis', maximum_interval_s=.0075,
                        gravity_mps2=9.81, disc_radius_m=6371000.)
                    reference = item['fit']; point = np.array(reference['normalized_parameters']); cache = {}
                    if list(problem.bounds.active) != reference['active_parameters']: raise ValueError('active parameter order changed')
                    def evaluate(u, *, fresh=False):
                        if not fresh or book.count(identity,'diagnostic') >= item['maximum_evaluations']:
                            raise ValueError('fresh identity allowance exceeded')
                        value = book.call(identity,'diagnostic','tangent',problem.residual_tangent,u,task['model'])
                        if not cache:
                            cost = float(value[0]@value[0]); old = reference['residual_sum_squares']
                            if abs(cost-old)/max(cost,old,1.) > 1e-8: raise ValueError('saved endpoint objective changed')
                        cache[tuple(u)] = value
                        return value
                    physical = lambda d: position.physical_residual_step(problem,d)
                    if item['kind'] == 'neighbor':
                        index = list(problem.bounds.active).index('time_offset')
                        geometry = lambda t: clock.bracket(times,len(values),problem.bounds.limits['time_offset'],t)
                        result.update(candidate.check(point,evaluate,physical,time_index=index,geometry_at=geometry))
                    else:
                        residual,jac,_ = evaluate(point,fresh=True)
                        repeated,_,_ = evaluate(point,fresh=True)
                        repeat = adapter.displacement_metrics(residual,repeated,physical)
                        gate = position.verify_stability(point,residual,jac,evaluate,physical)
                        result.update(passed=bool(repeat['passed'] and gate['passed']),reason=gate['reason'],
                            original_repeat=repeat,smooth_check=gate,normalized_parameters=point.tolist(),
                            evaluations=book.count(identity,'diagnostic'))
                    native = candidate.selected_evaluation(point,result,cache)
                    if native is not None:
                        r,j,edges = native; selected = result['normalized_parameters']
                        name = identity.replace('::','-')+'-linearization.json.gz'
                        local = dict(normalized_parameters=selected,active_parameters=list(problem.bounds.active),residual=r.tolist(),
                            jacobian=j.tolist(),times_s=times.tolist(),gps=gps.tolist(),packet_boundaries=edges,
                            convention='whitened residual derivative by normalized parameter')
                        e.atomic_bytes(OUTPUT/name,gzip.compress(json.dumps(local,sort_keys=True,allow_nan=False).encode(),mtime=0))
                        result.update(linearization_file=name,linearization_sha256=sha(OUTPUT/name),residual_sum_squares=float(r@r))
                    result['status'] = 'complete'
                except Exception as error:
                    result.update(status='error',reason=type(error).__name__+': '+str(error),passed=False)
                    write(OUTPUT/'last-error.json',dict(identity=identity,reason=result['reason'],traceback=traceback.format_exc()))
            result.update(native_evaluations=book.count(identity,'diagnostic'),elapsed_s=time.monotonic()-began,
                          scientific_eligible=False,scientific_decision='abstain',original_labels_changed=False)
            base.save(target,result,digest); results.append(result)
            print(json.dumps({k:result[k] for k in ('identity','status','passed','native_evaluations','elapsed_s')}),flush=True)
        verify(originals=False)
        starts, sweeps = book.read('starts'), book.read('sweeps')
        if len(starts)>4 or len(sweeps)>66: raise ValueError('finite accounting mismatch')
        summary = dict(version=VERSION,state='complete',results=results,native_evaluations=len(sweeps),
            charged_local_joint_nuisance_starts=sum(r['identity'] in {t['identity'] for t in tasks if t['kind']=='neighbor'} for r in starts),
            scientific_decision='abstain',original_labels_changed=False)
        write(OUTPUT/'summary.json',summary); book.export()
        write(OUTPUT/'charges-index.json',{str(p.relative_to(OUTPUT)):sha(p) for p in (OUTPUT/'charges').glob('*.json')})
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=digest,summary_sha256=sha(OUTPUT/'summary.json')))
        write(OUTPUT/'status.json',dict(state='complete',native_evaluations=len(sweeps),allocated_numerical_threads=0))
        publish()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('qualify','prepare-only','detach','package-only'): parser.add_argument('--'+flag,action='store_true')
    args = parser.parse_args(); OUTPUT.mkdir(exist_ok=True)
    if args.qualify: qualify()
    elif args.prepare_only:
        with (OUTPUT/'worker.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); prepare()
    elif args.package_only: publish()
    elif args.detach:
        with (OUTPUT/'launch.lock').open('a+') as launch:
            fcntl.flock(launch,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if (OUTPUT/'completion.json').exists(): raise ValueError('completed study cannot restart')
            with (OUTPUT/'worker.lock').open('a+') as lock: fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            verify()
            with (OUTPUT/'worker.log').open('a') as log:
                child = subprocess.Popen([sys.executable,str(Path(__file__).resolve())],cwd=ROOT,stdin=subprocess.DEVNULL,
                    stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            print(json.dumps(dict(state='launched',pid=child.pid,maximum_native_evaluations=66,numerical_threads=4)))
    else:
        try: run()
        except BaseException as error:
            write(OUTPUT/'failure.json',dict(state='stopped',error=repr(error),traceback=traceback.format_exc()))
            write(OUTPUT/'status.json',dict(state='stopped',allocated_numerical_threads=0,error=repr(error)))
            raise


if __name__ == '__main__': main()
