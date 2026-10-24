# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path
from unittest.mock import patch

import pytest


def test_error_structure_standalone_definition_has_finite_zero_native_scope():
    path=Path('analysis/lll/airquantumgrav_error_structure.py')
    spec=importlib.util.spec_from_file_location('_saved_error_worker',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    r=module.recipe();tasks=module.tasks()
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(1,1,300.)
    assert r['maximum_saved_records']==24 and r['maximum_saved_error_epochs']==28800
    assert len(tasks)==1 and not any(tasks[0]['limits'].values())
    assert tasks[0]['input_key']=='curves'
    assert module.work_limits(r)['correlation_pairs']==24*34698


def test_error_structure_requires_qualification_before_parent_or_inputs(tmp_path):
    from lll.airquantumgrav_error_structure import prepare
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_error_structure_rejects_unguarded_environment_before_parent(tmp_path):
    from lll import airquantumgrav_error_structure as module
    with patch.object(module,'environment',return_value=dict(numerical_environment={})):
        with pytest.raises(ValueError,match='thread environment'):module.prepare(tmp_path,qualification='missing')
    assert not (tmp_path/'data').exists()


def test_error_structure_rejects_open_parent_before_numerical_imports(tmp_path):
    from lll.airquantumgrav_error_structure import parent_report
    with pytest.raises(ValueError,match='closed study'):parent_report(tmp_path)


def test_error_structure_requires_exact_verified_development_parent():
    from lll.airquantumgrav_error_structure import require_parent
    good=dict(verified=True,total=24,expected_primaries=12,complete_predictions=22,numerically_converged=22,
        original_reads=0,protected_reads=0,native_calls_during_audit=0,
        source=dict(source_references=dict(imu=dict(filename='187_rqh01.txt'))))
    require_parent(good)
    for change in (dict(verified=False),dict(total=23),dict(complete_predictions=24),dict(original_reads=1),
            dict(protected_reads=1),dict(source=dict(source_references=dict(imu=dict(filename='other.txt'))))):
        with pytest.raises(ValueError):require_parent(dict(good,**change))


def test_error_structure_preparation_keeps_study_identity_separate_from_curve_identity(tmp_path):
    from types import SimpleNamespace
    from lll import airquantumgrav_error_structure as module
    from lll.studies.artifacts import encoded
    curve_id='last-parent-curve'
    parent=SimpleNamespace(completion=dict(manifest_sha256='b'*64),read=lambda *args,**kwargs:encoded({}) if kwargs.get('raw') else {},
        artifact=lambda *args:{},envelope=lambda *args:dict(artifacts={'artifacts/'+curve_id+'/scores.json':'a'*64}),close=lambda:None)
    report=dict(rows=[dict(identity=curve_id,complete=True)])
    captured=[]
    def definition(value,root):
        captured.append(value)
        return SimpleNamespace(prepare=lambda root:dict(allocation=dict(workers=1,threads=1)))
    from lll.compute_budget import environment
    with patch.object(module,'environment',return_value=dict(numerical_environment=environment(workers=1,threads=1))), \
            patch.object(module,'qualification_sources',return_value=['explicit-source.py']), \
            patch('lll.studies.qualification.checked',return_value=(b'{}',b'<testsuites/>')), \
            patch.object(module,'parent_report',return_value=(parent,report)), \
            patch.object(module,'validate_inputs'),patch('lll.studies.runtime.Definition.from_dict',side_effect=definition):
        result=module.prepare(tmp_path,qualification='qualified',identity='new-diagnostic')
    assert captured[0]['id']=='new-diagnostic' and result['path']=='data/new-diagnostic'
