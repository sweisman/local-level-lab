"""Bounded, reproducible memory/time check for 64,080 receiver epochs."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import resource
import time

import numpy as np
import scipy

from lll.ilvis0_error_model import Spec
from lll.ilvis0_structured_receiver_likelihood import StructuredWhitening

MAX_EPOCHS = 64080
SEED = 20261118


def _hash_arrays(*arrays):
    digest = hashlib.sha256()
    for array in arrays:
        item = np.ascontiguousarray(array)
        digest.update(str(item.dtype).encode())
        digest.update(str(item.shape).encode())
        digest.update(item.tobytes())
    return digest.hexdigest()


def run(epochs, output):
    if type(epochs) is not int or not 1 <= epochs <= MAX_EPOCHS:
        raise ValueError('epoch count must be 1..64080')
    output = Path(output)
    if output.exists():
        raise ValueError('benchmark output already exists')
    rng = np.random.default_rng(SEED)
    index = np.arange(epochs, dtype=float)
    times = 0.5 * index + 0.01 * np.sin(index * 0.03)
    spec = Spec(
        white=np.diag([0.09, 0.16, 0.25]),
        components=((12.0, np.diag([0.04, 0.02, 0.09])),
                    (900.0, np.diag([0.02, 0.04, 0.03]))),
        offset=np.diag([0.01, 0.02, 0.01]),
        drift=np.diag([0.04, 0.03, 0.02]),
        drift_origin_s=0.0,
        drift_span_s=float(times[-1] + 1.0))
    formal = np.broadcast_to(
        np.array([[0.03, 0.004, 0.0],
                  [0.004, 0.05, 0.0],
                  [0.0, 0.0, 0.08]]), (epochs, 3, 3)).copy()
    transforms = np.broadcast_to(np.eye(3), (epochs, 3, 3)).copy()
    residual = rng.normal(size=3 * epochs)
    jacobian = rng.normal(size=(3 * epochs, 26))
    input_sha = _hash_arrays(times, spec.white, spec.offset, spec.drift,
                             *(matrix for _, matrix in spec.components),
                             formal, transforms, residual, jacobian)
    start = time.perf_counter()
    operator = StructuredWhitening(times, spec, formal_blocks=formal,
                                   transforms=transforms)
    result = operator.apply(residual, jacobian)
    elapsed = time.perf_counter() - start
    output_sha = _hash_arrays(result['residual'], result['jacobian'],
                              np.array([result['quadratic'],
                                        result['log_determinant'],
                                        result['negative_log_likelihood']]))
    report = {
        'version': 'structured-receiver-benchmark-v1',
        'epochs': epochs,
        'jacobian_columns': 26,
        'seed': SEED,
        'input_sha256': input_sha,
        'output_sha256': output_sha,
        'quadratic': result['quadratic'],
        'log_determinant': result['log_determinant'],
        'wall_seconds': elapsed,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'python': platform.python_version(),
        'numpy': np.__version__,
        'scipy': scipy.__version__,
        'source_sha256': hashlib.sha256(
            (Path(__file__).resolve().parents[1] / 'lll' /
             'ilvis0_structured_receiver_likelihood.py').read_bytes()).hexdigest(),
        'core_source_sha256': hashlib.sha256(
            (Path(__file__).resolve().parents[1] / 'lll' /
             'state_space_covariance.py').read_bytes()).hexdigest(),
        'benchmark_source_sha256': hashlib.sha256(
            Path(__file__).read_bytes()).hexdigest(),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.partial')
    temporary.write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    os.replace(temporary, output)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--epochs', type=int, default=MAX_EPOCHS)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = run(args.epochs, args.output)
    print(json.dumps({key: report[key] for key in
                      ('epochs', 'wall_seconds', 'peak_rss_kib',
                       'input_sha256', 'output_sha256')}, sort_keys=True))


if __name__ == '__main__':
    main()
