# SPDX-License-Identifier: AGPL-3.0-or-later
from copy import deepcopy
import json
import pytest


def test_recovery_adapter_loads_under_the_actual_frozen_loader_name():
    import importlib.util
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'lll/ilvis0_native_prefix_repair_study.py'
    spec=importlib.util.spec_from_file_location('_ilvis0_frozen_control_adapter',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.evaluate) and callable(module.prepare)


def receipt(tmp_path):
    from lll.studies.artifacts import encoded,digest
    p=tmp_path/'regression';p.mkdir()
    source=tmp_path/'checked.py';source.write_text('checked = True\n')
    arguments=['analysis/tests/test_ilvis0_native_prefix_long.py',
        'analysis/tests/test_ilvis0_native_prefix_recovery.py',
        'analysis/tests/test_ilvis0_summary_error_controls.py::test_dense_lineage_accepts_the_actual_numerical_error_family']
    request=dict(sources={'checked.py':digest(source.read_bytes())},arguments=arguments,
        numerical_threads=1,reserved_threads=3)
    (p/'request.json').write_bytes(encoded(request))
    (p/'completion.json').write_bytes(encoded(dict(state='complete',exit_code=0,numerical_threads=0,
        request_sha256=digest(encoded(request)))))
    (p/'results.xml').write_text('<testsuites><testsuite tests="45" failures="0" errors="0" skipped="0"/></testsuites>')
    return p


def test_recovery_requires_completed_current_numerical_regression(tmp_path):
    from lll.ilvis0_native_prefix_repair_study import regression_gate
    p=receipt(tmp_path);out=regression_gate(tmp_path,'regression')
    assert out['tests']==45 and out['threads']==1 and out['reserved_threads']==3
    (tmp_path/'checked.py').write_text('changed = True\n')
    with pytest.raises(ValueError,match='source'):regression_gate(tmp_path,'regression')


@pytest.mark.parametrize('change',['failure','skipped','short','receipt','required_test','allocation'])
def test_recovery_rejects_incomplete_or_mismatched_qualification(tmp_path,change):
    from lll.ilvis0_native_prefix_repair_study import regression_gate
    from lll.studies.artifacts import encoded,digest
    p=receipt(tmp_path)
    if change in ('failure','skipped','short'):
        text=(p/'results.xml').read_text()
        for key in ('failures','skipped','tests'):
            if (change,key) in (('failure','failures'),('skipped','skipped'),('short','tests')):
                text=text.replace(key+'="'+('45' if key=='tests' else '0')+'"',key+'="1"')
        (p/'results.xml').write_text(text)
    else:
        request=json.loads((p/'request.json').read_bytes())
        if change=='required_test':request['arguments'].pop()
        if change=='allocation':request['reserved_threads']=0
        (p/'request.json').write_bytes(encoded(request))
        if change=='receipt':
            request['sources']['checked.py']='wrong'
            (p/'request.json').write_bytes(encoded(request))
        else:
            completion=json.loads((p/'completion.json').read_bytes())
            completion['request_sha256']=digest(encoded(request))
            (p/'completion.json').write_bytes(encoded(completion))
    with pytest.raises(ValueError):regression_gate(tmp_path,'regression')
