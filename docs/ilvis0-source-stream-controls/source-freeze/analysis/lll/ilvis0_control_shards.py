# SPDX-License-Identifier: AGPL-3.0-or-later
"""Immutable storage/charging for future sharded native software controls.

Imports no numerical libraries. Execution completion, mathematical acceptance
and observational qualification remain separate. Existing serial studies are
never converted, restarted or written by this module.
"""
from contextlib import ExitStack,contextmanager
import fcntl
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import time

from .compute_budget import allocation,environment as thread_environment
from .ilvis0_receipt_journal import Ledger,durable_write,encoded,digest

VERSION='ilvis0-sharded-native-controls-v1'
RESOURCES=('native_calls','packet_visits','bound_calls','bound_steps')
IDENTITY=re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}')
RUNNER='analysis/tests/ilvis0_control_shards.py'


class BudgetStopped(RuntimeError):pass


def runtime_environment():
    return dict(python=sys.version,executable=sys.executable,platform=platform.platform(),
        packages={name:importlib.metadata.version(name) for name in ('numpy','scipy')})


def path_within(root,name):
    root=Path(root).resolve();name=Path(name)
    if name.is_absolute() or not (root/name).resolve().is_relative_to(root):
        raise ValueError('relative path must remain within its declared root')
    return (root/name).resolve()


def _load(path):return json.loads(Path(path).read_text())
def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);durable_write(path,encoded(value))


def _tasks(tasks,workers):
    if not isinstance(tasks,list) or not workers<=len(tasks)<=10000:raise ValueError('finite nonempty shard/task list required')
    seen=set();out=[]
    for index,task in enumerate(tasks):
        identity=task.get('identity');limits=task.get('limits')
        if (not isinstance(identity,str) or not IDENTITY.fullmatch(identity) or identity in seen
                or not isinstance(limits,dict) or set(limits)!=set(RESOURCES)
                or any(type(v) is not int or v<0 for v in limits.values())
                or task.get('native_kind','tangent') not in ('value','tangent')):
            raise ValueError('unique safe identities and exact finite task limits required')
        encoded(task);seen.add(identity);out.append(dict(task,index=index,shard=index%workers))
    return out


def prepare(output,*,project_root,tasks,sources,inputs,adapter,workers=4,threads=1,maximum_wall_s=3600,environment,stop_after_failure=False):
    output=Path(output);project=Path(project_root).resolve();budget=allocation(workers=workers,threads=threads,reserved=0)
    tasks=_tasks(tasks,workers)
    if (output.exists() or not math.isfinite(maximum_wall_s) or maximum_wall_s<=0
            or not isinstance(environment,dict) or adapter not in sources or not sources or len(set(sources))!=len(sources)
            or type(stop_after_failure) is not bool):
        raise ValueError('new output, explicit adapter/sources, environment and finite deadline required')
    source_paths={name:path_within(project,name) for name in sources}
    input_paths={key:path_within(project,name) for key,name in inputs.items()}
    if (any(not p.is_file() for p in list(source_paths.values())+list(input_paths.values()))
            or any(t.get('input_key') not in input_paths for t in tasks)):
        raise ValueError('explicit existing source/input files and recognized task inputs required')
    encoded(environment);output.mkdir(parents=True)
    copied_sources={};copied_inputs={}
    for name,path in source_paths.items():
        target=output/'source-freeze'/name;target.parent.mkdir(parents=True,exist_ok=True)
        durable_write(target,path.read_bytes());copied_sources[name]=_sha(target)
    for index,(key,path) in enumerate(input_paths.items()):
        name=f'inputs/{index:04d}'+''.join(path.suffixes);target=output/name;target.parent.mkdir(parents=True,exist_ok=True)
        durable_write(target,path.read_bytes());copied_inputs[key]=dict(path=name,source=inputs[key],sha256=_sha(target))
    totals={key:sum(t['limits'][key] for t in tasks) for key in RESOURCES}
    manifest=dict(version=VERSION,tasks=tasks,sources=copied_sources,inputs=copied_inputs,adapter=adapter,
        allocation=budget,numerical_environment=thread_environment(workers=workers,threads=threads),environment=environment,
        limits=dict(totals,maximum_identities=len(tasks),maximum_wall_s=float(maximum_wall_s)),
        stop_after_failure=stop_after_failure,scientific_decision='abstain',scope='generated software controls only')
    _write(output/'manifest.json',manifest)
    _write(output/'authorization.json',dict(manifest_sha256=_sha(output/'manifest.json'),limits=manifest['limits']))
    for shard in range(workers):
        directory=output/'shards'/f'{shard:03d}';(directory/'results').mkdir(parents=True)
        durable_write(directory/'worker.lock',b'')
    return manifest


def verify(output):
    output=Path(output);manifest=_load(output/'manifest.json')
    authorization=_load(output/'authorization.json')
    if (manifest.get('version')!=VERSION or authorization['manifest_sha256']!=_sha(output/'manifest.json')
            or authorization['limits']!=manifest['limits']
            or _tasks(manifest['tasks'],manifest['allocation']['workers'])!=manifest['tasks']):
        raise ValueError('sharded source/task/authorization freeze mismatch')
    a=manifest['allocation']
    if allocation(workers=a['workers'],threads=a['threads'],reserved=a['reserved'])!=a:
        raise ValueError('invalid frozen numerical allocation')
    if manifest['numerical_environment']!=thread_environment(workers=a['workers'],threads=a['threads']):
        raise ValueError('invalid frozen thread environment')
    for name,sha in manifest['sources'].items():
        if _sha(path_within(output/'source-freeze',name))!=sha:raise ValueError('changed frozen source')
    for record in manifest['inputs'].values():
        if _sha(path_within(output,record['path']))!=record['sha256']:raise ValueError('changed frozen input')
    if (output/'start.json').exists() or (output/'start.seal.json').exists():_clock_record(output,manifest)
    return manifest


def _directory(root,manifest,shard):
    if type(shard) is not int or not 0<=shard<manifest['allocation']['workers']:raise ValueError('unknown shard')
    return Path(root)/'shards'/f'{shard:03d}'


def _journal(root,manifest,shard):
    assigned=[t for t in manifest['tasks'] if t['shard']==shard]
    return Ledger(_directory(root,manifest,shard),_sha(Path(root)/'manifest.json'),[t['identity'] for t in assigned],
        fit_limit=max(1,max(t['limits']['native_calls'] for t in assigned)),
        diagnostic_limit=max(1,max(t['limits']['bound_calls'] for t in assigned)))


def _counts(journal,task):
    total={key:0 for key in RESOURCES}
    for row in journal.read('sweeps'):
        if row['identity']!=task['identity']:continue
        if row['phase']=='fit':
            packet=row.get('packet_visits');total['native_calls']+=1
            if row['kind']!=task.get('native_kind','tangent'):raise ValueError('native charge kind mismatch')
            key='packet_visits'
        else:packet=row.get('bound_steps');total['bound_calls']+=1;key='bound_steps'
        if type(packet) is not int or packet<0:raise ValueError('invalid packet reservation')
        total[key]+=packet
    if any(total[key]>task['limits'][key] for key in RESOURCES):raise ValueError('task charge exceeds frozen limit')
    return total


def _task(manifest,shard,identity):
    task=next((t for t in manifest['tasks'] if t['identity']==identity),None)
    if task is None or task['shard']!=shard:raise ValueError('task assigned to a different shard')
    return task


def _begin(root,manifest):
    root=Path(root)
    with (root/'start.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        path=root/'start.json'
        if not path.exists():
            now=time.time();_write(path,dict(manifest_sha256=_sha(root/'manifest.json'),started_unix=now,
                deadline_unix=now+manifest['limits']['maximum_wall_s']))
            _write(root/'start.seal.json',dict(manifest_sha256=_sha(root/'manifest.json'),sha256=_sha(path)))
        return _clock_record(root,manifest)


def _clock_record(root,manifest):
    root=Path(root)
    if not (root/'start.json').exists() or not (root/'start.seal.json').exists():
        raise ValueError('incomplete original deadline transaction; no reset')
    start=_load(root/'start.json');seal=_load(root/'start.seal.json')
    if (seal['sha256']!=_sha(root/'start.json') or seal['manifest_sha256']!=_sha(root/'manifest.json')
            or start['manifest_sha256']!=seal['manifest_sha256']
            or start['deadline_unix']!=start['started_unix']+manifest['limits']['maximum_wall_s']):
        raise ValueError('original deadline or freeze changed')
    return start


def _check_continue(root,manifest):
    root=Path(root);start=_begin(root,manifest)
    if (root/'stop-request.json').exists():
        stop=_load(root/'stop-request.json')
        if stop['manifest_sha256']!=_sha(root/'manifest.json'):raise ValueError('stop request source mismatch')
        raise BudgetStopped(stop['reason'])
    if time.time()>=start['deadline_unix']:raise BudgetStopped('original cooperative deadline exhausted')


def _replace(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);durable_write(path,encoded(value),replace=True)


def _request_stop(root,reason):
    root=Path(root)
    with (root/'stop-request.lock').open('a+b') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if not (root/'stop-request.json').exists():
            _write(root/'stop-request.json',dict(manifest_sha256=_sha(root/'manifest.json'),reason=reason,requested_unix=time.time()))


def _seal(root,manifest,shard,task,result,status,artifacts):
    directory=_directory(root,manifest,shard);identity=task['identity'];normal=directory/'results'/(identity+'.json')
    if (normal.with_suffix('.seal.json')).exists():raise ValueError('result already sealed')
    target=normal if not normal.exists() else directory/'results'/(identity+'.interrupted.json')
    if status!='interrupted' and target!=normal:raise ValueError('unsealed prior result must remain interrupted')
    envelope=dict(manifest_sha256=_sha(Path(root)/'manifest.json'),identity=identity,shard=shard,task_sha256=digest(task),
        status=status,result=result,result_sha256=digest(result),artifacts=artifacts,
        charged=_counts(_journal(root,manifest,shard),task))
    _write(target,envelope)
    _write(target.with_suffix('.seal.json'),dict(manifest_sha256=envelope['manifest_sha256'],sha256=_sha(target)))
    return envelope


class TaskContext:
    def __init__(self,study,shard,identity):
        self.root=Path(study);self.manifest=verify(self.root);self.shard=shard
        self.task=_task(self.manifest,shard,identity);self.journal=_journal(self.root,self.manifest,shard)
        self.directory=self.root/'artifacts'/identity;self.artifacts={};self.finished=False
        _check_continue(self.root,self.manifest)
        self.journal.start(identity)

    def _writable(self):
        directory=_directory(self.root,self.manifest,self.shard)/'results';identity=self.task['identity']
        sealed=any((directory/(identity+suffix+'.seal.json')).exists() for suffix in ('','.interrupted'))
        if self.finished or sealed:raise ValueError('sealed task cannot execute or write more work')

    def charge(self,**increase):
        self._writable()
        _check_continue(self.root,self.manifest)
        native=set(increase)=={'native_calls','packet_visits'}
        bound=set(increase)=={'bound_calls','bound_steps'}
        if not (native or bound) or any(type(v) is not int or v<0 for v in increase.values()):
            raise ValueError('one complete finite operation reservation required')
        if increase['native_calls' if native else 'bound_calls']!=1:raise ValueError('charge exactly one operation')
        current=_counts(self.journal,self.task)
        if any(current[k]+increase.get(k,0)>self.task['limits'][k] for k in RESOURCES):
            raise ValueError('task allowance exhausted; no operation performed')
        self.journal.append('sweeps',dict(identity=self.task['identity'],phase='fit' if native else 'diagnostic',
            kind=self.task.get('native_kind','tangent') if native else 'value',
            **{'packet_visits' if native else 'bound_steps':increase['packet_visits' if native else 'bound_steps']}))

    def save(self,name,value):
        self._writable()
        path=path_within(self.directory,name);_write(path,value);return self.note_file(path)

    def note_file(self,path):
        self._writable()
        path=Path(path).resolve()
        if not path.is_relative_to(self.directory.resolve()) or not path.is_file():raise ValueError('owned task artifact required')
        name=str(path.relative_to(self.root.resolve()));sha=_sha(path)
        if name in self.artifacts and self.artifacts[name]!=sha:raise ValueError('task artifact changed')
        self.artifacts[name]=sha;return name

    def input_path(self,key=None):
        key=self.task['input_key'] if key is None else key
        if key not in self.manifest['inputs']:raise ValueError('input is outside frozen selection')
        record=self.manifest['inputs'][key];path=path_within(self.root,record['path'])
        if _sha(path)!=record['sha256']:raise ValueError('frozen input changed')
        return path

    def finish(self,result):
        self._writable()
        if type(result.get('passed')) is not bool or result.get('scientific_decision')!='abstain':
            raise ValueError('one explicit software result and continued scientific abstention required')
        encoded(result)
        envelope=_seal(self.root,self.manifest,self.shard,self.task,result,'complete',self.artifacts)
        self.finished=True;return envelope


@contextmanager
def _lease(path,exclusive):
    with Path(path).open('rb') as handle:
        try:fcntl.flock(handle, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('shard is still owned; no duplicate execution or merge') from None
        try:yield handle
        finally:fcntl.flock(handle,fcntl.LOCK_UN)


def mark_interrupted(study,shard,identity):
    root=Path(study);manifest=verify(root);directory=_directory(root,manifest,shard)
    with _lease(directory/'worker.lock',True):
        task=_task(manifest,shard,identity);journal=_journal(root,manifest,shard)
        if identity not in {r['identity'] for r in journal.read('starts')}:raise ValueError('uncharged task cannot be interrupted')
        return _seal(root,manifest,shard,task,dict(passed=False,scientific_decision='abstain',reason='charged work interrupted; not retried'),
            'interrupted',{})


def merge(study):
    root=Path(study);manifest=verify(root);rows=[];totals={key:0 for key in RESOURCES};starts=0
    with ExitStack() as stack:
        for shard in range(manifest['allocation']['workers']):
            directory=_directory(root,manifest,shard);stack.enter_context(_lease(directory/'worker.lock',False))
            journal=_journal(root,manifest,shard);charged={r['identity'] for r in journal.read('starts')};starts+=len(charged)
            for task in manifest['tasks']:
                identity=task['identity'];paths=[directory/'results'/(identity+suffix+'.json') for suffix in ('','.interrupted')]
                if task['shard']!=shard:
                    if any(p.exists() or p.with_suffix('.seal.json').exists() for p in paths):raise ValueError('result in wrong shard or duplicate identity')
                    continue
                counts=_counts(journal,task)
                for key in RESOURCES:totals[key]+=counts[key]
                sealed=[p for p in paths if p.with_suffix('.seal.json').exists()]
                if len(sealed)>1:raise ValueError('multiple sealed outcomes for one charged identity')
                if not sealed:continue
                path=sealed[0];seal=_load(path.with_suffix('.seal.json'));envelope=_load(path)
                if (identity not in charged or seal['sha256']!=_sha(path) or seal['manifest_sha256']!=_sha(root/'manifest.json')
                        or envelope['manifest_sha256']!=seal['manifest_sha256'] or envelope['identity']!=identity
                        or envelope['shard']!=shard or envelope['task_sha256']!=digest(task) or envelope['charged']!=counts
                        or envelope['result_sha256']!=digest(envelope['result']) or envelope['status'] not in ('complete','interrupted')):
                    raise ValueError('result provenance, sealing or accounting mismatch')
                for name,sha in envelope['artifacts'].items():
                    artifact=path_within(root,name)
                    if not artifact.is_relative_to((root/'artifacts'/identity).resolve()) or _sha(artifact)!=sha:
                        raise ValueError('changed or misplaced task artifact')
                result=envelope['result']
                if type(result.get('passed')) is not bool or result.get('scientific_decision')!='abstain':raise ValueError('invalid software result')
                rows.append(dict(identity=identity,index=task['index'],status=envelope['status'],passed=result['passed'],
                    artifact=str(path.relative_to(root)),artifact_sha256=_sha(path),charged=counts))
    rows.sort(key=lambda r:r['index'])
    return dict(version=VERSION,completed=len(rows),total=len(manifest['tasks']),charged_identities=starts,charged=totals,results=rows,
        native_evaluations=totals['native_calls'],bound_evaluations=totals['bound_calls'],
        passed=len(rows)==len(manifest['tasks']) and all(r['passed'] and r['status']=='complete' for r in rows),
        scientific_decision='abstain',observational_coverage_qualified=False)


def _has_sealed(directory,identity):
    return any((directory/'results'/(identity+suffix+'.seal.json')).exists() for suffix in ('','.interrupted'))


def _validate_own_results(root,manifest,shard):
    directory=_directory(root,manifest,shard);journal=_journal(root,manifest,shard)
    for task in manifest['tasks']:
        if task['shard']!=shard:continue
        for suffix in ('','.interrupted'):
            path=directory/'results'/(task['identity']+suffix+'.json');seal=path.with_suffix('.seal.json')
            if not seal.exists():continue
            row=_load(path);receipt=_load(seal)
            if (receipt['sha256']!=_sha(path) or receipt['manifest_sha256']!=_sha(Path(root)/'manifest.json')
                    or row['manifest_sha256']!=receipt['manifest_sha256'] or row['identity']!=task['identity']
                    or row['shard']!=shard or row['task_sha256']!=digest(task)
                    or row['charged']!=_counts(journal,task) or row['result_sha256']!=digest(row['result'])):
                raise ValueError('saved shard result changed; no new work allowed')
            for name,sha in row['artifacts'].items():
                path=path_within(root,name)
                if not path.is_relative_to((Path(root)/'artifacts'/task['identity']).resolve()) or _sha(path)!=sha:
                    raise ValueError('saved shard artifact changed; no new work allowed')


def _progress(root,manifest,shard,journal,last_identity=None):
    directory=_directory(root,manifest,shard);completed=[];passed=0
    for task in manifest['tasks']:
        if task['shard']!=shard:continue
        for suffix in ('','.interrupted'):
            path=directory/'results'/(task['identity']+suffix+'.json')
            if path.with_suffix('.seal.json').exists():
                row=_load(path);completed.append(task['identity']);passed+=row['result']['passed'] is True
    sweeps=journal.read('sweeps')
    _replace(directory/'progress.json',dict(completed=completed,passed=passed,
        native_evaluations=sum(r['phase']=='fit' for r in sweeps),charged_identities=len(journal.read('starts')),last_identity=last_identity))


def run_shard(study,shard,evaluate=None,*,lease_fd=None):
    root=Path(study).resolve();manifest=verify(root);directory=_directory(root,manifest,shard)
    if manifest['environment']!=runtime_environment() or any(os.environ.get(k)!=v for k,v in manifest['numerical_environment'].items()):
        raise ValueError('worker environment differs from frozen one-thread allocation')
    if (root/'completion.json').exists() or (directory/'done.json').exists():raise ValueError('completed worker cannot restart')
    fd=os.open(directory/'worker.lock',os.O_RDONLY) if lease_fd is None else lease_fd
    try:
        expected=(directory/'worker.lock').stat();actual=os.fstat(fd)
        if (actual.st_dev,actual.st_ino)!=(expected.st_dev,expected.st_ino):raise ValueError('inherited lease identifies another shard')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('shard already owned; no duplicate worker') from None
        _begin(root,manifest);_validate_own_results(root,manifest,shard)
        _replace(directory/'status.json',dict(state='running',pid=os.getpid(),numerical_threads=manifest['allocation']['threads']))
        if evaluate is None:
            frozen=root/'source-freeze';sys.path.insert(0,str(frozen/'analysis'))
            spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',path_within(frozen,manifest['adapter']))
            module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);evaluate=module.evaluate
        journal=_journal(root,manifest,shard);started={r['identity'] for r in journal.read('starts')};reason=None
        for task in manifest['tasks']:
            identity=task['identity']
            if task['shard']!=shard or _has_sealed(directory,identity):continue
            if identity in started:
                _seal(root,manifest,shard,task,dict(passed=False,scientific_decision='abstain',reason='charged work interrupted; not retried'),
                    'interrupted',{})
                if manifest['stop_after_failure']:_request_stop(root,'interrupted charged task')
                _progress(root,manifest,shard,journal,identity)
                continue
            try:_check_continue(root,manifest)
            except BudgetStopped as error:reason=str(error);break
            context=TaskContext(root,shard,identity)
            try:
                result=evaluate(task,context);context.finish(result)
            except Exception as error:
                result=dict(passed=False,scientific_decision='abstain',error_type=type(error).__name__,reason=str(error))
                if not context.finished:context.finish(result)
            if not result['passed'] and manifest['stop_after_failure']:_request_stop(root,'failed control: '+identity)
            _progress(root,manifest,shard,journal,identity)
        _write(directory/'done.json',dict(manifest_sha256=_sha(root/'manifest.json'),shard=shard,reason=reason,finished_unix=time.time()))
        _replace(directory/'status.json',dict(state='complete',pid=os.getpid(),numerical_threads=0))
    finally:
        # An inherited open-file description may still have a parent copy.
        # Closing this descriptor preserves its lease until every copy closes.
        os.close(fd)


def _finish_study(root,manifest):
    for shard in range(manifest['allocation']['workers']):
        journal=_journal(root,manifest,shard);directory=_directory(root,manifest,shard)
        for start in journal.read('starts'):
            if not _has_sealed(directory,start['identity']):mark_interrupted(root,shard,start['identity'])
    report=merge(root);state='complete' if report['passed'] else 'terminal'
    start=_begin(root,manifest)
    summary=dict(report,state=state,elapsed_s=time.time()-start['started_unix'],
        terminal_reason=None if state=='complete' else 'not every frozen task completed and passed; charges preserved')
    _write(root/'summary.json',summary)
    _write(root/'completion.json',dict(state=state,manifest_sha256=_sha(root/'manifest.json'),summary_sha256=_sha(root/'summary.json')))
    _replace(root/'status.json',dict(state=state,numerical_threads=0,total=len(manifest['tasks'])))
    return summary


def verify_completion(study):
    root=Path(study);verify(root);completion=_load(root/'completion.json');summary=_load(root/'summary.json')
    if (completion['manifest_sha256']!=_sha(root/'manifest.json') or completion['summary_sha256']!=_sha(root/'summary.json')
            or completion['state']!=summary['state']):raise ValueError('changed sealed completion')
    current=merge(root)
    if any(summary[k]!=current[k] for k in current):raise ValueError('sealed summary differs from immutable shard evidence')
    return summary


def launch(study,*,reserved_threads):
    root=Path(study).resolve();manifest=verify(root);a=manifest['allocation']
    allocation(workers=a['workers'],threads=a['threads'],reserved=reserved_threads)
    if manifest['environment']!=runtime_environment():raise ValueError('coordinator environment differs from freeze')
    if (root/'completion.json').exists():raise ValueError('completed study cannot restart')
    runner=path_within(root/'source-freeze',RUNNER)
    if RUNNER not in manifest['sources'] or not runner.is_file():raise ValueError('frozen worker entry required')
    with (root/'worker.lock').open('a+b') as coordinator:
        try:fcntl.flock(coordinator,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('coordinator already active') from None
        descriptors={};processes=[]
        try:
            # Acquire every lease before creating any child. Inheritance then
            # leaves no ownership gap during process startup or disconnection.
            for shard in range(a['workers']):
                fd=os.open(_directory(root,manifest,shard)/'worker.lock',os.O_RDONLY);descriptors[shard]=fd
                try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:raise ValueError('prior shard is still owned; no new children') from None
            _begin(root,manifest)
            _replace(root/'status.json',dict(state='running',pid=os.getpid(),numerical_threads=a['workers']*a['threads'],total=len(manifest['tasks'])))
            for shard in range(a['workers']):
                directory=_directory(root,manifest,shard)
                if (directory/'done.json').exists():os.close(descriptors.pop(shard));continue
                fd=descriptors[shard];env={**os.environ,**manifest['numerical_environment']}
                with (directory/'worker.log').open('ab') as log:
                    process=subprocess.Popen([sys.executable,str(runner),'--study',str(root),'--run-shard',str(shard),'--lease-fd',str(fd)],
                        cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,pass_fds=(fd,))
                processes.append(process);os.close(descriptors.pop(shard))
            while any(p.poll() is None for p in processes):
                progress=0;passed=0
                for shard in range(a['workers']):
                    path=_directory(root,manifest,shard)/'progress.json'
                    if path.exists():
                        snapshot=_load(path);progress+=len(snapshot['completed']);passed+=snapshot['passed']
                _replace(root/'progress.json',dict(completed=progress,passed=passed))
                time.sleep(.25)
            return _finish_study(root,manifest)
        finally:
            # Never signal children, including when a later spawn fails.
            for fd in descriptors.values():os.close(fd)
