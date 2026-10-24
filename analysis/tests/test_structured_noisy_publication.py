# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest


def report():
    rows=[]
    for i,converged in enumerate((True,False)):
        rows.append(dict(identity=f'case-{i}',law='increment' if i==0 else 'point',model='sphere_rotating',
            profile=bool(i),start=0,complete=True,converged=converged,accurate=True,
            prediction=dict(horizontal_rms_m=1.8+i*.2,vertical_rms_m=.2),
            conditional_prediction=dict(horizontal_rms_m=1.81+i*.2,vertical_rms_m=.21,accuracy=dict(passed=True)),
            linear_calibration_status='active_bounds_unsupported',normalized_parameters={'gyro_gain_x':1.}))
    return dict(verified=True,total=2,complete=2,numerically_converged=1,raw_accuracy=2,conditional_accuracy=2,
        rows=rows,qualified=False,elapsed_s=120.,attempted_native_calls=10,
        prepaid=dict(native_calls=20,packet_visits=100),confidence_calibrated=False)


def test_render_separates_accuracy_numerical_failure_and_calibration_limits():
    from lll.structured_noisy_publication import render
    text=render(report())
    assert '2/2' in text and '1/2' in text
    assert 'case-0' in text and 'case-1' in text
    assert 'boundary' in text and 'not qualified' in text
    assert 'not Earth-model votes' in text


def test_render_refuses_an_unverified_result():
    from lll.structured_noisy_publication import render
    data=report();data['verified']=False
    with pytest.raises(ValueError):render(data)


def test_result_csv_preserves_both_starts_and_the_failed_case():
    import csv,io
    from lll.structured_noisy_publication import result_csv
    rows=list(csv.DictReader(io.StringIO(result_csv(report()))))
    assert len(rows)==2 and [r['identity'] for r in rows]==['case-0','case-1']
    assert rows[0]['numerical_pass']=='True' and rows[1]['numerical_pass']=='False'
    assert rows[1]['linear_calibration_status']=='active_bounds_unsupported'


def test_render_rejects_inconsistent_summary_counts():
    from lll.structured_noisy_publication import render
    data=report();data['numerically_converged']=2
    with pytest.raises(ValueError):render(data)
