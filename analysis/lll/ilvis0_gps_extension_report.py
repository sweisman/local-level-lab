# SPDX-License-Identifier: AGPL-3.0-or-later
"""Report the new receiver comparison from hash-checked position results."""

from collections import defaultdict
from contextlib import closing
import gzip
import json
from pathlib import Path

from . import ilvis0_gps_reconstruction_extension as extension
from .ilvis0_gps_reconstruction_pilot import FOLDER, MAX_ITERATIONS, METHODS, _write_equal, receiver_difference
from .ilvis0_gps_reconstruction_pilot_report import comparisons, _csv
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


def block_rows(study, task):
    import numpy as np

    identity = task['identity']
    envelope = study.envelope(identity)
    result = envelope['result']
    material = json.loads(gzip.decompress(study.input(task['input_key'], raw=True)))
    charge = study.artifact(identity, 'position-charge.json')
    positions = json.loads(gzip.decompress(study.artifact(identity, 'positions.json.gz', raw=True)))
    records = {row['tag']: row for row in material['records']}
    tags = task['selected_tags']
    starts = task['position_starts']
    if (list(records) != tags or [(r['gps_millisecond_tag'], r['method']) for r in positions] !=
            [(tag, method) for tag in tags for method in METHODS]
            or envelope['charged'] != extension.position_limits(starts)
            or not result['passed'] or result['observed_fit_starts'] != 0
            or result['position_starts'] != starts or charge['charged_starts'] != starts
            or charge['maximum_iterations_per_start'] != MAX_ITERATIONS or charge['methods'] != list(METHODS)
            or charge['gps_millisecond_tags'] != tags or charge['seed_tag'] != material['seed_tag']
            or charge['seed_ecef_m'] != material['seed_ecef_m']
            or result['converged'] != sum(row['status'] == 'converged' for row in positions)):
        raise ValueError('saved position starts, support or charges differ: '+identity)
    for row in positions:
        tag = row['gps_millisecond_tag']
        record = records[tag]
        difference = row.get('difference_neu_m')
        if (row['status'] not in ('converged', 'abstain') or row.get('iterations', 0) > MAX_ITERATIONS
                or row['measurement_sha256'] != record['measurement']['payload_sha256']
                or row['used_as_initialization'] != (tag == material['seed_tag'])
                or (row['status'] == 'converged') != (difference is not None)):
            raise ValueError('saved GPS disposition or measurement differs: '+identity)
        if difference is not None and not np.allclose(
                difference, receiver_difference(row['ecef_m'], record['reference']), rtol=0., atol=1e-12):
            raise ValueError('saved position comparison does not reproduce: '+identity)
        yield dict(segment_id=task['segment_id'], imu_type=material['imu_type'],
            method=row['method'], gps_millisecond_tag=tag, status=row['status'], reason=row.get('reason'),
            iterations=row.get('iterations'), used_as_initialization=row['used_as_initialization'],
            difference_neu_m=difference)


def build(root):
    grouped = defaultdict(list)
    with closing(ClosedStudy(root, 'data/'+extension.ID)) as study:
        if (not study.summary['passed'] or study.completion['state'] != 'complete'
                or study.manifest['scope'] != extension.SCOPE):
            raise ValueError('the complete sealed two-group receiver reconstruction is required')
        selection = study.input('selection', raw=True)
        if digest(selection) != extension.SELECTION_SHA:
            raise ValueError('the exact added receiver selection is required')
        selection = json.loads(selection)
        for task in study.tasks.values():
            for row in block_rows(study, task):
                grouped[row['segment_id'], row['method']].append(row)
        starts = selection['position_solve_starts']
        if sum(map(len, grouped.values())) != starts:
            raise ValueError('saved position results do not cover the frozen allowance')
        receipt = dict(study.completion, position_starts=starts, imu_fit_starts=0,
                       charged=study.summary['charged'], scientific_decision='abstain')
    rows, rates, summary = [], [], []
    for pick in selection['selected']:
        for method in METHODS:
            segment = pick['segment_id']
            selected = sorted(grouped.pop((segment, method)), key=lambda r: r['gps_millisecond_tag'])
            if [row['gps_millisecond_tag'] for row in selected] != pick['gps_millisecond_tags']:
                raise ValueError('the saved output omits or duplicates frozen GPS epochs')
            score, derivative_rows = comparisons(selected)
            keys = dict(segment_id=segment, group_id=pick['group_id'], imu_type=pick['imu_type'], method=method)
            summary.append(dict(keys, **score))
            rows.extend(selected)
            rates.extend(dict(keys, **row) for row in derivative_rows)
    if grouped:
        raise ValueError('unexpected receiver results outside the fixed selection')
    return dict(receipt, comparisons=summary), rows, rates


def publish(root):
    receipt, rows, rates = build(root)
    outputs = {
        'gps-reconstruction-extension-positions.csv': _csv(rows, (('difference_neu_m', 'difference_m'),)),
        'gps-reconstruction-extension-derivatives.csv': _csv(rates, (
            ('velocity_neu_mps', 'velocity_difference_mps'),
            ('acceleration_neu_mps2', 'acceleration_difference_mps2'))),
    }
    receipt.update(output_sha256={name: digest(raw) for name, raw in outputs.items()},
                   reporter_sha256=digest(Path(__file__).read_bytes()))
    outputs['gps-reconstruction-extension-receipt.json'] = encoded(receipt)
    for name, raw in outputs.items():
        _write_equal(root/FOLDER/name, raw)
    return receipt


if __name__ == '__main__':
    print(json.dumps(publish(Path.cwd()), sort_keys=True))
