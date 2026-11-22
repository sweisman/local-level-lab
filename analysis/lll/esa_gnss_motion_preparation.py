# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze training-only ESA-187 IMU and 5 Hz receiver motion inputs."""

import gzip
import hashlib
import io
import json
from pathlib import Path


FIT = 'data/esa-rolling-origin-400-development-v1-20261115'
RATE = 'data/esa-training-rate-variation-20261024'
SOURCE = 'data/external-imu-survey-20261018/esa-sample/187_mosaic03_ppp_5Hz_final.txt'
OUTPUT = 'data/esa-gnss-motion-context-input-v1'
TRAINING_SHA = '07bf133c016e9f4429827a3a1803487e2bed3df6a7728af2c5ec641deedee6c9'
RATE_SHA = '41c03b1756e243b42abd04d081995244670c28dfad2aad0b225e7e96e1788a94'
GNSS_SHA = 'e6706cbe2971c25dc07d03446d8a77b9a48f673be0d967d1a8a11de59578555d'


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def prepare(root):
    import numpy as np
    from .airquantumgrav_receiver import records
    from .esa_parallel_gnss import earlier_lines
    from .esa_ppp_acquisition import TARGETS, verify_complete
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy

    root = Path(root).resolve()
    fit = ClosedStudy(root, FIT)
    rate = ClosedStudy(root, RATE)
    try:
        training_raw = fit.input('training', raw=True)
        rate_raw = rate.input('interval', raw=True)
        if _sha(training_raw) != TRAINING_SHA or _sha(rate_raw) != RATE_SHA:
            raise ValueError('saved ESA training inputs changed')
        training = json.loads(gzip.decompress(training_raw))
        if len(training) != 400 or any(
                training[i]['time_s'] >= training[i+1]['time_s']
                for i in range(399)):
            raise ValueError('ordered 400-report training boundary required')
        first = float(training[0]['time_s'])
        cutoff = float(training[-1]['time_s'])
        if first != 388214.9996717 or cutoff != 388613.99964356:
            raise ValueError('unchanged ESA development training times required')
        base = root / 'data/external-imu-survey-20261018/esa-sample'
        path = root / SOURCE
        receipt = json.loads((base / (path.name + '.receipt.json')).read_text())
        if verify_complete(path, TARGETS[path.name], receipt) != GNSS_SHA:
            raise ValueError('verified 5 Hz receiver source required')
        with path.open() as stream:
            receiver = [row for row in records(earlier_lines(
                stream, last_training_s=cutoff)) if row['time_s'] >= first-5]
        if len(receiver) != 2021 or receiver[-1]['time_s'] > cutoff+.002:
            raise ValueError('fixed earlier-only 5 Hz receiver rows required')
        with np.load(io.BytesIO(rate_raw), allow_pickle=False) as archive:
            time = archive['raw_time_s']
            angular = archive['angular_rate_rads']
        selected = (time >= first-5) & (time <= cutoff)
        if (len(time) != 360029 or int(np.sum(selected)) != 119865 or
                angular.shape != (len(time), 3) or
                np.any(np.diff(time) <= 0)):
            raise ValueError('fixed earlier-only IMU source required')
        buffer = io.BytesIO()
        np.savez_compressed(buffer, imu_time_s=time[selected],
                            gyro_body_rads=angular[selected],
                            receiver_time_s=np.array([row['time_s'] for row in receiver]),
                            receiver_ne_mps=np.array([[row['north_mps'], row['east_mps']]
                                                      for row in receiver]),
                            center_time_s=np.array([row['time_s'] for row in training]))
        staged = buffer.getvalue()
        binding = dict(version='esa-gnss-motion-context-input-v1',
                       training_sha256=TRAINING_SHA, rate_sha256=RATE_SHA,
                       gnss_sha256=GNSS_SHA, staged_sha256=_sha(staged),
                       source_sha256=_sha(Path(__file__).read_bytes()),
                       first_training_s=first, last_training_s=cutoff,
                       imu_samples=int(np.sum(selected)),
                       receiver_samples=len(receiver), centers=len(training),
                       later_receiver_reports_decoded=0,
                       protected_group_reads=0, earth_model_fits=0)
        directory = root / OUTPUT
        directory.mkdir(parents=True, exist_ok=True)
        for target, raw in ((directory/'staged.npz', staged),
                            (directory/'binding.json', encoded(binding))):
            if target.exists():
                if target.read_bytes() != raw:
                    raise ValueError('existing staged motion input differs')
            else:
                atomic(target, raw)
        return binding
    finally:
        fit.close()
        rate.close()


if __name__ == '__main__':
    print(json.dumps(prepare('.'), sort_keys=True))
