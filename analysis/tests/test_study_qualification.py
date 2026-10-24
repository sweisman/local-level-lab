# SPDX-License-Identifier: AGPL-3.0-or-later
"""Small metadata-only tests for binding a passing suite to tested source."""
import importlib
import xml.etree.ElementTree as ET

import pytest


def library():return importlib.import_module('lll.studies.qualification')


def fixture(tmp_path):
    source=tmp_path/'analysis/lll/example.py';source.parent.mkdir(parents=True);source.write_text('VALUE=1\n')
    return dict(root=tmp_path,sources=['analysis/lll/example.py'],environment=dict(python='test',numpy='test'),
        output='data/request.json',report='data/report.xml')


def report(path,*,names=('test_pipeline','test_inputs'),child=None,suite_failures=0):
    root=ET.Element('testsuites');suite=ET.SubElement(root,'testsuite',tests=str(len(names)),
        errors='0',failures=str(suite_failures),skipped='0')
    for i,name in enumerate(names):
        case=ET.SubElement(suite,'testcase',name=name,classname='checks')
        if i==0 and child:ET.SubElement(case,child)
    path.write_bytes(ET.tostring(root))


def test_request_then_check_preserves_exact_source_and_report_bytes(tmp_path):
    q=fixture(tmp_path);library().request(**q)
    report(tmp_path/q['report'])
    raw,xml=library().checked(tmp_path,q['output'],sources=q['sources'],environment=q['environment'],
        required_tests=['test_pipeline'],minimum_tests=2)
    assert raw==(tmp_path/q['output']).read_bytes() and xml==(tmp_path/q['report']).read_bytes()


@pytest.mark.parametrize('fault',['source','environment','failed','skipped','missing','too_few','duplicate','suite_failure','truncated'])
def test_check_rejects_stale_or_incomplete_qualification(tmp_path,fault):
    q=fixture(tmp_path);library().request(**q);path=tmp_path/q['report'];report(path)
    if fault=='source':(tmp_path/q['sources'][0]).write_text('VALUE=2\n')
    elif fault=='environment':q['environment']['python']='changed'
    elif fault=='failed':report(path,child='failure')
    elif fault=='skipped':report(path,child='skipped')
    elif fault=='missing':report(path,names=('test_other','test_inputs'))
    elif fault=='too_few':report(path,names=('test_pipeline',))
    elif fault=='duplicate':report(path,names=('test_pipeline','test_pipeline'))
    elif fault=='suite_failure':report(path,suite_failures=1)
    else:path.write_text('<testsuites>')
    with pytest.raises(ValueError):library().checked(tmp_path,q['output'],sources=q['sources'],
        environment=q['environment'],required_tests=['test_pipeline'],minimum_tests=2)


def test_request_cannot_be_written_after_its_test_report(tmp_path):
    q=fixture(tmp_path);path=tmp_path/q['report'];path.parent.mkdir();report(path)
    with pytest.raises(ValueError):library().request(**q)
    assert not (tmp_path/q['output']).exists()


def test_request_cannot_replace_an_existing_request(tmp_path):
    q=fixture(tmp_path);library().request(**q)
    before=(tmp_path/q['output']).read_bytes()
    with pytest.raises(ValueError):library().request(**q)
    assert (tmp_path/q['output']).read_bytes()==before


@pytest.mark.parametrize('sources',[[],['../outside'],['/absolute'],['analysis/lll/example.py']*2])
def test_request_requires_explicit_safe_unique_sources(tmp_path,sources):
    q=fixture(tmp_path);q['sources']=sources
    with pytest.raises(ValueError):library().request(**q)
    assert not (tmp_path/q['output']).exists()
