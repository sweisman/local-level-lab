"""Saved-only error-structure description of the twenty-group forecasts."""

import math

import pytest

from lll import ilvis0_remaining_error_structure as audit


def _epoch(index, role, north, east=0., up=0.):
    return dict(epoch=index, role=role, time_s=float(index),
                north_direct_error_m=north, east_direct_error_m=east,
                up_direct_error_m=up)


def test_prediction_trend_and_serial_correlation_use_only_later_epochs():
    rows=[_epoch(0,'training',1000.),_epoch(1,'training',1000.)]
    rows += [_epoch(2,'prediction',1.),_epoch(3,'prediction',2.),
             _epoch(4,'prediction',3.),_epoch(5,'prediction',4.)]
    result=audit.describe_epochs(rows)
    north=result['axes']['north']
    assert result['training_epochs']==2
    assert result['prediction_epochs']==4
    assert north['mean_m']==2.5
    assert north['rms_m']==pytest.approx(math.sqrt(7.5))
    assert north['slope_m_per_min']==60.
    assert north['lag1_correlation']==pytest.approx(1.)
    assert north['final_m']==4.
    assert result['axes']['east']['lag1_correlation'] is None


def test_epoch_audit_rejects_missing_or_shuffled_predictions():
    with pytest.raises(ValueError):
        audit.describe_epochs([_epoch(0,'training',0.)])
    with pytest.raises(ValueError):
        audit.describe_epochs([_epoch(0,'prediction',0.),
                               _epoch(1,'training',0.),
                               _epoch(2,'prediction',0.)])
    with pytest.raises(ValueError):
        audit.describe_epochs([_epoch(0,'training',0.),
                               _epoch(1,'prediction',float('nan'))])
    with pytest.raises(ValueError):
        audit.describe_epochs([_epoch(0,'training',0.),
                               _epoch(1,'prediction',0.),
                               _epoch(1,'prediction',0.)])


def test_group_accounting_preserves_all_twenty_and_nine_scored():
    rows=[dict(segment_id=f'segment-{i}',
               outer_identity=f'fit-{i}' if i<9 else None)
          for i in range(20)]
    epochs={f'fit-{i}':[_epoch(0,'training',0.),
                       _epoch(1,'prediction',float(i)),
                       _epoch(2,'prediction',float(i+1))]
            for i in range(9)}
    result=audit.describe_groups(rows,lambda identity:epochs[identity])
    assert result['groups']==20
    assert result['scored_groups']==9
    assert result['unscored_groups']==11
    assert len(result['rows'])==20
    assert result['rows'][-1]['error_structure'] is None


def test_public_report_labels_near_unit_correlation_as_descriptive():
    rows=[dict(segment_id=f'segment-{i}',
               outer_identity=f'fit-{i}' if i<9 else None)
          for i in range(20)]
    epochs={f'fit-{i}':[_epoch(0,'training',0.),
                       _epoch(1,'prediction',1.,2.,3.),
                       _epoch(2,'prediction',2.,3.,4.),
                       _epoch(3,'prediction',3.,4.,5.),
                       _epoch(4,'prediction',4.,5.,6.)]
            for i in range(9)}
    report=audit.describe_groups(rows,lambda identity:epochs[identity])
    text=audit.render(report)
    assert 'Median adjacent-epoch correlation' in text
    assert '1.0000' in text
    assert 'do not measure a stationary noise process' in text

