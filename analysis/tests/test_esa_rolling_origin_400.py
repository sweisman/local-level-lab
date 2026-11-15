"""The earlier ESA development cut excludes its future receiver values."""

import gzip
import io
import json

import numpy as np


def _parent(*,later_shift=0.):
    stream=io.BytesIO()
    np.savez(stream,theta=np.zeros((550,3)),dv=np.zeros((550,3)),
             dt=np.ones(550))
    rows=[dict(time_s=float(100+i),latitude_deg=1.,longitude_deg=2.,
               height_m=float(i)+(later_shift if i>=400 else 0.))
          for i in range(800)]
    return dict(interval=stream.getvalue(),
                training=gzip.compress(json.dumps(rows).encode()),
                **{'saved-increment-forecast':json.dumps(
                    dict(times_s=np.arange(1.,801.).tolist())).encode(),
                   'saved-input-binding':json.dumps(dict(
                       source_id='esa-99f1530c3eda4318',
                       training_epochs=800,time_origin_s=99.)).encode(),
                   'recipe':json.dumps(dict(clock='header_elapsed',
                       model='sphere_rotating',limits=dict(time_offset=0.),
                       noise_by_law={'increment':{},'point':{}})).encode()})


def test_400_120_fit_material_excludes_future_receiver_values():
    from lll.esa_rolling_origin_400 import build_material
    first=build_material(_parent())
    changed=build_material(_parent(later_shift=1000.))
    assert first.split.fit_material()==changed.split.fit_material()
    assert len(json.loads(gzip.decompress(first.split.training_bytes)))==400
    assert len(first.split.scoring_rows)==120
    assert first.split.scoring_rows!=changed.split.scoring_rows
    assert first.split.packet_count==520
    assert first.split.times_s[-1]==520.
