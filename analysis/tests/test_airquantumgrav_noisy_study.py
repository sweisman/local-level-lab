# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest
from unittest.mock import patch


def test_noisy_study_defines_fresh_finite_24_case_scope_without_observed_inputs():
    from lll.airquantumgrav_noisy_study import recipe,tasks,construction_limits
    r=recipe();matrix=tasks();limits=construction_limits(r)
    assert len(matrix)==24 and len({v['identity'] for v in matrix})==24
    assert (r['workers'],r['threads'],r['maximum_wall_s'])==(4,1,28800.)
    assert sum(v['limits']['native_calls'] for v in matrix)==4824
    assert sum(v['limits']['packet_visits'] for v in matrix)==931411200000
    assert limits==dict(constructed_intervals=360000,generated_samples=362001,noise_normal_variates=6484812)
    assert r['accuracy_limits']==dict(horizontal_rms_m=10.,vertical_rms_m=30.,maximum_horizontal_m=50.,maximum_absolute_up_m=150.)
    assert not any(r[k] for k in ('original_reads','observed_starts','protected_reads','retries'))


def test_noisy_study_requires_qualification_before_creating_inputs(tmp_path):
    from lll.airquantumgrav_noisy_study import prepare
    with pytest.raises(ValueError,match='qualification'):prepare(tmp_path,qualification=None)
    assert not (tmp_path/'data').exists()


def test_noisy_study_requires_guarded_thread_environment_before_parent_or_inputs(tmp_path):
    from lll import airquantumgrav_noisy_study as module
    with patch.object(module,'environment',return_value=dict(numerical_environment={})):
        with pytest.raises(ValueError,match='thread environment'):module.prepare(tmp_path,qualification='missing')
    assert not (tmp_path/'data').exists()


def test_noisy_report_rejects_open_study_before_numerical_imports(tmp_path):
    from lll.airquantumgrav_noisy_report import inspect
    with pytest.raises(ValueError,match='closed study'):inspect(tmp_path)


def test_noisy_report_render_distinguishes_generated_robustness_from_archive_confidence():
    from lll.airquantumgrav_noisy_report import render
    text=render(dict(total=24,complete=0,numerically_converged=0,accurate=0,rows=[],elapsed_s=1.,charged=dict(native_calls=0)))
    for phrase in ('generated','not measured instrument','not calibrated confidence','no observed','Seven confirmation'):
        assert phrase.lower() in text.lower()
