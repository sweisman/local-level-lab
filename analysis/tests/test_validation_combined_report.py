# SPDX-License-Identifier: AGPL-3.0-or-later
"""A recovered validation family must have one final saved outcome per fit."""
import pytest
import importlib.util
import json
import hashlib
import subprocess
import sys


def test_combined_report_uses_release_specific_native_binding():
    from types import SimpleNamespace
    from lll.studies import validation_combined_report as report
    views = [object(), object()]
    seen = []
    def qualified_binding(view):
        seen.append(view)
        return {'wide_sha256': 'release-specific'}
    policy = SimpleNamespace(native_bindings=qualified_binding)
    assert report.release_native_bindings(policy, views) == [
        {'wide_sha256': 'release-specific'},
        {'wide_sha256': 'release-specific'},
    ]
    assert seen == views


def test_final_sources_reuse_parent_and_replace_only_interrupted_work():
    assert importlib.util.find_spec('lll.studies.validation_combined_report') is not None
    from lll.studies import validation_combined_report as report
    assert hasattr(report,'final_sources')
    parent=[dict(identity='a',status='complete',passed=True),
            dict(identity='b',status='interrupted',passed=False)]
    first=[dict(identity='b',status='interrupted',passed=False)]
    second=[dict(identity='b',status='complete',passed=False),
            dict(identity='c',status='complete',passed=True)]
    assert report.final_sources(['a','b','c'],[parent,first,second])=={'a':0,'b':2,'c':2}
    with pytest.raises(ValueError,match='duplicate'):
        report.final_sources(['a'],[[parent[0]],[dict(identity='a',status='complete',passed=True)]])
    with pytest.raises(ValueError,match='missing'):
        report.final_sources(['a','b','c'],[parent,first])


def test_public_summary_keeps_recovered_validation_distinct_from_original_run():
    from lll.studies import validation_combined_report as report
    assert hasattr(report,'render')
    summary=report.render(dict(verified=True,total=4344,original_completed=3750,
        continuation_completed=594,complete_forecasts=4344,numerically_converged=4344,
        validation=dict(draws=181,failures=0,unavailable_draws=0,
                        failure_upper=0.02,passed=False)))
    assert 'original validation was interrupted' in summary.lower()
    assert 'separate continuation' in summary.lower()
    assert 'did not pass' in summary.lower()
    assert 'generated' in summary.lower()


def test_publication_seals_report_and_refuses_to_overwrite(tmp_path,monkeypatch):
    from lll.studies import validation_combined_report as report
    assert hasattr(report,'publish')
    source=dict(verified=True,total=2,original_completed=1,continuation_completed=1,
        numerically_converged=2,complete_forecasts=2,rows=[],
        validation=dict(draws=1,failures=0,unavailable_draws=0,
                        failure_upper=0.5,passed=False))
    monkeypatch.setattr(report,'inspect',lambda *args:source)
    public=tmp_path/'docs/recovered'
    receipt=report.publish(tmp_path,'data/study',public)
    saved=json.loads((public/'verified-report.json').read_text())
    assert saved==source
    assert 'report-source.py' in receipt['artifacts']
    assert 'numerical_environment' in receipt
    assert receipt['artifacts']['verified-report.json']==hashlib.sha256(
        (public/'verified-report.json').read_bytes()).hexdigest()
    assert report.verify_publication(tmp_path,public,replay=False)['verified'] is True
    assert report.verify_publication(tmp_path,public,replay=True)['replayed'] is True
    monkeypatch.setattr(report.runner,'runtime_environment',lambda:dict(python='changed'))
    with pytest.raises(ValueError,match='environment'):
        report.verify_publication(tmp_path,public,replay=True)
    (public/'results.csv').write_text('changed\n')
    with pytest.raises(ValueError,match='publication artifact'):
        report.verify_publication(tmp_path,public,replay=False)
    with pytest.raises(ValueError,match='fresh'):
        report.publish(tmp_path,'data/study',public)


def test_publication_failure_never_exposes_a_partial_public_page(tmp_path,monkeypatch):
    from lll.studies import validation_combined_report as report
    source=dict(verified=True,total=2,original_completed=1,continuation_completed=1,
        numerically_converged=2,complete_forecasts=2,rows=[],
        validation=dict(draws=1,failures=0,unavailable_draws=0,
                        failure_upper=0.5,passed=False))
    monkeypatch.setattr(report,'inspect',lambda *args:source)
    real_atomic=report.atomic;calls=[]
    def fail_second(path,data):
        calls.append(path)
        if len(calls)==2:raise OSError('simulated interrupted publication')
        return real_atomic(path,data)
    monkeypatch.setattr(report,'atomic',fail_second)
    public=tmp_path/'docs/recovered'
    with pytest.raises(OSError,match='simulated'):
        report.publish(tmp_path,'data/study',public)
    assert not public.exists()


def test_report_module_has_explicit_replay_command():
    completed=subprocess.run([sys.executable,'-m','lll.studies.validation_combined_report','--help'],
                             capture_output=True,text=True,check=False)
    assert completed.returncode==0
    assert '--campaign' in completed.stdout
    assert '--public' in completed.stdout
    assert '--verify' in completed.stdout
