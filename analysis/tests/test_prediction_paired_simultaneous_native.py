# SPDX-License-Identifier: AGPL-3.0-or-later
"""Real native fits save both whole-period unions before generated truth."""
from test_native_structured_training import training_kernels


def test_short_native_pair_saves_both_whole_period_targets(training_kernels):
    from lll.airquantumgrav_noisy_inputs import construct
    from lll.ilvis0_wide_tangent import load
    from lll.prediction_paired_law_study import recipe
    from lll.prediction_paired_simultaneous_native import calculate

    r = dict(recipe(), duration_s=2., rate_hz=200, queries=9,
             query_start_s=.1, query_step_s=.2,
             maximum_evaluations=8, calibration_alpha=.0125,
             simultaneous_alpha=.025)
    spec = dict(model='sphere_rotating', latitude_deg=55.,
                profile=False, start=0, policy_id='reported-short-v1')
    material = construct(spec, dict(r, noise=r['noise_by_law']['increment'],
                                    sensor_case='interior'),
                         reserve=lambda **work: None)
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

    def truth():
        events.append('truth')
        assert {'union-simultaneous-bounded-physical.json',
                'union-simultaneous-bounded-receiver.json'} <= saved.keys()
        return dict(opened=True)

    result = calculate(spec, r, material,
                       noise_kernel=training_kernels['kernel'],
                       kernel_factory=tangent,
                       reserve=lambda **work: None,
                       save=save, withheld_truth=truth,
                       check_continue=lambda: None)
    assert result['withheld_truth']['opened']
    assert events.index('union-simultaneous-bounded-receiver.json') < events.index('truth')
    assert result['candidates']['increment']['binding'] == \
        result['candidates']['point']['binding']
    for target, suffix, diagnostic in (
            ('physical_position', 'physical', 'physical_diagnostic'),
            ('receiver_measurement', 'receiver', 'diagnostic')):
        union = result['simultaneous_law_family'][target]
        assert union['prediction_target'] == target
        assert union['selected_law'] is None
        assert union.get('scope') in (None,
            'union_of_supplied_affine_simultaneous_laws')
        for law in r['input_laws']:
            interval = saved[law+'/simultaneous-bounded-'+suffix+'.json']
            if union.get('scope'):
                assert interval['forecast_support_sha256'] == union['forecast_support_sha256']
            assert interval['error_operator_configuration'] == \
                result['candidates'][law][diagnostic]['error_operator'][
                    'operator_configuration']
