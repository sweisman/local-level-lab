# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util


def test_report_distinguishes_prediction_accuracy_from_numerical_qualification():
    name='lll.ilvis0_forecast_report'
    assert importlib.util.find_spec(name) is not None, 'saved forecast report missing'
    module=__import__(name,fromlist=['render'])
    report=dict(total=24,passing=0,converged=0,native_calls=4320,complete=False,
        rows=[dict(model='sphere_rotating',profile=False,clock='header_elapsed',start=0,
            passed=False,converged=False,prediction=dict(rms_neu_m=[1e-6,1e-7,1e-8]),
            reason='fresh_position_probe_not_stable')],pairs=[],
        original_reads=0,observed_starts=0)
    text=module.render(report)
    assert '0/24' in text and '0/1' in text
    assert 'Small forecast errors do not qualify a failed stopping check.' in text
    assert 'No aircraft observations' in text
    assert 'did not qualify' in text


def test_linear_diagnosis_retains_columns_and_charges_both_solves():
    from lll.ilvis0_forecast_report import linear_corrections
    charges=[]
    report=linear_corrections([-0.4,-0.8],[[1.,1.],[2.,2.]],[0.,0.],
        reserve=lambda:charges.append(1))
    assert charges==[1,1]
    assert report['columns']==2 and report['minimum_norm_rank']==1
    assert report['minimum_norm_inside_bounds']
    assert max(abs(v-.2) for v in report['minimum_norm_step'])<1e-12
    assert report['native_calls']==0
