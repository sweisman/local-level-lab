"""A missing candidate abstains; shape is tested before the field."""

from lll.esa_rolling_origin_400_model_matrix_report import compare


def _rows(*, missing=None, flat_error=30., rotating_error=1., still_error=10.):
    values = dict(sphere_rotating=rotating_error,
                  sphere_still=still_error, flat_still=flat_error)
    result = []
    for model, error in values.items():
        for start in (0, 1):
            result.append(dict(identity=f'{model}-0-increment-{start}',
                model=model, profile=False, law='increment', start=start,
                fit_known=(model != missing), converged=(model != missing),
                training_cost=float(start), forecast_complete=(model != missing),
                prediction_total_rms_m=error+start,
                training_accuracy=True, prediction_accuracy=True))
    return result


def test_model_matrix_report_preserves_missing_primary():
    result = compare(_rows(missing='flat_still'),
                     profile=False, law='increment')
    assert result['complete'] is False
    assert result['shape_lower_error_family'] is None
    assert result['field_lower_error_model'] is None


def test_model_matrix_report_orders_shape_before_field():
    globe = compare(_rows(), profile=False, law='increment')
    assert globe['complete'] is True
    assert globe['shape_lower_error_family'] == 'globe'
    assert globe['preferred_model'] == 'sphere_rotating'
    assert globe['field_lower_error_model'] == 'specified_field'
    flat = compare(_rows(flat_error=.5), profile=False, law='increment')
    assert flat['shape_lower_error_family'] == 'flat'
    assert flat['field_lower_error_model'] is None
