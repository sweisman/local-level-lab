# SPDX-License-Identifier: AGPL-3.0-or-later
import fcntl
import json

import pytest


def prior(tmp_path):
    from lll.studies.artifacts import atomic,encoded,digest
    directory=tmp_path/'prior';directory.mkdir()
    raw=encoded(dict(study='data/parent',manifest_sha256='parent',sources={}))
    atomic(directory/'request.json',raw);(directory/'worker.lock').touch()
    atomic(directory/'results.xml',b'<testsuites><testsuite><testcase name="one"/></testsuite></testsuites>')
    atomic(directory/'completion.json',encoded(dict(state='complete',exit_code=0,request_sha256=digest(raw))))
    return directory,digest(raw)


def test_test_chain_requires_completed_report_and_released_predecessor_lease(tmp_path):
    from lll.studies.testing_chain import predecessor_ready
    directory,sha=prior(tmp_path)
    with (directory/'worker.lock').open('rb') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert predecessor_ready(directory,request_sha256=sha,minimum_tests=1) is None
    assert predecessor_ready(directory,request_sha256=sha,minimum_tests=1)
    (directory/'completion.json').unlink()
    assert predecessor_ready(directory,request_sha256=sha,minimum_tests=1) is None


@pytest.mark.parametrize('change',('request','failed','skipped','short','invalid_xml'))
def test_test_chain_rejects_unqualified_or_changed_predecessor(tmp_path,change):
    from lll.studies.testing_chain import predecessor_ready
    directory,sha=prior(tmp_path)
    minimum=1
    if change=='request':sha='0'*64
    if change=='failed':
        value=json.loads((directory/'completion.json').read_bytes());value['exit_code']=1
        (directory/'completion.json').write_text(json.dumps(value))
    if change=='skipped':(directory/'results.xml').write_text('<testsuites><testsuite><testcase name="one"><skipped/></testcase></testsuite></testsuites>')
    if change=='short':minimum=2
    if change=='invalid_xml':(directory/'results.xml').write_text('broken')
    with pytest.raises(ValueError):predecessor_ready(directory,request_sha256=sha,minimum_tests=minimum)


def test_test_chain_checks_frozen_qualification_sources_without_numerical_imports(tmp_path):
    from lll.studies.testing_chain import verify_sources
    from lll.studies.artifacts import digest
    path=tmp_path/'input.py';path.write_bytes(b'# known source\n')
    verify_sources(tmp_path,{'input.py':digest(path.read_bytes())})
    path.write_bytes(b'# changed source\n')
    with pytest.raises(ValueError):verify_sources(tmp_path,{'input.py':digest(b'# known source\n')})


def test_test_chain_successor_is_called_only_after_qualifying_predecessor(tmp_path,monkeypatch):
    import importlib.util
    from pathlib import Path
    from lll.studies import testing_chain as module
    from lll.studies.artifacts import atomic,encoded,digest
    directory,sha=prior(tmp_path)
    study=tmp_path/'data/parent';study.mkdir(parents=True)
    manifest=encoded(dict(allocation=dict(workers=4,threads=1,total=4)))
    atomic(study/'manifest.json',manifest)
    request=json.loads((directory/'request.json').read_bytes());request['manifest_sha256']=digest(manifest)
    atomic(directory/'request.json',encoded(request));sha=digest(encoded(request))
    atomic(directory/'completion.json',encoded(dict(state='complete',exit_code=0,request_sha256=sha)))
    source=tmp_path/'check.py';source.write_text('# finite tests\n')
    qualification=dict(sources={'check.py':digest(source.read_bytes())},report='data/next/results.xml')
    atomic(tmp_path/'qualification.json',encoded(qualification));calls=[]
    spec=importlib.util.spec_from_file_location('chain_status',Path(__file__).resolve().parents[1]/'status.py')
    status=importlib.util.module_from_spec(spec);spec.loader.exec_module(status);status.ROOT=tmp_path
    def successor(root,study,output,**kwargs):
        assert module.predecessor_ready(directory,request_sha256=sha,minimum_tests=1)
        active=status.inspect_study(tmp_path/'data/chain')
        assert active['state']=='running' and active['threads']==1
        calls.append(kwargs)
        destination=tmp_path/output;destination.mkdir(parents=True)
        atomic(destination/'results.xml',b'<testsuites><testsuite><testcase name="next"/></testsuite></testsuites>')
        return 0
    monkeypatch.setattr(module,'run_after',successor)
    result=module.run(tmp_path,predecessor='prior',qualification='qualification.json',study='data/parent',
        output='data/chain',target='data/next',shards=[0],seconds=30.,arguments=['check.py'],
        predecessor_minimum_tests=1,minimum_tests=1)
    assert result==0 and len(calls)==1
    assert json.loads((tmp_path/'data/chain/completion.json').read_bytes())['exit_code']==0
    finished=status.inspect_study(tmp_path/'data/chain')
    assert finished['state']=='complete' and finished['passed']==1 and finished['threads']==0
    with pytest.raises(ValueError,match='reserved'):
        module.run(tmp_path,predecessor='prior',qualification='qualification.json',study='data/parent',
            output='data/chain',target='data/next',shards=[0],seconds=30.,arguments=['check.py'],
            predecessor_minimum_tests=1,minimum_tests=1)
