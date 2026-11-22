"""Matched fixed-law forecasts on saved development inputs."""

import numpy as np

from test_native_structured_training import training_kernels

from lll.studies.artifacts import digest, encoded


def test_observed_native_opens_later_receiver_only_after_both_unions(training_kernels):
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_observed_material import bind
    from lll.prediction_observed_native import calculate
    from lll.prediction_paired_law_study import recipe

    r = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
             query_start_s=.1, query_step_s=.2,
             maximum_evaluations=8, calibration_alpha=.0125,
             simultaneous_alpha=.025)
    spec = dict(model='sphere_rotating', latitude_deg=55.,
                profile=False, start=0, policy_id='reported-short-v1')
    generated = construct(
        spec, dict(r, noise=r['noise_by_law']['increment'],
                   sensor_case='interior'), reserve=lambda **work: None)
    origin = 100.
    training = [dict(row, time_s=row['time_s'] + origin)
                for row in generated['training_rows']]
    query_times = np.array([float(t + origin) - origin
                            for t in generated['times']])
    arrays = {name: generated[name] for name in ('theta', 'dv', 'dt')}
    cut = generated['training_epochs']
    prefix = int(np.searchsorted(np.cumsum(arrays['dt']),
                                 query_times[cut - 1]
                                 + r['limits']['time_offset'],
                                 side='left')) + 1
    layout = dict(times_s=query_times.tolist(), training_epochs=cut,
                  prediction_epochs=len(query_times) - cut,
                  training_prefix_packets=prefix,
                  time_origin_gps_sow_s=origin)
    hashes = {name: digest(np.asarray(value, dtype='<f8').tobytes())
              for name, value in arrays.items()}
    hashes.update(layout=digest(encoded(layout)),
                  training_rows=digest(encoded(training)))
    material = bind(arrays=arrays, layout=layout, training_rows=training,
                    frozen_hashes=hashes, source_id='adapter-software-control',
                    maximum_interval_s=.0075,
                    time_offset_bound_s=r['limits']['time_offset'])
    saved = {}
    events = []

    def save(name, value):
        assert name not in saved
        saved[name] = value
        events.append(name)

    def tangent(anchor):
        native, metadata = load(
            training_kernels['directory'], gravity_anchor_height_m=anchor,
            expected_source_sha256=training_kernels['hashes'][
                'analysis/lll/ilvis0_tangent.cpp'])
        return None, native, dict(tangent=metadata)

    def later():
        events.append('later-receiver-read')
        assert {'union-simultaneous-bounded-physical.json',
                'union-simultaneous-bounded-receiver.json'} <= saved.keys()
        return dict(rows_opened=True)

    result = calculate(spec, r, material,
                       noise_kernel=training_kernels['kernel'],
                       kernel_factory=tangent,
                       reserve=lambda **work: None,
                       save=save, open_scoring=later,
                       check_continue=lambda: None)
    assert result['withheld_truth']['rows_opened']
    assert events.index('union-simultaneous-bounded-receiver.json') < events.index('later-receiver-read')
    assert saved['input-binding.json']['source_id'] == 'adapter-software-control'
    assert result['candidates']['increment']['binding'] == \
        result['candidates']['point']['binding']
