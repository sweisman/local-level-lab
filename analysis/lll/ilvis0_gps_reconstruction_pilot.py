# SPDX-License-Identifier: AGPL-3.0-or-later
"""Two-flight receiver-only GPS reconstruction from the frozen epoch selection."""

import argparse
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

import numpy as np

from . import gnss_position as gps
from . import ilvis0_raw_gps_preflight as parent
from .ilvis0_position import fit_epoch
from .ilvis0_receiver_overlap import _time_index
from .studies.artifacts import atomic, digest, encoded


IDENTITY = 'ilvis0-gps-reconstruction-pilot-v1-20261118'
FOLDER = parent.FOLDER
PLAN = FOLDER+'GPS_RECONSTRUCTION_PILOT_PLAN.md'
SELECTION = FOLDER+'gps-reconstruction-pilot-selection.json'
PREFLIGHT_RECEIPT = FOLDER+'raw-gps-preflight-receipt.json'
ADAPTER = 'analysis/lll/ilvis0_gps_reconstruction_pilot.py'
BLOCK = 100
METHODS = parent.METHODS
MAX_ITERATIONS = 12


def one_per_second(tags):
    """Take the first observed millisecond tag per second without filling gaps."""
    if (not tags or any(type(tag) is not int or tag < 0 for tag in tags)
            or any(right <= left for left, right in zip(tags, tags[1:]))):
        raise ValueError('ordered unique integer GPS time tags required')
    return [tag for i, tag in enumerate(tags) if not i or tag//1000 != tags[i-1]//1000]


def _geodetic(reference):
    latitude, longitude = np.deg2rad([float(reference['latitude_deg']),
                                     float(reference['longitude_deg'])])
    return latitude, longitude, float(reference['ellipsoid_height_m'])


def receiver_difference(ecef, reference):
    latitude, longitude, _ = geo = _geodetic(reference)
    return gps.local_rotation(latitude, longitude) @ (np.asarray(ecef)-gps.ecef(*geo))


def _write_equal(path, payload):
    if path.is_file():
        if path.read_bytes() != payload:
            raise ValueError('existing staged material differs: '+str(path))
    else:
        atomic(path, payload)


def _verified_selection(root, study):
    selection = json.loads((root/SELECTION).read_bytes())
    if (selection['plan_sha256'] != digest((root/PLAN).read_bytes())
            or selection['preflight_receipt_sha256'] != digest((root/PREFLIGHT_RECEIPT).read_bytes())
            or selection['preflight'] != study.completion
            or selection['maximum_iterations_per_start'] != MAX_ITERATIONS
            or selection['imu_fit_budget'] != 0):
        raise ValueError('frozen position selection or plan changed')
    coverage = (root/FOLDER/'raw-gps-preflight-coverage.csv').read_bytes()
    receipt = json.loads((root/PREFLIGHT_RECEIPT).read_bytes())
    if digest(coverage) != receipt['output_sha256']:
        raise ValueError('sealed preflight coverage table changed')
    eligible = sorted(csv.DictReader(coverage.decode().splitlines()), key=lambda row: row['segment_id'])
    metadata = {row['segment_id']: row for row in study.input('eligible_metadata')['rows']}
    grouped = {entry['segment_id']: entry for entry in study.tasks.values()}
    groups = set()
    for imu, pick in zip(('8', '21'), selection['selected'], strict=True):
        expected = next(row for row in eligible if row['imu_type'] == imu
                        and row['l1_supported'] == row['dual_supported'] == row['selected_epochs']
                        and metadata[row['segment_id']]['group_id'] not in groups)
        segment = expected['segment_id']
        group = metadata[segment]['group_id']
        task = grouped[segment]
        if (pick['segment_id'] != segment or pick['group_id'] != group
                or pick['source_sha256'] != task['source_sha256'] or pick['identity'] != task['identity']):
            raise ValueError('position pilot no longer follows the fixed source selection')
        groups.add(group)
    return selection


def position_blocks(study, pick):
    """Stage the exact raw measurements for a verified receiver selection."""
    identity = pick['identity']
    task = study.tasks[identity]
    raw = gzip.decompress(study.input(task['input_key'], raw=True))
    position_bytes = study.input(task['position_key'], raw=True)
    if digest(raw) != task['receiver_sha256'] or digest(position_bytes) != task['position_sha256']:
        raise ValueError('sealed original-derived receiver bytes changed')
    epoch_bytes = study.artifact(identity, 'epochs.json.gz', raw=True)
    if digest(epoch_bytes) != pick['parent_epochs_sha256']:
        raise ValueError('sealed epoch ledger differs from selected source')
    epoch_rows = json.loads(gzip.decompress(epoch_bytes))
    tags = one_per_second([row['gps_millisecond_tag'] for row in epoch_rows])
    if tags != pick['gps_millisecond_tags'] or len(tags) > 750:
        raise ValueError('frozen GPS time selection differs')
    rows_by_tag = {row['gps_millisecond_tag']: row for row in epoch_rows}
    week, positioned = parent._selected_positions(position_bytes, task)
    full = _time_index(list(csv.DictReader(io.StringIO(gzip.decompress(position_bytes).decode()))))
    seed_tag = next(iter(full))
    seed = gps.ecef(*_geodetic(full[seed_tag])).tolist()
    decoded = parent.decode(raw, task['bounds'], week)
    matched, duplicates = parent.associate(decoded['records'], set(tags))
    coefficients = {tuple(row['alpha']+row['beta']) for row in decoded['ionosphere']}
    if (set(matched) != set(tags) or duplicates or len(coefficients) != 1
            or any(row['leap_seconds'] != task['leap_seconds'] for row in decoded['ionosphere'])):
        raise ValueError('record association or recorded ionospheric context changed')
    for tag in tags:
        ledger = rows_by_tag[tag]
        if (not all(ledger[method]['eligible'] for method in METHODS)
                or matched[tag]['payload_sha256'] != ledger['payload_sha256']):
            raise ValueError('range payload or recorded geometry disposition differs')
    for start in range(0, len(tags), BLOCK):
        part = tags[start:start+BLOCK]
        block = f'{identity}-{start//BLOCK:02d}'
        material = dict(source_identity=identity, source_sha256=pick['source_sha256'],
            imu_type=pick['imu_type'], segment_id=pick['segment_id'], seed_tag=seed_tag,
            seed_ecef_m=seed, ephemerides=decoded['ephemerides'], ionosphere=decoded['ionosphere'][0],
            records=[dict(tag=tag, measurement=matched[tag], reference=positioned[tag]) for tag in part])
        yield dict(identity=block, input_key='positions_'+block, source_identity=identity,
                   segment_id=pick['segment_id'], selected_tags=part,
                   position_starts=len(part)*len(METHODS),
                   limits=dict(native_calls=0, packet_visits=0, bound_calls=0, bound_steps=0)), material


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    root = Path(root).resolve()
    if (root/'data'/IDENTITY).exists():
        raise ValueError('already prepared; run or inspect the recorded allowance')
    inputs = dict(selection=SELECTION, preflight_receipt=PREFLIGHT_RECEIPT)
    tasks = []
    with closing(ClosedStudy(root, 'data/'+parent.IDENTITY)) as study:
        selection = _verified_selection(root, study)
        for pick in selection['selected']:
            for task, material in position_blocks(study, pick):
                path = f'data/{IDENTITY}-inputs/{task["identity"]}.json.gz'
                _write_equal(root/path, gzip.compress(encoded(material), mtime=0))
                inputs[task['input_key']] = path
                tasks.append(task)
    starts = sum(task['position_starts'] for task in tasks)
    if starts != selection['position_solve_starts']:
        raise ValueError('position start allowance does not match frozen selection')
    definition = dict(id=IDENTITY, scope='two frozen GPS-only position reconstructions; zero IMU fits',
        adapter=ADAPTER, inputs=inputs, tasks=tasks, workers=2, threads=1, maximum_wall_s=180.,
        sources=source_closure(root, (ADAPTER, PLAN, 'analysis/tests/test_ilvis0_gps_reconstruction_pilot.py')))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(study=IDENTITY, tasks=len(tasks), position_starts=starts, allocation=manifest['allocation'])


def evaluate(task, context):
    data = json.loads(gzip.decompress(context.input_path().read_bytes()))
    records = data['records']
    if (data['source_identity'] != task['source_identity'] or data['segment_id'] != task['segment_id']
            or [row['tag'] for row in records] != task['selected_tags']
            or task['position_starts'] != len(records)*len(METHODS)):
        raise ValueError('position start inventory differs from the frozen task')
    # Seal every position start against this task before its first solve.
    charge = context.save('position-charge.json', dict(
        methods=METHODS, gps_millisecond_tags=task['selected_tags'],
        charged_starts=task['position_starts'], maximum_iterations_per_start=MAX_ITERATIONS,
        seed_tag=data['seed_tag'], seed_ecef_m=data['seed_ecef_m']))
    results = []
    for record in records:
        if parent.tag(record['measurement']) != record['tag']:
            raise ValueError('raw GPS epoch differs from frozen position identity')
        for method in METHODS:
            solution = fit_epoch(record['measurement'], data['ephemerides'], data['ionosphere'],
                                 method, data['seed_ecef_m'])
            if solution.get('iterations', 0) > MAX_ITERATIONS:
                raise ValueError('position iteration ceiling exceeded')
            if solution['status'] == 'converged':
                solution['difference_neu_m'] = receiver_difference(solution['ecef_m'], record['reference']).tolist()
            solution.update(method=method, gps_millisecond_tag=record['tag'],
                            used_as_initialization=record['tag'] == data['seed_tag'],
                            measurement_sha256=record['measurement']['payload_sha256'])
            results.append(solution)
    artifact = context.save_bytes('positions.json.gz', gzip.compress(encoded(results), mtime=0))
    return dict(passed=True, source_identity=task['source_identity'], segment_id=task['segment_id'],
        position_starts=len(results), converged=sum(row['status'] == 'converged' for row in results),
        position_results=artifact, charge=charge, observed_fit_starts=0, scientific_decision='abstain')


if __name__ == '__main__':
    from .ilvis0_control_shards import launch
    from .studies.validation_resume import _other_threads

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    args = parser.parse_args()
    root = Path.cwd()
    report = (prepare(root) if args.action == 'prepare'
              else launch(root/'data'/IDENTITY, reserved_threads=_other_threads(root, 2)))
    print(json.dumps(report, sort_keys=True))
