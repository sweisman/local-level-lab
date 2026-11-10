# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind local software qualification to explicit source and environment bytes.

This checks trusted local test evidence, not scientific adequacy or statistical
coverage. It imports no numerical library and never launches a calculation.
"""
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from .artifacts import atomic,digest,encoded,safe_path

VERSION='study-software-qualification-v1'


def _sources(root,names):
    names=list(names)
    if (not names or any(not isinstance(n,str) for n in names) or len(set(names))!=len(names)):
        raise ValueError('explicit nonempty unique source paths required')
    return {n:digest(safe_path(root,n).read_bytes()) for n in sorted(names)}


def request(root,*,sources,environment,output,report):
    """Write a source/environment binding before the named test report exists."""
    root=Path(root).resolve();target=safe_path(root,output);test_report=safe_path(root,report)
    if target.exists() or test_report.exists() or target==test_report:
        raise ValueError('fresh request and future report paths required')
    if not isinstance(environment,dict) or not environment:raise ValueError('explicit environment required')
    value=dict(version=VERSION,sources=_sources(root,sources),environment=environment,report=report)
    atomic(target,encoded(value))
    return dict(request=output,report=report,sources=len(value['sources']))


def checked(root,request_path,*,sources,environment,required_tests,minimum_tests):
    """Return exact request/report bytes only for a matching passing suite."""
    root=Path(root).resolve();raw=safe_path(root,request_path).read_bytes();value=json.loads(raw)
    if (value.get('version')!=VERSION or value.get('sources')!=_sources(root,sources)
            or value.get('environment')!=environment):
        raise ValueError('software qualification source or environment changed')
    if (type(minimum_tests) is not int or minimum_tests<1 or not required_tests
            or any(not isinstance(n,str) or not n for n in required_tests)):
        raise ValueError('explicit required tests and positive minimum case count required')
    report=safe_path(root,value['report']).read_bytes()
    try:
        tree=ET.fromstring(report);cases=list(tree.iter('testcase'));suites=list(tree.iter('testsuite'))
        names=[c.attrib['name'] for c in cases]
        identities=[(c.attrib.get('classname',''),c.attrib['name']) for c in cases]
        failed=(any(n.tag in ('failure','error','skipped') for c in cases for n in c.iter())
            or any(int(s.attrib.get(k,0)) for s in suites for k in ('errors','failures','skipped')))
    except (ET.ParseError,KeyError,ValueError,TypeError) as error:
        raise ValueError('well-formed complete local test report required') from error
    if (not suites or failed or len(cases)<minimum_tests or len(set(identities))!=len(cases)
            or any(not n for n in names) or not set(required_tests)<=set(names)):
        raise ValueError('complete passing required software tests required')
    return raw,report
