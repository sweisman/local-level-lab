# SPDX-License-Identifier: AGPL-3.0-or-later
import json
import socket
import pytest
from lll.studies import testing
from lll.studies.artifacts import ArchiveStore
from lll.studies.testing import run


@pytest.mark.parametrize('stage',['create','send'])
def test_socket_denial_stops_before_lock_restore_or_child_start(tmp_path,monkeypatch,stage):
    def denied(*a,**k):raise PermissionError('local socket denied')
    def forbidden(*a,**k):raise AssertionError('fixture work started before socket preflight')
    closed=[]
    class Pipe:
        def __enter__(self):return self
        def __exit__(self,*a):closed.append(self)
        def settimeout(self,value):pass
        send=denied
    pair=denied if stage=='create' else lambda:(Pipe(),Pipe())
    monkeypatch.setattr(socket,'socketpair',pair)
    monkeypatch.setattr(testing,'ArchiveStore',forbidden)
    monkeypatch.setattr(testing.subprocess,'Popen',forbidden)
    with pytest.raises(RuntimeError,match='local socket'):
        run(tmp_path,['server/tests'],threads=4)
    assert not (tmp_path/'data/study-test-runtime').exists()
    assert len(closed)==(2 if stage=='send' else 0)


def test_failed_tests_release_restored_fixtures_without_signaling(tmp_path,monkeypatch):
    path=tmp_path/'docs/example/results/a.json';path.parent.mkdir(parents=True);path.write_text('{}')
    store=ArchiveStore(tmp_path);store.pack(['docs/example/results/a.json']);store.compact()
    class Child:
        pid=42
        def wait(self):
            assert path.is_file()
            return 1
    def popen(args,**kwargs):
        assert 'faulthandler_timeout=300' in args
        assert str(tmp_path/'data/study-test-runtime/results.xml') in args
        assert kwargs['env']['OMP_THREAD_LIMIT']=='2'
        assert kwargs['env']['PYTHONDONTWRITEBYTECODE']=='1'
        assert len(kwargs['pass_fds'])==1
        return Child()
    monkeypatch.setattr('lll.studies.testing.subprocess.Popen',popen)
    assert run(tmp_path,['tests'],threads=2,reserved=2)==1
    assert not path.exists()
    status=json.loads((tmp_path/'data/study-test-runtime/status.json').read_text())
    assert status['state']=='complete' and status['exit_code']==1 and status['numerical_threads']==0


def test_default_suite_runs_peak_memory_controls_in_a_fresh_process(tmp_path,monkeypatch):
    """Full-suite collection must not inflate the controls' process RSS."""
    calls=[]
    class Child:
        pid=42
        def wait(self):return 0
    def popen(args,**kwargs):
        calls.append((args,kwargs['env']))
        return Child()
    monkeypatch.setattr(testing,'check_local_socket_io',lambda:None)
    monkeypatch.setattr(testing.subprocess,'Popen',popen)
    assert run(tmp_path,[],threads=2,reserved=2)==0
    assert len(calls)==2
    isolated={
        'analysis/tests/test_ilvis0_dense_bound_batches.py',
        'analysis/tests/test_ilvis0_native_prefix_long.py',
        'analysis/tests/test_ilvis0_native_prefix_recovery.py',
    }
    peak,peak_env=calls[0]
    main,main_env=calls[1]
    assert isolated <= set(peak)
    assert '--junitxml' in peak
    assert str(tmp_path/'data/study-test-runtime/peak-memory-results.xml') in peak
    assert peak_env['OMP_THREAD_LIMIT']=='1'
    assert peak_env['OPENBLAS_NUM_THREADS']=='1'
    assert 'analysis/tests' in main and 'server/tests' in main
    assert {f'--ignore={name}' for name in isolated} <= set(main)
    assert str(tmp_path/'data/study-test-runtime/results.xml') in main
    assert main_env['OMP_THREAD_LIMIT']=='2'


def test_peak_memory_controls_run_before_archive_expansion(tmp_path,monkeypatch):
    """Forked pytest inherits the runner's peak RSS, even after exec."""
    events=[]
    class Store:
        def __init__(self,root):pass
        def catalog(self):
            events.append('catalog')
            return {'paths':{}}
        def restore(self,root,*,names):events.append('restore')
        def compact(self,*,names):
            events.append('compact')
            return 0
    class Child:
        pid=42
        def wait(self):return 0
    def popen(args,**kwargs):
        events.append('peak' if any(str(arg).endswith('/peak-memory-results.xml')
                                    for arg in args) else 'main')
        return Child()
    monkeypatch.setattr(testing,'check_local_socket_io',lambda:None)
    monkeypatch.setattr(testing,'ArchiveStore',Store)
    monkeypatch.setattr(testing.subprocess,'Popen',popen)
    assert run(tmp_path,[],threads=4)==0
    assert events==['peak','catalog','restore','main','compact']


def test_interrupted_cleanup_compacts_only_saved_restoration_list(tmp_path):
    path=tmp_path/'docs/example/results/a.json'
    path.parent.mkdir(parents=True)
    path.write_text('{"saved":true}')
    unrelated=tmp_path/'docs/other.txt'
    unrelated.write_text('keep')
    store=ArchiveStore(tmp_path)
    store.pack(['docs/example/results/a.json'])
    store.compact()
    store.restore(tmp_path,names=['docs/example/results/a.json'])
    directory=tmp_path/'data/study-test-runtime'
    directory.mkdir(parents=True)
    (directory/'restore-list.json').write_text(json.dumps(['docs/example/results/a.json']))
    (directory/'status.json').write_text(json.dumps(dict(state='testing',phase=2,pid=123)))
    result=testing.cleanup_interrupted(tmp_path)
    assert result['compacted_files']==1
    assert not path.exists() and unrelated.read_text()=='keep'
    assert json.loads((directory/'status.json').read_text())['state']=='interrupted'
    assert store.verify(names=['docs/example/results/a.json'])


def test_cleanup_cli_uses_the_verified_test_restoration_list(tmp_path,monkeypatch,capsys):
    from lll.studies.runtime import command
    called=[]
    def cleanup(root):
        called.append(root)
        return dict(state='interrupted',compacted_files=1)
    monkeypatch.setattr(testing,'cleanup_interrupted',cleanup)
    assert command(['--root',str(tmp_path),'test-cleanup'])==0
    assert called==[tmp_path.resolve()]
    assert json.loads(capsys.readouterr().out)['compacted_files']==1


def test_detached_launcher_writes_log_and_separates_worker_session(tmp_path,monkeypatch):
    calls=[]
    class Child:
        pid=8123
    def popen(args,**kwargs):
        calls.append((args,kwargs))
        return Child()
    monkeypatch.setattr(testing,'check_local_socket_io',lambda:None)
    monkeypatch.setattr(testing.subprocess,'Popen',popen)
    result=testing.launch_detached(tmp_path,[],threads=2,reserved=2)
    assert result['pid']==8123
    assert len(calls)==1
    args,options=calls[0]
    assert 'test-worker' in args
    assert options['start_new_session'] is True
    assert options['stdin'] is testing.subprocess.DEVNULL
    assert options['stderr'] is testing.subprocess.STDOUT
    assert options['env']['LLL_TEST_LAUNCH_TOKEN']
    assert options['env']['PYTHONPATH'].startswith(str(tmp_path/'analysis'))
    status=json.loads((tmp_path/'data/study-test-runtime/status.json').read_text())
    assert status['state']=='launching'
    assert (tmp_path/'data/study-test-runtime/run.log').is_file()


def test_detached_test_cli_routes_without_running_in_caller(tmp_path,monkeypatch,capsys):
    from lll.studies.runtime import command
    called=[]
    def launch(root,arguments,*,threads,reserved):
        called.append((root,arguments,threads,reserved))
        return dict(state='launching',pid=42)
    monkeypatch.setattr(testing,'launch_detached',launch)
    assert command(['--root',str(tmp_path),'test-detached','--threads','2',
                    '--reserved-threads','2','--','analysis/tests/test_study_testing.py'])==0
    assert called==[(tmp_path.resolve(),['analysis/tests/test_study_testing.py'],2,2)]
    assert json.loads(capsys.readouterr().out)['state']=='launching'
