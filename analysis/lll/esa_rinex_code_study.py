# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and run the finite ESA AIR1 code reconstruction."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

from .compute_budget import environment
from .esa_rinex_code import observation_epochs, read_navigation, reconstruct
from .esa_rinex_window import FIRST, FOLDER, LAST, LOCAL, WEEK, read_header
from .studies.artifacts import atomic, digest, encoded

_BASE = LOCAL + '/rinex-400-120-stream/'
_OBS = _BASE + 'air10706a-400-120-excerpt.23o.gz'
_NAV = _BASE + 'products/BRDC00IGS_R_20231870000_01D_MN.rnx.gz'
_INPUTS = {
    _OBS: 'cc57da8f72970e5617366be0f4742a7404e5c48d6ce6ec1f122ee8ba78a37e84',
    _NAV: '5cc7b18bc26396ab2811a7a150c7317b704ffac4f73376ac62ed6832131bb002',
}
_SOURCES = tuple('analysis/lll/' + name + '.py' for name in (
    'compute_budget', 'esa_rinex_code', 'esa_rinex_code_study',
    'esa_rinex_window', 'gnss_position', 'trimble_observations', 'studies/artifacts',
)) + (FOLDER + 'ESA_RINEX_CODE_PLAN.md',)


def _files(root):
    obs = gzip.decompress((root / _OBS).read_bytes())
    nav = (root / _NAV).read_bytes()
    if { _OBS: digest(obs), _NAV: digest(nav) } != _INPUTS:
        raise ValueError('sealed observation or navigation input changed')
    return obs, gzip.decompress(nav)


def _approximation(header):
    xyz = []
    clock_flags = []
    for line in header.decode('ascii').splitlines():
        if line[60:].strip() == 'APPROX POSITION XYZ':
            xyz.append([float(item) for item in line[:60].split()])
        if line[60:].strip() == 'RCV CLOCK OFFS APPL':
            clock_flags.append(int(line[:6]))
    if len(xyz) != 1 or len(xyz[0]) != 3 or clock_flags not in ([], [0], [1]):
        raise ValueError('one RINEX starting point and an unambiguous clock flag required')
    return xyz[0], clock_flags[0] if clock_flags else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    settings = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in settings.items()):
        raise ValueError('run through analysis/tests/run_numerical.py --threads 1')
    import numpy as np

    root = Path.cwd()
    obs, nav = _files(root)
    header, metadata = read_header(obs)
    initial, clock_applied = _approximation(header)
    times = [(WEEK, FIRST+.5*i) for i in range(round((LAST-FIRST)*2)+1)]
    freeze = encoded(dict(
        schema='esa-air1-gps-code-v1', input_sha256=_INPUTS,
        source_sha256={name: digest((root/name).read_bytes()) for name in _SOURCES},
        environment=dict(python=platform.python_version(), numpy=np.__version__,
                         os=platform.system(), arch=platform.machine(), settings=settings),
        starting_ecef_m=initial, rinex_clock_applied=clock_applied,
        epoch_count=len(times), first=times[0], last=times[-1],
        methods=['l1_broadcast', 'dual_frequency'],
        maximum_starts=2*len(times), maximum_iterations_per_start=12,
        receiver_export_used=False, reserve_opened=False,
    ))
    output = root / (_BASE + 'code-position')
    output.mkdir(exist_ok=True)
    manifest = output / 'freeze.json'
    result = output / 'positions.json.gz'
    charge = output / 'charge.json'
    with (output / 'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == 'freeze':
            if not manifest.exists():
                atomic(manifest, freeze)
            if manifest.read_bytes() != freeze:
                raise ValueError('existing code reconstruction freeze differs')
            print(f'frozen {len(times)} epochs under two fixed code methods')
            return
        if manifest.read_bytes() != freeze:
            raise ValueError('code reconstruction freeze differs')
        if result.exists():
            saved = json.loads(gzip.decompress(result.read_bytes()))
            positions_sha = digest(encoded(saved['positions']))
            if saved['freeze_sha256'] != digest(freeze) or saved['positions_sha256'] != positions_sha:
                raise ValueError('saved position artifact differs')
            print(f'verified {len(saved["positions"])} already saved epochs, SHA-256 {positions_sha}')
            return
        ephemerides, ions = read_navigation(nav.decode('ascii'))
        records = list(observation_epochs(obs[len(header):].decode('ascii'), metadata['observation_types']))
        if [(item['gps_week'], item['gps_week_seconds']) for item in records] != times:
            raise ValueError('unexpected GPS epoch grid')
        if charge.exists():
            raise ValueError('code reconstruction was already charged')
        atomic(charge, encoded(dict(freeze_sha256=digest(freeze), maximum_starts=2*len(times))))
        positions = list(reconstruct(records, ephemerides, ions, initial))
        positions_sha = digest(encoded(positions))
        report = encoded(dict(freeze_sha256=digest(freeze), positions_sha256=positions_sha,
                              gps_navigation_records=len(ephemerides), positions=positions))
        atomic(result, gzip.compress(report, mtime=0))
        print(f'saved {len(positions)} receiver epochs, SHA-256 {positions_sha}')


if __name__ == '__main__':
    main()
