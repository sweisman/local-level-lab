from lll.ilvis0_matched_extension_forecast import compare_shapes


def test_new_flight_requires_complete_same_field_shape_comparisons_before_field_rank():
    globes = ('sphere_rotating', 'sphere_still')
    discs = ('flat_geographic_field', 'flat_still')
    tracks = ('onboard', 'l1_broadcast', 'dual_frequency')
    order = dict(zip((*globes, *discs), (1., 2., 3., 4.), strict=True))

    def row(value):
        return dict(heldout_rms_by_gps_stream={track: dict(horizontal_rms_m=value, height_rms_m=0.)
                                              for track in tracks})

    records = {model: row(value) for model, value in order.items()}
    assert compare_shapes(records)['globe_field'] == 'specified'
    del records['flat_still']
    assert compare_shapes(records)['globe_field'] == 'unresolved'
    records['flat_still'] = row(1.9)
    assert compare_shapes(records)['globe_field'] == 'unresolved'
    records['flat_still'] = row(4.)
    records['flat_geographic_field']['heldout_rms_by_gps_stream']['onboard']['horizontal_rms_m'] = .9
    assert compare_shapes(records)['globe_field'] == 'unresolved'
