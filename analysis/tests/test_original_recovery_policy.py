"""A reusable recovery freeze survives completion and rejects mutation."""

import json
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from lll import ilvis0_control_shards as runner
from lll.studies import original_recovery_policy as policy
from lll.studies import task_resume


ROOT = Path(__file__).resolve().parents[2]


def _prepared(tmp_path):
    for name in set(task_resume.qualification_sources(tmp_path)+
                    [policy.SELF, runner.RUNNER]):
        destination = tmp_path/name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT/name).read_bytes())
    (tmp_path/'adapter.py').write_text(
        'def evaluate(task, context): return dict(passed=True)\n')
    (tmp_path/'recipe.json').write_text('{}')
    registry = tmp_path/'analysis/study-status.json'
    registry.parent.mkdir(exist_ok=True)
    registry.write_text('{"studies":[]}')
    (tmp_path/'analysis/study-status.lock').touch()
    parent = tmp_path/'data/parent'
    runner.prepare(parent, project_root=tmp_path,
                   tasks=[dict(identity='case', input_key='recipe',
                               payload={}, native_kind='tangent',
                               limits=dict(native_calls=3, packet_visits=9,
                                           bound_calls=0, bound_steps=0))],
                   sources=['adapter.py', runner.RUNNER],
                   inputs={'recipe': 'recipe.json'}, adapter='adapter.py',
                   workers=1, threads=1, maximum_wall_s=3600,
                   environment=runner.runtime_environment(),
                   accounting_format='sqlite-v1', scope='toy freeze')
    request = policy.request_qualification(
        tmp_path, output='qualification-request.json',
        report='qualification-report.xml')
    suite = ET.Element('testsuite', tests=str(len(task_resume.REQUIRED_TESTS)),
                       failures='0', errors='0', skipped='0')
    for name in task_resume.REQUIRED_TESTS:
        ET.SubElement(suite, 'testcase', name=name, classname='task_resume')
    (tmp_path/request['report']).write_bytes(ET.tostring(suite))
    frozen = policy.freeze(
        tmp_path, parent='data/parent', policy_path='recovery-policy.json',
        continuation='data/continuation',
        qualification_request=request['request'],
        minimum_free_bytes=0)
    assert frozen['state'] == 'frozen'
    return parent


def test_recovery_policy_freezes_before_launch_and_is_idempotent_after_completion(tmp_path):
    parent = _prepared(tmp_path)
    manifest = runner.verify(parent)
    runner._begin(parent, manifest)
    task = manifest['tasks'][0]
    runner.TaskContext(parent, task['shard'], task['identity']).finish(
        dict(passed=True, scientific_decision='abstain'))
    runner._finish_study(parent, manifest)
    result = policy.resume(tmp_path, 'recovery-policy.json')
    assert result['state'] == 'complete'
    assert result['completed'] == 1
    assert policy.resume(tmp_path, 'recovery-policy.json') == result


def test_recovery_policy_rejects_changed_limits(tmp_path):
    _prepared(tmp_path)
    path = tmp_path/'recovery-policy.json'
    value = json.loads(path.read_text())
    value['max_attempts_per_task'] = 100
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='frozen task recovery policy changed'):
        policy.resume(tmp_path, 'recovery-policy.json')


def test_recovery_policy_seals_interrupted_charge_before_continuation(tmp_path,
                                                                      monkeypatch):
    parent = _prepared(tmp_path)
    manifest = runner.verify(parent)
    runner._begin(parent, manifest)
    task = manifest['tasks'][0]
    runner.TaskContext(parent, task['shard'], task['identity']).charge(
        native_calls=1, packet_visits=1)
    (parent/'worker.lock').touch()
    def checked_continuation(root, output, *, launch):
        assert launch is True
        assert output == tmp_path/'data/continuation'
        assert (output/'freeze.json').is_file()
        return dict(state='continuation_prepared')
    monkeypatch.setattr(task_resume, 'resume_campaign', checked_continuation)
    assert policy.resume(tmp_path, 'recovery-policy.json') == dict(
        state='continuation_prepared')
    assert runner.verify_completion(parent)['state'] == 'terminal'
