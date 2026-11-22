# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze, run and verify the bounded GLONASS-only ESA receiver study."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

from . import glonass_code as glo
from .compute_budget import environment
from .esa_rinex_code import read_navigation
from .esa_rinex_code_study import _approximation, _files, _INPUTS
from .esa_rinex_window import FIRST, FOLDER, LAST, LOCAL, WEEK, read_header
from .studies.artifacts import atomic, digest, encoded

DIRECTORY = LOCAL+'/rinex-400-120-stream/glonass-position'
PLAN = FOLDER+'ESA_GLONASS_CODE_PLAN.md'
SOURCE = tuple('analysis/lll/'+name+'.py' for name in (
    'esa_glonass_code_study', 'glonass_code', 'gnss_position', 'esa_rinex_code',
    'esa_rinex_window', 'esa_rinex_code_study', 'compute_budget', 'studies/artifacts',
)) + (PLAN, 'analysis/tests/test_glonass_code.py')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in threads.items()):
        raise ValueError('configure one numerical thread before imports')
    import numpy as np
    import scipy

    root = Path.cwd()
    obs, nav = _files(root)
    header, metadata = read_header(obs)
    initial, clock_applied = _approximation(header)
    times = [(WEEK, FIRST+.5*i) for i in range(round((LAST-FIRST)*2)+1)]
    ephemerides = glo.navigation(nav.decode('ascii'))
    _, ionosphere = read_navigation(nav.decode('ascii'))
    records = list(glo.observation_epochs(obs[len(header):].decode('ascii'),
                                         metadata['observation_types']))
    if [time for time, _ in records] != times:
        raise ValueError('same consecutive half-second source grid required')
    freeze = encoded(dict(schema='esa-air1-glonass-code-v1', input_sha256=_INPUTS,
        source_sha256={name:digest((root/name).read_bytes()) for name in SOURCE},
        environment=dict(python=platform.python_version(), numpy=np.__version__,
            scipy=scipy.__version__, os=platform.system(), arch=platform.machine(), threads=threads),
        starting_ecef_m=initial, rinex_clock_applied=clock_applied, first=times[0], last=times[-1],
        maximum_starts=2*len(times), maximum_updates=12, methods=glo.METHODS,
        glonass_records=len(ephemerides), read_export_positions=False,
        new_earth_model_fits=0, reserved_group_reads=0))
    folder = root/DIRECTORY
    folder.mkdir(exist_ok=True)
    manifest = folder/'freeze.json'
    charge = folder/'charge.json'
    result_path = folder/'positions.json.gz'
    with (folder/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == 'freeze' and not manifest.exists():
            atomic(manifest, freeze)
        if manifest.read_bytes() != freeze:
            raise ValueError('frozen GLONASS dependencies or observations changed')
        if args.action == 'freeze':
            print(f'{len(ephemerides)} GLONASS navigation records, freeze SHA-256 {digest(freeze)}')
            return
        allowance = encoded(dict(freeze_sha256=digest(freeze), charged_starts=2*len(times)))
        if not result_path.exists():
            if charge.exists():
                raise ValueError('GLONASS positioning was already charged')
            atomic(charge, allowance)
            positions = list(glo.reconstruct(records, ephemerides, ionosphere, initial))
            report = encoded(dict(freeze_sha256=digest(freeze), positions=positions,
                                  positions_sha256=digest(encoded(positions))))
            atomic(result_path, gzip.compress(report, mtime=0))
        saved = json.loads(gzip.decompress(result_path.read_bytes()))
        if (charge.read_bytes() != allowance or saved['freeze_sha256'] != digest(freeze)
                or digest(encoded(saved['positions'])) != saved['positions_sha256']
                or [(row['gps_week'], row['gps_week_seconds']) for row in saved['positions']] != times):
            raise ValueError('sealed GLONASS position rows differ')
        counts = {name: sum(row[name]['status'] == 'converged' for row in saved['positions'])
                  for name in glo.METHODS}
        print(f'{counts} solved out of {len(times)}, positions SHA-256 {saved["positions_sha256"]}')


if __name__ == '__main__':
    main()
