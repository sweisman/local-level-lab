"""Ground control selection is independent of the receiver position errors."""

import pytest


def rows(n=30):
    return [dict(sequence=i,time_s=i*.5,latitude_deg=55.,longitude_deg=0.,height_m=100.,
                 north_mps=0.,east_mps=0.,up_mps=0.,
                 position_variance_m2=[.01,.04,.09]) for i in range(n)]


def test_longest_velocity_only_run_breaks_tie_earliest():
    from lll.esa_ground_receiver_control import select_run
    data=rows()
    for i in (0,1,2,9,10,11,12,19,20,21,22,23,24,25,26,27,28,29):
        data[i]['east_mps']=2.
    assert select_run(data,min_reports=5)==(3,9)
    for i in range(13,19):data[i]['latitude_deg']+=1.
    assert select_run(data,min_reports=5)==(3,9)


def test_no_qualifying_ground_run_is_rejected():
    from lll.esa_ground_receiver_control import select_run
    data=rows()
    for row in data[15:]:row['time_s']+=2.
    with pytest.raises(ValueError,match='ground run'):
        select_run(data,min_reports=20)


def test_position_scatter_uses_metre_chart_and_reports_no_coverage():
    from lll.esa_ground_receiver_control import position_stability
    data=rows(240)
    data[0]['latitude_deg']+=1e-5
    result=position_stability(data,block_reports=120)
    assert 0.05<result['relative_rms_neu_m'][0]<0.15
    assert result['relative_rms_neu_m'][1:]==[0.,0.]
    assert result['reported_sd_median_neu_m']==[.1,.2,.3]
    assert result['empirical_coverage_calibrated'] is False
