# SPDX-License-Identifier: AGPL-3.0-or-later
from fractions import Fraction as F

import pytest
from lll import ilvis0_receiver_scale as receiver


def fixes(n=16):
    return [dict(time_s=100.+i,latitude_rad=.5+i*.00001,longitude_rad=-.4+i*.00002,
                 height_m=1000.+i*.1) for i in range(n)]


def test_chart_is_fixed_exact_and_rejects_future_rows():
    rows=fixes();chart=receiver.training_chart(rows,expected_epochs=16)
    assert chart['values'][0][0]==F(rows[0]['latitude_rad'])*6371000
    assert chart['values'][0][1]==F(rows[0]['longitude_rad'])*3185500
    with pytest.raises(ValueError):receiver.training_chart(rows+fixes(1),expected_epochs=16)
    assert chart==receiver.training_chart(rows,expected_epochs=16)


def test_nonuniform_or_invalid_positions_cannot_be_repaired():
    rows=fixes();rows[3]['time_s']+=.1
    with pytest.raises(ValueError,match='uniform'):receiver.training_chart(rows,expected_epochs=16)
    rows=fixes();rows[3]['latitude_rad']=float('nan')
    with pytest.raises(ValueError):receiver.training_chart(rows,expected_epochs=16)


def test_assessment_keeps_all_axes_and_reference_columns_without_model_inputs():
    chart=receiver.training_chart(fixes(),expected_epochs=16)
    result=receiver.assess(chart,degree=3,tau=10,maximum_seconds=5)
    assert result['observations']==48 and result['reference_columns']==12 and result['degrees']==36
    assert len(result['axes'])==3 and result['scale_upper']>=0
    assert result['scientific_decision']=='abstain' and not result['observational_coverage_qualified']
    assert result['future_receiver_positions_used'] is False and result['earth_model_residuals_used'] is False
    assert result['maximum_epochs']==48
    with pytest.raises(ValueError):receiver.assess(chart,degree=4,tau=10)


def test_bad_reference_does_not_create_negative_quadratic_and_hex_is_exact():
    value=F(2**15000,3**9000)
    encoded=receiver.rational_record(value)
    assert F(int(encoded['numerator_hex'],16),int(encoded['denominator_hex'],16))==value
