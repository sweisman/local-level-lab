# SPDX-License-Identifier: AGPL-3.0-or-later
"""Standard-library bookkeeping controls; no numerical imports or workers."""
import hashlib
import importlib.util
import json
import fcntl
import os
from pathlib import Path
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from lll import ilvis0_control_shards as shards

ROOT=Path(__file__).resolve().parents[2]


def workspace():return tempfile.TemporaryDirectory()


def fixture(root,workers=4,stop_after_failure=False):
    project=root/'project';project.mkdir();(project/'adapter.py').write_text('# fixture only\n')
    (project/'case.json').write_text('{"value":3}\n')
    runner=project/'analysis/tests/ilvis0_control_shards.py';runner.parent.mkdir(parents=True);runner.write_text('# runner fixture\n')
    tasks=[dict(identity=f'task-{i}',payload=dict(i=i),input_key='case',
        limits=dict(native_calls=1,packet_visits=3,bound_calls=1,bound_steps=3)) for i in range(4)]
    output=root/'study'
    shards.prepare(output,project_root=project,tasks=tasks,sources=['adapter.py','analysis/tests/ilvis0_control_shards.py'],inputs={'case':'case.json'},
        adapter='adapter.py',workers=workers,threads=1,maximum_wall_s=60,environment=shards.runtime_environment(),
        stop_after_failure=stop_after_failure)
    return output,project,tasks


class StorageTests(unittest.TestCase):
    def test_full_merge_preserves_assignment_counts_and_artifacts(self):
        with workspace() as tmp:
            output,_,tasks=fixture(Path(tmp))
            for i,task in enumerate(tasks):
                context=shards.TaskContext(output,i,task['identity'])
                context.charge(native_calls=1,packet_visits=3)
                context.charge(bound_calls=1,bound_steps=3)
                context.save('native.json',dict(value=i))
                context.finish(dict(passed=True,scientific_decision='abstain',value=i))
            report=shards.merge(output)
            self.assertTrue(report['passed']);self.assertEqual(report['completed'],4)
            self.assertEqual(report['native_evaluations'],4);self.assertEqual(report['bound_evaluations'],4)
            self.assertEqual(report['charged']['packet_visits'],12)
            self.assertEqual([r['identity'] for r in report['results']],[t['identity'] for t in tasks])

    def test_excess_charge_wrong_assignment_and_retry_are_rejected(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp))
            with self.assertRaises(ValueError):shards.TaskContext(output,1,'task-0')
            context=shards.TaskContext(output,0,'task-0');context.charge(native_calls=1,packet_visits=3)
            with self.assertRaises(ValueError):context.charge(native_calls=1,packet_visits=3)
            with self.assertRaises(ValueError):context.charge(native_calls=0,packet_visits=0)
            with self.assertRaises(ValueError):shards.TaskContext(output,0,'task-0')
            context.finish(dict(passed=False,scientific_decision='abstain',reason='known failure'))
            with self.assertRaises(ValueError):context.charge(bound_calls=1,bound_steps=3)

    def test_changed_frozen_input_and_side_artifact_are_rejected(self):
        with workspace() as tmp:
            output,project,_=fixture(Path(tmp));manifest=shards.verify(output)
            (project/'case.json').write_text('new external version')
            shards.verify(output)  # Execution reads its frozen copy.
            context=shards.TaskContext(output,0,'task-0');relative=context.save('native.json',dict(value=3))
            context.finish(dict(passed=True,scientific_decision='abstain'))
            (output/relative).write_text('corrupt')
            with self.assertRaises(ValueError):shards.merge(output)
            (output/manifest['inputs']['case']['path']).write_text('corrupt input')
            with self.assertRaises(ValueError):shards.verify(output)

    def test_known_identity_in_wrong_shard_is_detected(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));context=shards.TaskContext(output,0,'task-0')
            context.finish(dict(passed=True,scientific_decision='abstain'))
            source=output/'shards/000/results/task-0.json';target=output/'shards/001/results/task-0.json'
            target.write_bytes(source.read_bytes())
            with self.assertRaises(ValueError):shards.merge(output)

    def test_interrupted_start_is_preserved_without_native_retry(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));context=shards.TaskContext(output,0,'task-0')
            context.charge(native_calls=1,packet_visits=3)
            shards.mark_interrupted(output,0,'task-0')
            report=shards.merge(output)
            self.assertFalse(report['passed']);self.assertEqual(report['native_evaluations'],1)
            self.assertEqual(report['results'][0]['status'],'interrupted')
            with self.assertRaises(ValueError):shards.TaskContext(output,0,'task-0')
            with self.assertRaises(ValueError):context.charge(bound_calls=1,bound_steps=3)

    def test_incomplete_charge_transaction_is_preserved_and_blocks_execution(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));shards.TaskContext(output,0,'task-0')
            pending=output/'shards/000/charges/.pending-control';pending.write_text('incomplete')
            with self.assertRaises(ValueError):shards.merge(output)
            self.assertEqual(pending.read_text(),'incomplete')

    def test_changed_result_envelope_is_rejected(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));context=shards.TaskContext(output,0,'task-0')
            context.finish(dict(passed=True,scientific_decision='abstain',value=3))
            path=output/'shards/000/results/task-0.json';row=json.loads(path.read_text())
            row['status']='interrupted';path.write_text(json.dumps(row))
            with self.assertRaises(ValueError):shards.merge(output)

    def test_duplicate_freeze_and_escaped_paths_are_rejected(self):
        with workspace() as tmp:
            root=Path(tmp);output,project,tasks=fixture(root)
            with self.assertRaises(ValueError):shards.prepare(output,project_root=project,tasks=tasks,
                sources=['adapter.py'],inputs={'case':'case.json'},adapter='adapter.py',workers=4,threads=1,
                maximum_wall_s=60,environment={})
            duplicate=[tasks[0],tasks[0]]
            with self.assertRaises(ValueError):shards.prepare(root/'duplicate',project_root=project,tasks=duplicate,
                sources=['adapter.py'],inputs={'case':'case.json'},adapter='adapter.py',workers=1,threads=1,
                maximum_wall_s=60,environment={})
            with self.assertRaises(ValueError):shards.path_within(output,'../outside')


class ProcessTests(unittest.TestCase):
    @staticmethod
    def evaluate(task,context):
        context.charge(native_calls=1,packet_visits=3)
        context.charge(bound_calls=1,bound_steps=3)
        context.save('native.json',dict(value=task['payload']['i']))
        return dict(passed=True,scientific_decision='abstain',value=task['payload']['i'])

    def popen(self,output,seen):
        def spawn(argv,**kwargs):
            shard=int(argv[argv.index('--run-shard')+1]);fd=kwargs['pass_fds'][0];seen.append(shard)
            self.assertTrue(kwargs['start_new_session']);self.assertEqual(kwargs['env']['OPENBLAS_NUM_THREADS'],'1')
            lease=output/f'shards/{shard:03d}/worker.lock'
            with lease.open('rb') as another:
                with self.assertRaises(BlockingIOError):fcntl.flock(another,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with patch.dict(os.environ,kwargs['env'],clear=True):
                shards.run_shard(output,shard,self.evaluate,lease_fd=os.dup(fd))
            # Closing the child's duplicate must not unlock the parent's copy.
            with lease.open('rb') as another:
                with self.assertRaises(BlockingIOError):fcntl.flock(another,fcntl.LOCK_EX|fcntl.LOCK_NB)
            return SimpleNamespace(pid=9000+shard,poll=lambda:0)
        return spawn

    def test_launch_hands_off_locked_leases_and_merges_once(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));seen=[]
            with patch.object(shards.subprocess,'Popen',side_effect=self.popen(output,seen)):
                summary=shards.launch(output,reserved_threads=0)
                self.assertTrue(summary['passed']);self.assertEqual(seen,[0,1,2,3])
                for shard in range(4):
                    progress=json.loads((output/f'shards/{shard:03d}/progress.json').read_text())
                    self.assertEqual(progress['passed'],1)
                with self.assertRaises(ValueError):shards.launch(output,reserved_threads=0)
            self.assertEqual(shards.verify_completion(output)['native_evaluations'],4)

    def test_reservation_and_existing_shard_prevent_any_launch(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));seen=[]
            with patch.object(shards.subprocess,'Popen',side_effect=self.popen(output,seen)):
                with self.assertRaises(ValueError):shards.launch(output,reserved_threads=1)
                with (output/'shards/003/worker.lock').open('rb') as held:
                    fcntl.flock(held,fcntl.LOCK_EX)
                    with self.assertRaises(ValueError):shards.launch(output,reserved_threads=0)
                self.assertEqual(seen,[])

    def test_resume_marks_interrupted_start_without_repeating_it(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp),workers=1)
            context=shards.TaskContext(output,0,'task-0');context.charge(native_calls=1,packet_visits=3)
            seen=[];environment=shards.verify(output)['numerical_environment']
            def evaluate(task,ctx):seen.append(task['identity']);return self.evaluate(task,ctx)
            with patch.dict(os.environ,environment):shards.run_shard(output,0,evaluate)
            report=shards.merge(output)
            self.assertEqual(seen,['task-1','task-2','task-3']);self.assertFalse(report['passed'])
            self.assertEqual(report['native_evaluations'],4);self.assertEqual(report['results'][0]['status'],'interrupted')

    def test_changed_worker_environment_refuses_before_start(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp))
            with patch.dict(os.environ,dict(OPENBLAS_NUM_THREADS='4')):
                with self.assertRaises(ValueError):shards.run_shard(output,0,self.evaluate)
            self.assertEqual(shards.merge(output)['charged_identities'],0)

    def test_status_retains_child_allocation_after_coordinator_loss(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));context=shards.TaskContext(output,0,'task-0')
            context.charge(native_calls=1,packet_visits=3);context.charge(bound_calls=1,bound_steps=3)
            path=Path(__file__).resolve().parents[1]/'status.py'
            spec=importlib.util.spec_from_file_location('sharded_status_control',path)
            status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status)
            with (output/'shards/000/worker.lock').open('rb') as held:
                fcntl.flock(held,fcntl.LOCK_EX)
                report=status.inspect_study(output)
                self.assertEqual(report['state'],'running');self.assertEqual(report['threads'],4)
                self.assertEqual(report['native_calls'],1);self.assertEqual(report['charged_identities'],1)
            self.assertEqual(status.inspect_study(output)['threads'],0)

    def test_spawn_failure_preserves_completed_shards_for_continuation(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));seen=[];spawn=self.popen(output,seen)
            def interrupted_spawn(argv,**kwargs):
                if int(argv[argv.index('--run-shard')+1])==2:raise OSError('controlled spawn failure')
                return spawn(argv,**kwargs)
            with patch.object(shards.subprocess,'Popen',side_effect=interrupted_spawn):
                with self.assertRaises(OSError):shards.launch(output,reserved_threads=0)
            start=(output/'start.json').read_bytes()
            with patch.object(shards.subprocess,'Popen',side_effect=spawn):summary=shards.launch(output,reserved_threads=0)
            self.assertTrue(summary['passed']);self.assertEqual(seen,[0,1,2,3])
            self.assertEqual((output/'start.json').read_bytes(),start)

    def test_original_deadline_cannot_be_reset(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp));context=shards.TaskContext(output,0,'task-0')
            start=json.loads((output/'start.json').read_text());start['started_unix']+=600;start['deadline_unix']+=600
            (output/'start.json').write_text(json.dumps(start))
            with self.assertRaises(ValueError):context.charge(native_calls=1,packet_visits=3)

    def test_declared_failure_stop_preserves_missing_tasks_and_charges(self):
        with workspace() as tmp:
            output,_,_=fixture(Path(tmp),stop_after_failure=True);seen=[]
            def failing(task,context):
                context.charge(native_calls=1,packet_visits=3)
                return dict(passed=False,scientific_decision='abstain',reason='planned control failure')
            spawn=self.popen(output,seen)
            with patch.object(self,'evaluate',side_effect=failing):
                with patch.object(shards.subprocess,'Popen',side_effect=spawn):summary=shards.launch(output,reserved_threads=0)
            self.assertFalse(summary['passed']);self.assertEqual(summary['completed'],1)
            self.assertEqual(summary['native_evaluations'],1);self.assertEqual(summary['state'],'terminal')


REAL_SOURCES=['analysis/lll/'+name for name in ('__init__.py','compute_budget.py','ilvis0_receipt_journal.py','ilvis0_control_shards.py')]
REAL_SOURCES+=['analysis/tests/ilvis0_control_shards.py']
REAL_ADAPTER='''import json,os,sys,time
assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
def evaluate(task,context):
    values=json.loads(context.input_path().read_text())['values'];i=task['payload']['i']
    context.charge(native_calls=1,packet_visits=3)
    context.charge(bound_calls=1,bound_steps=3)
    context.save('execution.json',dict(i=i,pid=os.getpid(),session=os.getsid(0)))
    if task['payload'].get('wait'):
        context.save('ready.json',dict(ready=True));deadline=time.monotonic()+15.
        while not (context.root/'release.json').exists():
            if time.monotonic()>deadline:raise RuntimeError('fixture handshake deadline')
            time.sleep(.01)
    time.sleep(task['payload'].get('delay',0.))
    assert 'numpy' not in sys.modules and 'scipy' not in sys.modules
    return dict(passed=True,scientific_decision='abstain',value=values[i]*values[i],numerical_imports=False)
'''


def real_fixture(root,*,delay=False,wait=False):
    project=root/'project';project.mkdir()
    for name in REAL_SOURCES:
        target=project/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    (project/'adapter.py').write_text(REAL_ADAPTER);(project/'case.json').write_text('{"values":[0,1,2,3]}\n')
    tasks=[dict(identity=f'real-{i}',payload=dict(i=i,delay=.03*(3-i) if delay else 0.,wait=wait and i==0),input_key='case',
        limits=dict(native_calls=1,packet_visits=3,bound_calls=1,bound_steps=3)) for i in range(4)]
    output=root/'study'
    shards.prepare(output,project_root=project,tasks=tasks,sources=REAL_SOURCES+['adapter.py'],inputs={'case':'case.json'},
        adapter='adapter.py',workers=4,threads=1,maximum_wall_s=30,environment=shards.runtime_environment())
    return output


class RealProcessTests(unittest.TestCase):
    def assert_values(self,output,summary):
        self.assertTrue(summary['passed']);values=[]
        for row in summary['results']:
            result=json.loads((output/row['artifact']).read_text())['result']
            values.append(result['value']);self.assertFalse(result['numerical_imports'])
        self.assertEqual(values,[0,1,4,9])
        for i in range(4):
            execution=json.loads((output/f'artifacts/real-{i}/execution.json').read_text())
            self.assertEqual(execution['pid'],execution['session'])

    def test_four_real_processes_preserve_frozen_results(self):
        with workspace() as tmp:
            output=real_fixture(Path(tmp));summary=shards.launch(output,reserved_threads=0)
            self.assert_values(output,summary);shards.verify_completion(output)

    def test_completion_order_does_not_change_manifest_order_or_values(self):
        with workspace() as tmp:
            output=real_fixture(Path(tmp),delay=True);summary=shards.launch(output,reserved_threads=0)
            self.assert_values(output,summary)

    def test_real_child_survives_coordinator_error_and_blocks_duplicate(self):
        with workspace() as tmp:
            output=real_fixture(Path(tmp),wait=True);real_popen=shards.subprocess.Popen;children=[]
            def interrupted_launch(argv,**kwargs):
                if '--run-shard' in argv:
                    if children:raise OSError('controlled coordinator interruption')
                    process=real_popen(argv,**kwargs);children.append(process);return process
                return real_popen(argv,**kwargs)
            try:
                with patch.object(shards.subprocess,'Popen',side_effect=interrupted_launch):
                    with self.assertRaises(OSError):shards.launch(output,reserved_threads=0)
                ready=output/'artifacts/real-0/ready.json';deadline=time.monotonic()+12.
                while not ready.exists() and children[0].poll() is None and time.monotonic()<deadline:time.sleep(.01)
                self.assertTrue(ready.exists());self.assertIsNone(children[0].poll())
                with self.assertRaises(ValueError):shards.launch(output,reserved_threads=0)
            finally:
                (output/'release.json').write_text('{}\n')
                for child in children:child.wait()  # Normal completion; never signal a child.
            start=(output/'start.json').read_bytes();summary=shards.launch(output,reserved_threads=0)
            self.assert_values(output,summary);self.assertEqual((output/'start.json').read_bytes(),start)


if __name__=='__main__':unittest.main()
