# SPDX-License-Identifier: AGPL-3.0-or-later
import json
from lll.studies.artifacts import ArchiveStore
from lll.studies.testing import run


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
