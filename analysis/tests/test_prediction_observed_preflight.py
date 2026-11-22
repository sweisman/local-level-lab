"""No-fit full-history covariance construction on development inputs."""

import numpy as np
import pytest

from test_native_structured_training import training_kernels


@pytest.mark.parametrize('target', ['physical_position', 'receiver_measurement'])
def test_observed_preflight_constructs_target_without_later_receiver(target, training_kernels):
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_observed_preflight import construct_operator
    from lll.prediction_paired_law_study import recipe

    r = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
             query_start_s=.1, query_step_s=.2,
             maximum_evaluations=8)
    spec = dict(model='sphere_rotating', latitude_deg=55.,
                profile=False, start=0, policy_id='reported-short-v1')
    material = construct(
        spec, dict(r, noise=r['noise_by_law']['increment'],
                   sensor_case='interior'), reserve=lambda **work: None)
    cut = material['training_epochs']
    prefix = int(np.searchsorted(np.cumsum(material['dt']),
                                 material['times'][cut - 1]
                                 + r['limits']['time_offset'],
                                 side='left')) + 1
    material['binding'] = dict(material['binding'], source_id='control',
                               training_prefix_packets=prefix)
    material['time_origin_s'] = 0.
    tangent, _ = load(
        training_kernels['directory'],
        gravity_anchor_height_m=material['training_rows'][0]['height_m'],
        expected_source_sha256=training_kernels['hashes'][
            'analysis/lll/ilvis0_tangent.cpp'])
    charges = []
    result = construct_operator(
        material, recipe=r, spec=spec, law='point', target=target,
        kernel=training_kernels['kernel'], tangent_kernel=tangent,
        noise_kernel=training_kernels['kernel'],
        reserve=lambda **work: charges.append(work),
        check_continue=lambda: None)
    assert result['source_id'] == 'control'
    assert result['epoch_count'] == len(material['times'])
    assert result['training_epochs'] == cut
    assert result['prediction_epochs'] == len(material['times']) - cut
    assert result['operator_storage_bytes'] > 0
    assert result['native_calls'] == sum(work['native_calls'] for work in charges)
    assert result['native_calls'] <= (
        len(material['dt']) + prefix + cut + len(material['times']))
    assert result['later_receiver_positions_read'] is False
    assert result['scientific_decision'] == 'abstain'


def test_observed_preflight_rejects_changed_law_before_work():
    from lll.prediction_observed_preflight import construct_operator
    charges = []
    with pytest.raises(ValueError, match='law'):
        construct_operator({}, recipe={}, spec={}, law='invented',
                           target='receiver_measurement', kernel=lambda: None,
                           tangent_kernel=lambda: None,
                           noise_kernel=lambda: None,
                           reserve=lambda **work: charges.append(work),
                           check_continue=lambda: None)
    assert charges == []
