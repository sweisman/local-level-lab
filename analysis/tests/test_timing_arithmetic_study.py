# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite allowances and isolated binding before saved-point execution."""
import math
from pathlib import Path

import pytest


def test_new_allowance_covers_reconstruction_and_sixty_four_calls_only():
    from lll.timing_arithmetic_study import allowance
    from lll.prediction_calibration_study import case_recipe
    r=case_recipe(281474976810726);work=allowance(r)
    cut=2*r['queries']//3;prefix=math.ceil((r['query_start_s']+(cut-1)*r['query_step_s']+r['limits']['time_offset'])*r['rate_hz'])+2
    assert work['native_calls']==prefix+cut+64
    assert work['packet_visits']==prefix+cut+64*prefix*cut
    assert work['bound_calls']==work['bound_steps']==0


def test_binding_replaces_probe_without_patching_original_module():
    from lll.timing_arithmetic_study import bind_probe
    from lll.studies.artifacts import digest
    from lll import stopping_consistency_study as original
    raw=Path(original.__file__).read_bytes()
    def provider(*a,**k):raise RuntimeError('diagnostic provider')
    bound,proof=bind_probe(provider,raw=raw,expected_sha256=digest(raw))
    assert proof['substitutions']==1 and proof['import_name']=='probe'
    assert bound is not original.calculate_point
    assert original.calculate_point.__globals__ is not bound.__globals__
    with pytest.raises(ValueError,match='hash'):bind_probe(provider,raw=raw,expected_sha256='0'*64)


def test_guard_accepts_only_declared_framework_updates():
    from lll.timing_arithmetic_study import verify_parent,FRAMEWORK_UPDATES
    parent={'physics.py':'a'*64,**{n:'b'*64 for n in FRAMEWORK_UPDATES}}
    current=dict(parent);current.update({n:'c'*64 for n in FRAMEWORK_UPDATES})
    updates=verify_parent(parent,current)
    assert set(updates)==set(FRAMEWORK_UPDATES)
    current['physics.py']='d'*64
    with pytest.raises(ValueError,match='scientific source'):verify_parent(parent,current)


def test_real_adapter_rejects_scope_before_any_input_or_native_access(tmp_path):
    import importlib.util
    from types import SimpleNamespace
    import lll.timing_arithmetic_study as original
    spec=importlib.util.spec_from_file_location('_frozen_test_adapter',original.__file__)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with pytest.raises(ValueError,match='scope'):
        module.evaluate({},SimpleNamespace(manifest={'scope':'unapproved'},root=tmp_path))


def test_full_configuration_freezes_new_budget_and_four_threads():
    from lll.timing_arithmetic_study import configuration,allowance
    from lll.prediction_calibration_study import case_recipe
    config=configuration('coordinate-full');r=case_recipe(281474976810726)
    assert config['workers']==4 and config['threads']==1 and config['maximum_evaluations']==171
    assert config['id']=='saved-point-coordinate-precision-20261026'
    assert allowance(r,maximum_evaluations=171)==dict(native_calls=23805,packet_visits=318228129,bound_calls=0,bound_steps=0)
    assert configuration('timing')['maximum_evaluations']==64
    with pytest.raises(ValueError):configuration('extra')


def test_coordinate_parent_gate_requires_the_complete_matrix():
    from lll.timing_arithmetic_study import verify_coordinate_gate
    rows=[dict(mode='compensated',precision_passed=True) for _ in range(6)]
    valid=dict(complete=18,selected=18,failures=[],candidate_qualified=True,rows=rows)
    verify_coordinate_gate(valid)
    for change in ({'complete':6},{'failures':[{'reason':'failed'}]},{'candidate_qualified':False}):
        with pytest.raises(ValueError):verify_coordinate_gate(dict(valid,**change))


def test_coordinate_kernel_binding_rejects_source_or_environment_changes():
    from lll.timing_arithmetic_study import verify_coordinate_binding
    binding=dict(sources={'kernel.py':'a'*64},environment={'compiler':'same'})
    verify_coordinate_binding(binding,{'kernel.py':'a'*64},{'compiler':'same'})
    with pytest.raises(ValueError):verify_coordinate_binding(binding,{'kernel.py':'b'*64},{'compiler':'same'})
    with pytest.raises(ValueError):verify_coordinate_binding(binding,{'kernel.py':'a'*64},{'compiler':'changed'})
