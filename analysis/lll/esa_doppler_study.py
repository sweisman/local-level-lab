# SPDX-License-Identifier: AGPL-3.0-or-later
"""Freeze and reconstruct velocity from the sealed ESA development excerpt."""
import argparse
import fcntl
import gzip
import json
import os
from pathlib import Path
import platform

from . import glonass_code, gnss_doppler
from .compute_budget import environment
from .esa_glonass_code_study import DIRECTORY as GLONASS
from .esa_glonass_comparison import POSITION_FREEZE, POSITION_SHA
from .esa_rinex_code import read_navigation
from .esa_rinex_code_comparison import BASE as GPS, CODE_FREEZE_SHA, CODE_SHA
from .esa_rinex_code_study import _files, _INPUTS
from .esa_rinex_window import FIRST, FOLDER, LAST, LOCAL, WEEK, read_header
from .studies.artifacts import atomic, digest, encoded

DIRECTORY = LOCAL+'/rinex-400-120-stream/doppler-velocity'
PLAN = FOLDER+'ESA_DOPPLER_VELOCITY_PLAN.md'


def position_rows(root, name, freeze_hash, *, file_hash=None, rows_hash=None):
    folder = root/name
    raw = (folder/'positions.json.gz').read_bytes()
    value = json.loads(gzip.decompress(raw))
    # Accept only the known paths and frozen source data for this development cut.
    if ((file_hash is not None and digest(raw) != file_hash)
            or (rows_hash is not None and value['positions_sha256'] != rows_hash)
            or digest((folder/'freeze.json').read_bytes()) != freeze_hash
            or value['freeze_sha256'] != freeze_hash
            or digest(encoded(value['positions'])) != value['positions_sha256']):
        raise ValueError('code path or freeze differs from saved position reconstruction')
    return value['positions'], digest(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'run'))
    args = parser.parse_args()
    threads = environment(threads=1)
    if any(os.environ.get(key) != value for key, value in threads.items()):
        raise ValueError('one numerical thread required')
    import numpy as np

    root = Path.cwd()
    gps, gps_hash = position_rows(root, GPS, CODE_FREEZE_SHA, file_hash=CODE_SHA)
    glonass, glonass_hash = position_rows(root, GLONASS, POSITION_FREEZE, rows_hash=POSITION_SHA)
    obs, nav = _files(root)
    header, metadata = read_header(obs)
    epochs = list(gnss_doppler.observation_epochs(obs[len(header):], metadata['observation_types']))
    times = [(WEEK, FIRST+.5*i) for i in range(round((LAST-FIRST)*2)+1)]
    if [time for time, _ in epochs] != times:
        raise ValueError('unaltered half-second Doppler source grid required')
    nav_text = nav.decode('ascii')
    gps_navigation, _ = read_navigation(nav_text)
    glonass_navigation = glonass_code.navigation(nav_text)
    sources = ['analysis/lll/'+name+'.py' for name in (
        'esa_doppler_study', 'gnss_doppler', 'glonass_code', 'gnss_position',
        'esa_rinex_code', 'esa_rinex_window', 'esa_glonass_comparison',
        'esa_rinex_code_comparison', 'esa_glonass_code_study', 'esa_rinex_code_study',
        'trimble_observations', 'compute_budget', 'studies/artifacts')]
    sources += [PLAN, 'analysis/tests/test_gnss_doppler.py']
    freeze = encoded(dict(version='esa-air1-doppler-v1', inputs=_INPUTS | dict(
        gps_position_file=gps_hash, glonass_position_file=glonass_hash),
        sources={p:digest((root/p).read_bytes()) for p in sources},
        environment=dict(python=platform.python_version(), numpy=np.__version__,
            os=platform.system(), arch=platform.machine(), threads=threads),
        maximum_solves=2*len(times), epochs=len(times), observed_groups=['187'],
        reference_velocities_read=False, new_earth_model_fits=0))
    folder = root/DIRECTORY
    folder.mkdir(exist_ok=True)
    binding = folder/'freeze.json'
    charge = folder/'charge.json'
    path = folder/'velocity.json.gz'
    with (folder/'run.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.action == 'freeze' and not binding.exists():
            atomic(binding, freeze)
        if binding.read_bytes() != freeze:
            raise ValueError('Doppler study freeze changed')
        if args.action == 'freeze':
            print(f'freeze SHA-256 {digest(freeze)}')
            return
        receipt = encoded(dict(freeze_sha256=digest(freeze), charged_solves=2*len(times)))
        if not path.exists():
            if charge.exists():
                raise ValueError('Doppler reconstruction already charged')
            atomic(charge, receipt)
            velocity = list(gnss_doppler.reconstruct(epochs, gps, glonass,
                                                    gps_navigation, glonass_navigation))
            atomic(path, gzip.compress(encoded(dict(freeze_sha256=digest(freeze),
                velocity_sha256=digest(encoded(velocity)), velocity=velocity)), mtime=0))
        value = json.loads(gzip.decompress(path.read_bytes()))
        if (charge.read_bytes() != receipt or value['freeze_sha256'] != digest(freeze)
                or digest(encoded(value['velocity'])) != value['velocity_sha256']
                or [(row['gps_week'], row['gps_week_seconds']) for row in value['velocity']] != times):
            raise ValueError('sealed Doppler rows differ')
        counts = {system:sum(row[system]['status'] == 'converged' for row in value['velocity'])
                  for system in ('G', 'R')}
        print(f'{counts} solved out of {len(times)}, velocity SHA-256 {value["velocity_sha256"]}')


if __name__ == '__main__':
    main()
