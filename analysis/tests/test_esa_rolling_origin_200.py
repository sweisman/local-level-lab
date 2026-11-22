"""The new earlier-origin cut cannot fit to its scoring positions."""

import gzip
import io
import json

import numpy as np


def _source(*, withheld_shift=0.):
    buffer = io.BytesIO()
    np.savez(buffer, theta=np.zeros((400, 3)), dv=np.zeros((400, 3)),
             dt=np.ones(400))
    rows = [dict(time_s=float(100+i), latitude_deg=1., longitude_deg=2.,
                 height_m=float(i)+(withheld_shift if i >= 200 else 0.))
            for i in range(800)]
    return dict(interval=buffer.getvalue(),
                training=gzip.compress(json.dumps(rows).encode()),
                **{'saved-increment-forecast': json.dumps(
                    dict(times_s=np.arange(1., 801.).tolist())).encode(),
                   'saved-input-binding': json.dumps(dict(
                    source_id='esa-99f1530c3eda4318', training_epochs=800,
                    time_origin_s=99.)).encode(),
                   'recipe': json.dumps(dict(clock='header_elapsed',
                    model='sphere_rotating', maximum_evaluations=200,
                    limits=dict(time_offset=0.),
                    noise_by_law={'increment': {}, 'point': {}})).encode()})


def test_200_120_fit_material_excludes_all_scoring_values():
    from lll.esa_rolling_origin_200 import build_material

    original = build_material(_source())
    altered = build_material(_source(withheld_shift=1000.))
    assert original.split.fit_material() == altered.split.fit_material()
    assert original.split.scoring_rows != altered.split.scoring_rows
    assert len(json.loads(gzip.decompress(original.split.training_bytes))) == 200
    assert len(original.split.scoring_rows) == 120
    assert original.split.packet_count == 320
    assert original.split.times_s[-1] == 320.
