# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two preserved flights, paired carrier-phase positions and matched motion diagnostics."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

import numpy as np

from . import gnss_carrier_phase as phase, gnss_position as gps
from . import ilvis0_gps_reconstruction_pilot as pilot
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy

IDENTITY = 'ilvis0-gps-carrier-pilot-v1-20261118'
PLAN = pilot.FOLDER+'GPS_CARRIER_PHASE_PLAN.md'
ADAPTER = 'analysis/lll/ilvis0_gps_carrier_pilot.py'
MAX_PAIRS = 1110
SCOPE = 'receiver-only L1 phase differences on the two frozen pilot recordings'


def _decode(blob):
    return json.loads(gzip.decompress(blob))


def _elapsed(a, b):
    return (b['tag']-a['tag'])/1000.


def _sign(records):
    """Qualify raw encoding with earlier clock-centred code changes."""
    errors = {-1: [], 1: []}
    for a, b in zip(records[:60], records[1:61], strict=True):
        if not .75 <= _elapsed(a, b) <= 1.25:
            continue
        common = phase.matched_phase(a['measurement'], b['measurement'])
        if len(common) < 5:
            continue
        code = np.array([v['pseudorange_m']-u['pseudorange_m'] for u, v in common.values()])
        carrier = np.array([v['phase_cycles']-u['phase_cycles'] for u, v in common.values()])
        for sign in errors:
            residual = code-sign*phase.L1_WAVELENGTH_M*carrier
            errors[sign].append(float(np.sqrt(np.mean((residual-np.median(residual))**2))))
    medians = {sign: float(np.median(values)) for sign, values in errors.items() if values}
    if len(errors[-1]) < 20:
        raise ValueError('insufficient earlier code/phase pairs to qualify the encoding sign')
    sign = min(medians, key=medians.get)
    if medians[sign] > 5. or medians[-sign] < 10.*max(medians[sign], .01):
        raise ValueError('earlier code changes did not qualify one unambiguous phase sign')
    return dict(sign=sign, training_pairs=len(errors[sign]),
                median_pair_range_change_rms_m={str(k): v for k, v in medians.items()})


def _tracks(study):
    picks = {row['identity']: row for row in study.input('selection')['selected']}
    tracks = {name: dict(records={}, positions={}) for name in picks}
    for identity, spec in study.tasks.items():
        name = spec['source_identity']
        track = tracks[name]
        data = _decode(study.input(spec['input_key'], raw=True))
        positions = _decode(study.artifact(identity, 'positions.json.gz', raw=True))
        for key in ('ephemerides', 'ionosphere', 'imu_type', 'segment_id'):
            if key in track and track[key] != data[key]:
                raise ValueError('GPS block metadata changed within a recording')
            track[key] = data[key]
        for record in data['records']:
            tag = record['tag']
            if tag in track['records'] or pilot.parent.tag(record['measurement']) != tag:
                raise ValueError('duplicate or changed GPS epoch')
            track['records'][tag] = dict(tag=tag, measurement=record['measurement'],
                onboard=gps.ecef(*pilot._geodetic(record['reference'])).tolist())
        for position in positions:
            tag, method = position['gps_millisecond_tag'], position['method']
            if (position['measurement_sha256'] != track['records'][tag]['measurement']['payload_sha256']
                    or method not in pilot.METHODS or position['status'] != 'converged'):
                raise ValueError('all archived code solutions must bind to the paired observation')
            methods = track['positions'].setdefault(tag, {})
            if method in methods:
                raise ValueError('duplicate code solution')
            methods[method] = position['ecef_m']
    for name, track in tracks.items():
        if sorted(track['records']) != picks[name]['gps_millisecond_tags']:
            raise ValueError('GPS carrier pilot must keep the same frozen time tags')
        track['records'] = [dict(row, **track['positions'][tag])
                            for tag, row in sorted(track['records'].items())]
        del track['positions']
    if len(tracks) != 2 or sum(len(tr['records'])-1 for tr in tracks.values()) != MAX_PAIRS:
        raise ValueError('changed carrier pilot allowance')
    return tracks


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/IDENTITY).exists():
        raise ValueError('existing phase pilot must be inspected or resumed')
    inputs = dict(plan=PLAN)
    tasks = []
    with closing(ClosedStudy(root, 'data/'+pilot.IDENTITY)) as study:
        if study.completion['state'] != 'complete' or not study.summary['passed']:
            raise ValueError('the completed two-recording code pilot is required')
        sources = dict(code_completion=study.completion, sign_by_recording={})
        for name, track in _tracks(study).items():
            records = track.pop('records')
            sign = _sign(records)
            sources['sign_by_recording'][name] = sign
            for first in range(0, len(records)-1, 100):
                selected = records[first:first+101]
                identity = name+'-phase-'+str(first//100)
                path = f'data/{IDENTITY}-inputs/{identity}.json.gz'
                pilot._write_equal(root/path, gzip.compress(encoded(dict(track, records=selected, sign=sign['sign'])), mtime=0))
                inputs[identity] = path
                tasks.append(dict(identity=identity, input_key=identity, segment_id=track['segment_id'],
                    tags=[r['tag'] for r in selected], phase_attempts=len(selected)-1,
                    limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)))
    path = f'data/{IDENTITY}-inputs/provenance.json'
    pilot._write_equal(root/path, encoded(sources))
    inputs['provenance'] = path
    definition = dict(id=IDENTITY, scope=SCOPE, adapter=ADAPTER, workers=2, threads=1,
        maximum_wall_s=180., inputs=inputs, tasks=tasks,
        sources=source_closure(root, (ADAPTER, PLAN, 'analysis/tests/test_gnss_carrier_phase.py')))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=IDENTITY, tasks=len(tasks), phase_attempts=MAX_PAIRS,
                configuration=manifest['allocation'], **sources)


def evaluate(task, context):
    data = _decode(context.input_path().read_bytes())
    records = data['records']
    if (context.manifest['scope'] != SCOPE or data['segment_id'] != task['segment_id']
            or task['tags'] != [r['tag'] for r in records] or task['phase_attempts'] != len(records)-1):
        raise ValueError('changed matched phase inputs')
    context.save('phase-charge.json', dict(tags=task['tags'], maximum_attempts=task['phase_attempts'],
                                         maximum_iterations=phase.MAX_ITERATIONS, imu_fit_starts=0))
    rows = []
    for a, b in zip(records, records[1:]):
        dt = _elapsed(a, b)
        row = dict(first_tag=a['tag'], last_tag=b['tag'], duration_s=dt)
        if .75 <= dt <= 1.25 and a['measurement']['gps_week'] == b['measurement']['gps_week']:
            result = phase.solve_pair(a['measurement'], b['measurement'], data['ephemerides'],
                                      data['ionosphere'], a['l1_broadcast'], sign=data['sign'])
        else:
            result = dict(status='abstain', reason='missing adjacent receiver epoch')
        if result['status'] == 'converged':
            result['difference_ecef_m'] = {key: (np.asarray(result['displacement_ecef_m'])
                - np.asarray(b[key]) + np.asarray(a[key])).tolist() for key in ('onboard', *pilot.METHODS)}
        rows.append(dict(row, **result))
    context.save('phase.json', rows)
    return dict(passed=True, pair_count=len(rows), converged=sum(r['status']=='converged' for r in rows),
                imu_fit_starts=0, scientific_decision='abstain')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare',))
    parser.parse_args()
    print(json.dumps(prepare(Path.cwd()), sort_keys=True))
