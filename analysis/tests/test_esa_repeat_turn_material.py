import gzip
import io
import json

import numpy as np
import pytest

from lll import esa_repeat_turn_material as material
from lll.studies.artifacts import digest, encoded


def fixture():
    rows = [{'time_s': 100.+i, 'latitude_deg': 65., 'longitude_deg': -32., 'height_m': 300.}
            for i in range(400)]
    time = 100.+np.arange(520)-99.95
    packets = 130000
    arrays = dict(dt=np.full(packets, .004), theta=np.ones((packets, 3)), dv=np.ones((packets, 3)))
    count = int(np.searchsorted(np.cumsum(arrays['dt']), time[399]+.01))+1
    hashes = {key: digest(value.astype('<f8').tobytes()) for key, value in arrays.items()}
    prefix = {key: digest(value[:count].astype('<f8').tobytes()) for key, value in arrays.items()}
    receipt = dict(training_receiver_sha256=digest(encoded(rows)), query_times_s=time.tolist(),
                   training_packets=count, forecast_packets=packets, increment_hashes=hashes,
                   training_prefix_hashes=prefix, raw_first_s=99.95)
    return rows, time, arrays, receipt


def test_packaged_forecast_material_can_contain_only_earlier_positions():
    rows, time, arrays, receipt = fixture()
    result = material.package(rows, time, arrays, receipt)
    assert set(result) == {'training.json.gz', 'forecast-times.json', 'interval.npz'}
    assert json.loads(gzip.decompress(result['training.json.gz'])) == rows
    assert json.loads(result['forecast-times.json']) == time.tolist()
    with np.load(io.BytesIO(result['interval.npz']), allow_pickle=False) as contents:
        assert set(contents.files) == {'dt', 'theta', 'dv'}
        assert contents['theta'] == pytest.approx(arrays['theta'])
    assert material.package(rows, time, arrays, receipt) == result


def test_comparison_refuses_added_outcomes_and_mutated_training_prefix():
    rows, time, arrays, receipt = fixture()
    with pytest.raises(ValueError, match='earlier receiver'):
        material.package(rows+[rows[-1]], time, arrays, receipt)
    arrays['dv'][0, 0] = 9.
    with pytest.raises(ValueError, match='inertial hash'):
        material.package(rows, time, arrays, receipt)
