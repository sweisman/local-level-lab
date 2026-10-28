# SPDX-License-Identifier: AGPL-3.0-or-later
import copy
from pathlib import Path

import pytest


def test_boundary_study_has_four_exact_exposed_points_and_separate_caps():
    from lll.timing_boundary_study import configuration,identities,work_allowance
    ids=identities();cfg=configuration()
    assert len(ids)==len(set(ids))==4
    assert all('-point-sphere_rotating-1-' in name for name in ids)
    assert {name.split('-')[2] for name in ids}=={'281474977010692','281474977010693'}
    assert cfg['workers']==4 and cfg['threads']==1 and cfg['maximum_wall_s']==3600.
    assert cfg['maximum_evaluations']==64 and cfg['nonlinear_fit_starts']==0
    assert work_allowance(281474977010693)==dict(native_calls=23698,packet_visits=119117714,
                                               bound_calls=0,bound_steps=0)
    with pytest.raises(ValueError):work_allowance(281474977010694)


def test_saved_point_encoding_changes_no_value_or_original_record():
    from lll.timing_boundary_study import canonical_fit
    names=['p'+str(i) for i in range(27)];values=[i/100 for i in range(27)]
    fit=dict(active_parameters=names,normalized_parameters=dict(zip(names,values)),
        local_linearization=dict(normalized_parameters=values),converged=False)
    original=copy.deepcopy(fit);encoded=canonical_fit(fit)
    assert fit==original and encoded['normalized_parameters']==values
    assert encoded['converged'] is False
    fit['local_linearization']['normalized_parameters'][0]=.5
    with pytest.raises(ValueError):canonical_fit(fit)


def test_boundary_capture_binding_replaces_only_probe_and_never_patches_original():
    from lll.timing_boundary_study import bind_capture
    from lll import stopping_consistency_study as old
    from lll.studies.artifacts import digest
    raw=Path(old.__file__).read_bytes()
    bound,proof=bind_capture(lambda *a,**k:None,raw=raw,expected_sha256=digest(raw))
    assert proof['substitutions']==1 and proof['import_name']=='probe'
    assert bound is not old.calculate_point and bound.__globals__ is not old.calculate_point.__globals__
    with pytest.raises(ValueError):bind_capture(None,raw=raw,expected_sha256='0'*64)


def test_boundary_preparation_requires_qualification_before_reading_data(tmp_path):
    from lll.timing_boundary_study import prepare
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_boundary_worker_rejects_unapproved_scope_before_native_or_input_access():
    from types import SimpleNamespace
    from lll.timing_boundary_study import evaluate
    with pytest.raises(ValueError,match='scope'):
        evaluate({},SimpleNamespace(manifest=dict(scope='unapproved')))


def test_boundary_parent_sources_cannot_change_scientific_equations():
    from lll.timing_boundary_study import parent_changes
    parent={'physics.py':'a'*64,'analysis/lll/prediction_calibration_report.py':'b'*64}
    current=dict(parent);current['analysis/lll/prediction_calibration_report.py']='c'*64
    assert list(parent_changes(parent,current))==['analysis/lll/prediction_calibration_report.py']
    current['physics.py']='d'*64
    with pytest.raises(ValueError):parent_changes(parent,current)
