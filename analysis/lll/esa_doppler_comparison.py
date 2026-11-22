# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit sealed Doppler velocities against the opened ESA receiver export."""
import argparse
from contextlib import closing
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform
from statistics import median

from .airquantumgrav_geographic_report import error_metrics
from .compute_budget import environment
from .esa_doppler_study import DIRECTORY
from .esa_fit_adjusted_forecast_report import ecef_coordinates
from .esa_glonass_comparison import MATCH_SHA
from .esa_rinex_code_comparison import BASE, FOLDER, PARENT, PARENT_SHA, coordinates
from .gnss_position import local_rotation
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

PLAN = FOLDER+'ESA_DOPPLER_COMPARISON_PLAN.md'
REPORT = FOLDER+'esa-doppler-comparison-result.json'
VELOCITY_SHA = '2154f617188047b4904a95089002c49f119b8365e71128710976bf6a23dc4b35'
VELOCITY_FREEZE = '27b72f4775e6096d5af4f44cd6b8ab5130e6003f3598bbd148e0770e03ebacdb'


def integrate_half_second(origin, velocities):
    import numpy as np

    start = np.asarray(origin, float)
    rates = np.asarray(velocities, float)
    if (start.shape != (3,) or rates.ndim != 2 or rates.shape[1] != 3 or len(rates) < 2
            or not np.all(np.isfinite(start)) or not np.all(np.isfinite(rates))):
        raise ValueError('finite three-axis origin and half-second velocities required')
    steps = .25*(rates[1:]+rates[:-1])
    return start+np.vstack((np.zeros(3), np.cumsum(steps, axis=0)))


def _series(errors):
    import numpy as np

    def correlation(values, lag):
        left, right = values[:-lag], values[lag:]
        if np.ptp(left) == 0 or np.ptp(right) == 0:
            return None
        return float(np.corrcoef(left, right)[0, 1])

    output = {}
    for label, block in (('earlier', errors[:400]), ('later', errors[400:])):
        output[label] = dict(
            epochs=len(block), rms_neu_mps=np.sqrt(np.mean(block**2, axis=0)).tolist(),
            mean_neu_mps=np.mean(block, axis=0).tolist(),
            autocorrelation={str(lag):[correlation(axis, lag) for axis in block.T]
                             for lag in (1, 5, 20, 60)})
    return output | dict(signed_errors_neu_mps=errors.tolist())


def compare(parent, indices, records):
    import numpy as np

    export = json.loads(gzip.decompress(parent.input('training', raw=True)))
    if (len(export) != 800 or len(indices) != 520 or indices != sorted(set(indices))
            or not 0 <= indices[0] < indices[-1] < len(records)):
        raise ValueError('exact earlier/later development split required')
    export = export[:520]
    matched = [records[index] for index in indices]
    if any(row['gps_week'] != ref['gps_week']
           or abs(row['gps_week_seconds']-ref['time_s']) > .001
           for row, ref in zip(matched, export, strict=True)):
        raise ValueError('same matched epoch required')
    grids = [row['gps_week_seconds'] for row in records]
    if any(b-a != .5 for a,b in zip(grids,grids[1:])):
        raise ValueError('half-second Doppler grid required')
    coords = coordinates(export)
    rotation = np.asarray([local_rotation(phi, longitude) for phi, longitude, _ in coords])
    ecef = ecef_coordinates(coords)
    target = np.asarray([[row[key] for key in ('north_mps', 'east_mps', 'up_mps')] for row in export])
    solutions, motion, local = {}, {}, {}
    for system in ('G', 'R'):
        solved = [row[system] for row in records if row[system]['status'] == 'converged']
        solutions[system] = dict(total=len(records), solved=len(solved),
            median_fit_residual_mps=median(row['rate_rms_mps'] for row in solved) if solved else None,
            min_satellites=min((len(row['used_satellites']) for row in solved), default=0),
            max_satellites=max((len(row['used_satellites']) for row in solved), default=0))
        if any(row[system]['status'] != 'converged' for row in matched):
            continue
        matched_velocity = [row[system]['velocity_ecef_mps'] for row in matched]
        local[system] = np.einsum('ijk,ik->ij', rotation, matched_velocity)
        solutions[system]['minus_export'] = _series(local[system]-target)
        motion[system] = {}
        for label, anchor, first, last in (('earlier', 0, 0, 399), ('later', 399, 400, 519)):
            start = indices[anchor]
            span = records[start:indices[last]+1]
            if any(row[system]['status'] != 'converged' for row in span):
                motion[system][label] = dict(status='incomplete_path')
                continue
            path = integrate_half_second(ecef[anchor], [row[system]['velocity_ecef_mps'] for row in span])
            subset = slice(first, last+1)
            delta = path[np.asarray(indices[subset])-start]-ecef[subset]
            errors = np.einsum('ijk,ik->ij', rotation[subset], delta).tolist()
            motion[system][label] = dict(status='complete', anchor_report=anchor,
                duration_s=.5*(indices[last]-start), endpoint_neu_m=errors[-1],
                metrics=error_metrics(errors), signed_errors_neu_m=errors)
    return dict(matched_reports=len(indices), per_constellation=solutions, integrated_motion=motion,
                gps_minus_glonass=_series(local['G']-local['R']) if len(local)==2 else None,
                independent_airborne_truth=False, reserved_reads=0, new_earth_model_fits=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in threads.items()):
        raise ValueError('one numerical thread required')
    import numpy as np

    root = Path.cwd()
    folder = root/DIRECTORY
    velocity = json.loads(gzip.decompress((folder/'velocity.json.gz').read_bytes()))
    matching = json.loads((root/(BASE+'comparison.json')).read_bytes())
    if (digest(encoded(velocity['velocity'])) != VELOCITY_SHA
            or velocity['velocity_sha256'] != VELOCITY_SHA
            or velocity['freeze_sha256'] != VELOCITY_FREEZE
            or digest((folder/'freeze.json').read_bytes()) != VELOCITY_FREEZE
            or digest(encoded(matching['result'])) != MATCH_SHA or matching['result_sha256'] != MATCH_SHA):
        raise ValueError('sealed Doppler solutions or GPS matching differ')
    with (folder/'comparison.lock').open('a') as lock, closing(ClosedStudy(root, PARENT)) as parent:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if parent.completion['manifest_sha256'] != PARENT_SHA:
            raise ValueError('sealed 800-report receiver parent differs')
        sources = [Path(__file__), root/PLAN, root/'analysis/tests/test_esa_doppler_comparison.py']
        sources.extend(root/'analysis/lll'/name for name in (
            'airquantumgrav_geographic_report.py', 'airquantumgrav_truth.py',
            'esa_fit_adjusted_forecast_report.py', 'esa_rinex_code_comparison.py',
            'gnss_position.py', 'compute_budget.py', 'studies/artifacts.py', 'studies/closed.py'))
        freeze = encoded(dict(
            inputs=dict(velocity=VELOCITY_SHA, match=MATCH_SHA, parent=PARENT_SHA),
            sources={str(path.relative_to(root)): digest(path.read_bytes()) for path in sources},
            environment=dict(python=platform.python_version(), numpy=np.__version__,
                             os=platform.system(), arch=platform.machine(), threads=threads),
            max_new_fits=0, max_new_forecasts=0, observed_groups=['187']))
        binding = folder/'comparison-freeze.json'
        if args.action == 'freeze' and not binding.exists():
            atomic(binding, freeze)
        if binding.read_bytes() != freeze:
            raise ValueError('Doppler comparison freeze differs')
        if args.action == 'freeze':
            print(digest(freeze))
            return
        path = root/REPORT
        if not path.exists():
            result = compare(parent, matching['result']['matched_code_indices'], velocity['velocity'])
            atomic(path, encoded(dict(freeze=json.loads(freeze), freeze_sha256=digest(freeze),
                                      result=result, result_sha256=digest(encoded(result)))))
        sealed = json.loads(path.read_bytes())
        if (sealed['freeze_sha256'] != digest(freeze)
                or digest(encoded(sealed['freeze'])) != sealed['freeze_sha256']
                or digest(encoded(sealed['result'])) != sealed['result_sha256']):
            raise ValueError('sealed Doppler comparison differs')
        print(f'{sealed["result"]["matched_reports"]} matches, SHA-256 {sealed["result_sha256"]}')


if __name__ == '__main__':
    main()
