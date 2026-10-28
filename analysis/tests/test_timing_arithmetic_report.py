# SPDX-License-Identifier: AGPL-3.0-or-later
"""A completed diagnostic does not turn derivative disagreements into passes."""
import pytest


def test_summary_preserves_failed_derivatives_and_original_fit_label():
    from lll.timing_arithmetic_report import summarize
    value=dict(mode='both',evaluations=13,cost=2.,jacobian=[[1.,2.]],
        derivatives=[dict(parameter='time_offset',steps=[dict(step=1e-4,stencil='forward',
            error_norm=1e-3,comparison_scale=1e-6,analytic_norm=2.,difference_norm=2.)])])
    row,curves=summarize('point',False,value,baseline=value)
    assert row['original_fit_converged'] is False and row['derivatives_agree'] is False
    assert curves[0]['error_ratio']==pytest.approx(1000.)
    assert row['fit_labels_changed'] is False


def test_summary_rejects_missing_comparison_scale():
    from lll.timing_arithmetic_report import summarize
    value=dict(mode='baseline',evaluations=13,cost=2.,jacobian=[[1.]],
        derivatives=[dict(parameter='time_offset',steps=[dict(step=1e-4,stencil='forward',
            error_norm=0.,comparison_scale=0.,analytic_norm=0.,difference_norm=0.)])])
    with pytest.raises(ValueError,match='comparison scale'):summarize('p',True,value,baseline=value)


def test_inspection_does_not_import_numerical_libraries():
    import subprocess
    import sys
    source='''
import sys
from types import SimpleNamespace
from lll.studies import closed
class Fake:
    manifest={'scope':'wrong'}
    def __init__(self,*a):pass
    def close(self):pass
closed.ClosedStudy=Fake
from lll.timing_arithmetic_report import inspect
try:inspect('.', 'not-an-input')
except ValueError:pass
assert 'numpy' not in sys.modules
assert 'scipy' not in sys.modules
'''
    subprocess.run([sys.executable,'-c',source],check=True)


def test_full_summary_keeps_a_new_stopping_pass_separate_from_original_failure():
    from lll.timing_arithmetic_report import summarize_full
    record=dict(identity='point',saved_converged=False)
    d=dict(columns=1,evaluations=11,cost=2.,baseline={'cost':2.},repeatability={'exact':True},
        stopping_probe=dict(passed=True,actual_cost_change=0.),signed_probe=None,
        active_parameters=['gyro_bias_z'],derivatives=[dict(column=0,steps=[dict(step=1e-4,
            error_norm=1e-3,analytic_norm=1.,difference_norm=1.,stencil='centered')])])
    row,curves=summarize_full(record,d)
    assert row['original_fit_converged'] is False
    assert row['candidate_stopping_passed'] is True
    assert row['derivatives_agree'] is False and row['fit_labels_changed'] is False
    assert curves[0]['parameter']=='gyro_bias_z' and curves[0]['error_ratio']>1
