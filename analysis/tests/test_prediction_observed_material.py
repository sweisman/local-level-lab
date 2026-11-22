"""Saved-input boundary for the observed two-law development check."""

import numpy as np
import pytest

from lll.studies.artifacts import digest, encoded


def _inputs():
    arrays = {
        'theta': np.arange(18, dtype=float).reshape(6, 3) * 1e-7,
        'dv': np.arange(18, dtype=float).reshape(6, 3) * 1e-5,
        'dt': np.full(6, .5),
    }
    layout = dict(times_s=[.5, 1., 1.5, 2.], training_epochs=2,
                  prediction_epochs=2, training_prefix_packets=2,
                  time_origin_gps_sow_s=100.)
    training = [dict(time_s=100.5, latitude_deg=1., longitude_deg=2., height_m=3.),
                dict(time_s=101., latitude_deg=1.01, longitude_deg=2.01, height_m=3.)]
    hashes = {key: digest(value.astype('<f8').tobytes())
              for key, value in arrays.items()}
    hashes.update(layout=digest(encoded(layout)),
                  training_rows=digest(encoded(training)))
    return arrays, layout, training, hashes


def test_observed_material_binds_complete_imu_and_earlier_receiver_only():
    from lll.prediction_observed_material import bind
    arrays, layout, training, hashes = _inputs()
    material = bind(arrays=arrays, layout=layout, training_rows=training,
                    frozen_hashes=hashes, source_id='development-187',
                    maximum_interval_s=.5, time_offset_bound_s=0.)
    assert len(material['dt']) == 6
    assert len(material['times']) == 4
    assert material['training_epochs'] == 2
    assert material['time_origin_s'] == 100.
    assert material['binding']['measured_raw_array_sha256'] == {
        key: hashes[key] for key in ('theta', 'dv', 'dt')}
    assert material['binding']['training_receiver_sha256'] == hashes['training_rows']
    assert 'scoring_rows' not in material
    assert 'later_receiver' not in material


def test_observed_material_rejects_changed_imu_split_or_training_rows():
    from lll.prediction_observed_material import bind
    arrays, layout, training, hashes = _inputs()
    kwargs = dict(arrays=arrays, layout=layout, training_rows=training,
                  frozen_hashes=hashes, source_id='development-187',
                  maximum_interval_s=.5, time_offset_bound_s=0.)
    changed = dict(arrays, theta=arrays['theta'].copy())
    changed['theta'][3, 0] += 1e-6
    with pytest.raises(ValueError, match='hash'):
        bind(**dict(kwargs, arrays=changed))
    wrong_layout = dict(layout, training_prefix_packets=3)
    wrong_hashes = dict(hashes, layout=digest(encoded(wrong_layout)))
    with pytest.raises(ValueError, match='split'):
        bind(**dict(kwargs, layout=wrong_layout, frozen_hashes=wrong_hashes))
    altered = [dict(row) for row in training]
    altered[0]['height_m'] += 1.
    with pytest.raises(ValueError, match='hash'):
        bind(**dict(kwargs, training_rows=altered))
    shifted = [dict(row) for row in training]
    shifted[1]['time_s'] += .001
    shifted_hashes = dict(hashes, training_rows=digest(encoded(shifted)))
    with pytest.raises(ValueError, match='timestamps'):
        bind(**dict(kwargs, training_rows=shifted,
                    frozen_hashes=shifted_hashes))
    rounded_layout = dict(layout, times_s=[.1, 1., 1.5, 2.])
    rounded_rows = [dict(row) for row in training]
    rounded_rows[0]['time_s'] = 100.1
    rounded_hashes = dict(hashes, layout=digest(encoded(rounded_layout)),
                          training_rows=digest(encoded(rounded_rows)))
    with pytest.raises(ValueError, match='timestamps'):
        bind(**dict(kwargs, layout=rounded_layout,
                    training_rows=rounded_rows,
                    frozen_hashes=rounded_hashes))


def test_observed_material_rejects_scoring_fields_at_its_input_boundary():
    from lll.prediction_observed_material import bind
    arrays, layout, training, hashes = _inputs()
    with pytest.raises(ValueError, match='input fields'):
        bind(arrays=dict(arrays, later_receiver=[1]), layout=layout,
             training_rows=training, frozen_hashes=hashes,
             source_id='development-187', maximum_interval_s=.5,
             time_offset_bound_s=0.)
