# SPDX-License-Identifier: AGPL-3.0-or-later
"""Measure force sensitivity to the two receivers on each sealed survey leg."""

import argparse
import bisect
from collections import Counter
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

import numpy as np

from . import ilvis0_force_path_order as order
from . import ilvis0_receiver_window_pairs_study as parent
from .ilvis0_control_shards import runtime_environment
from .ilvis0_exact_axis_force_report import OUTPUT as GAP_RECEIPT
from .ilvis0_receiver_overlap import _time_index
from .ilvis0_receiver_force import evaluate
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy

FOLDER = order.FOLDER
PLAN = FOLDER+'PAIRED_RECEIVER_FORCE_PLAN.md'
FREEZE = FOLDER+'paired-receiver-force-freeze.json'
RECEIPT = FOLDER+'paired-receiver-force-receipt.json'
OUTPUT = FOLDER+'paired-receiver-force-windows.json.gz'
PARENT_RECEIPT = 'docs/ilvis0-receiver-window-pairs/receipt.json'
PAIR_COUNT = 11
TARGETS = 490
HALF = 15
MAX_GAP_MS = 1500
MODELS = order.average.MATCHED_MODELS


def matched_support(tags, target):
    lo, hi = target-1000*HALF, target+1000*HALF
    selected = tags[bisect.bisect_left(tags, lo):bisect.bisect_right(tags, hi)]
    if len(selected) < 5 or not selected[0] <= target <= selected[-1]:
        return None
    if max(np.diff([lo, *selected, hi])) > MAX_GAP_MS:
        return None
    return selected


def paired_window(offsets, left, right, quadrature=None):
    nodes, weights = (np.polynomial.legendre.leggauss(order.QUADRATURE)
                      if quadrature is None else quadrature)
    comparisons = []
    for degree in order.ORDERS:
        fits = [order.fit_path(offsets, source, degree=degree) for source in (left, right)]
        centers = [evaluate(*order.point_jet(fit, 0.), **order._settings('sphere_still'))
                   ['acceleration_ned_mps2'] for fit in fits]
        means = {model: [] for model in MODELS}
        for fit in fits:
            jets = [order.point_jet(fit, node*HALF) for node in nodes]
            for model in MODELS:
                vectors = [evaluate(*jet, **order._settings(model))['specific_force_ned_mps2'] for jet in jets]
                means[model].append(float(weights@np.linalg.norm(vectors, axis=1)/2.))
        comparisons.append(dict(degree=degree,
            center_acceleration_difference_neu_mps2=((centers[0]-centers[1])*[1, 1, -1]).tolist(),
            mean_force_difference_mps2={model: a-b for model, (a,b) in means.items()}))
    return comparisons


def _coordinates(rows, tags):
    values = np.array([[float(rows[tag][field]) for field in ('latitude_deg', 'longitude_deg', 'ellipsoid_height_m')]
                       for tag in tags])
    values[:, :2] = np.deg2rad(values[:, :2])
    values[:, 1] = np.unwrap(values[:, 1])
    return values


def load(root):
    parent_raw, gaps_raw = ((root/name).read_bytes() for name in (PARENT_RECEIPT, GAP_RECEIPT))
    reported, gaps = json.loads(parent_raw), json.loads(gaps_raw)
    sources = {PARENT_RECEIPT: digest(parent_raw), GAP_RECEIPT: digest(gaps_raw)}
    pairs = []
    with closing(ClosedStudy(root, 'data/'+parent.IDENTITY)) as study:
        expected_completion = dict(state='complete', manifest_sha256=reported['manifest_sha256'],
                                   summary_sha256=reported['summary_sha256'])
        if (study.completion != expected_completion
                or not study.summary['passed'] or len(study.tasks) != PAIR_COUNT
                or reported['aggregate']['targets'] != TARGETS or gaps['tasks'] != 32
                or gaps['navigation_fits'] or not all(row['passed'] for row in gaps['rows'])):
            raise ValueError('original paired receiver study and saved calibration gaps required')
        for identity, task in study.tasks.items():
            result = study.artifact(identity, 'pair-window-comparison.json')
            if (result['pair_id'] != identity or result['earth_model_fits']
                    or result['interpolated_measurements'] or result['imu_observations_used']
                    or len(result['target_details']) != result['targets']):
                raise ValueError('changed paired receiver-only selection')
            sources[identity+'/selection'] = study.envelope(identity)['artifacts'][
                f'artifacts/{identity}/pair-window-comparison.json']
            records = []
            for side in ('left', 'right'):
                key = task[side+'_key']
                raw = study.input(key, raw=True)
                hashed = digest(raw)
                if hashed != task[side+'_sha256']:
                    raise ValueError('changed paired receiver position table')
                sources[identity+'/'+side] = hashed
                records.append(_time_index(csv.DictReader(io.StringIO(gzip.decompress(raw).decode()))))
            tags = sorted(records[0].keys() & records[1].keys())
            if len(tags) != result['matched_epochs']:
                raise ValueError('changed exact GPS intersection')
            pairs.append((identity, tags, records, result['target_details']))
        completion = study.completion
    if sum(len(p[3]) for p in pairs) != TARGETS:
        raise ValueError('changed prior target count')
    return pairs, gaps, sources, completion


def build(pairs, calibration):
    quadrature = np.polynomial.legendre.leggauss(order.QUADRATURE)
    window_rows, summaries = [], []
    for identity, tags, (left, right), targets in pairs:
        rows = []
        for old in targets:
            target = round(old['target_gps_s']*1000)
            row = dict(pair=identity, target_gps_ms=target,
                       accepted_width_s=[old['left_half_window_s'], old['right_half_window_s']])
            support = matched_support(tags, target)
            if row['accepted_width_s'] != [HALF, HALF]:
                row['state'] = 'not_both_30_seconds'
            elif support is None:
                row['state'] = 'common_epoch_gap'
            else:
                row.update(state='compared', epochs=len(support), results=paired_window(
                    (np.asarray(support)-target)/1000., _coordinates(left, support),
                    _coordinates(right, support), quadrature))
            rows.append(row)
        valid = [row for row in rows if row['state']=='compared']
        statistics = []
        for index, degree in enumerate(order.ORDERS):
            records = [row['results'][index] for row in valid]
            if records:
                accel = np.array([r['center_acceleration_difference_neu_mps2'] for r in records])
                force = np.abs(np.array([[r['mean_force_difference_mps2'][m] for m in MODELS] for r in records]))
                statistics.append(dict(degree=degree,
                    center_acceleration_rms_neu_mps2=np.sqrt(np.mean(accel**2, axis=0)).tolist(),
                    p95_absolute_force_difference_mps2=np.percentile(force, 95., axis=0).tolist(),
                    maximum_absolute_force_difference_mps2=np.max(force, axis=0).tolist()))
        summaries.append(dict(pair=identity, targets=len(rows), compared=len(valid),
                              dispositions=dict(Counter(row['state'] for row in rows)), by_degree=statistics))
        window_rows.extend(rows)
    compared = sum(row['compared'] for row in summaries)
    gaps = {}
    for degree in order.ORDERS:
        gaps[str(degree)] = {}
        for side in ('training', 'later'):
            values = [r[side]['maximum_gap_mps2'] for r in calibration['rows'] if r['degree']==degree]
            gaps[str(degree)][side] = [min(values), max(values)]
    return window_rows, dict(targets=len(window_rows), compared=compared, summaries=summaries,
        force_means=compared*2*len(order.ORDERS)*len(MODELS),
        force_quadrature_evaluations=compared*2*len(order.ORDERS)*len(MODELS)*order.QUADRATURE,
        central_kinematic_evaluations=compared*2*len(order.ORDERS),
        pilot_calibration_gap_range_mps2=gaps, model_order=list(MODELS), position_solves=0,
        navigation_fits=0, scientific_decision='abstain')


def main():
    from .studies.dependencies import source_closure

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    args = parser.parse_args()
    root = Path.cwd()
    pairs, gaps, inputs, completion = load(root)
    own = Path(__file__).relative_to(root).as_posix()
    deps = source_closure(root, (own, PLAN, 'analysis/tests/test_ilvis0_paired_receiver_force.py'))
    config = encoded(dict(inputs=inputs, parent_completion=completion, environment=runtime_environment(),
        sources={p: digest((root/p).read_bytes()) for p in deps}, threads=1, targets=TARGETS,
        max_force_quadrature_evaluations=62720, max_central_kinematic_evaluations=1960, position_solves=0))
    if args.action == 'freeze':
        order.SUPPORT._write_equal(root/FREEZE, config)
        print(digest(config))
        return
    if (root/FREEZE).read_bytes() != config:
        raise ValueError('changed paired receiver force freeze')
    windows, result = build(pairs, gaps)
    payload = gzip.compress(encoded(windows), mtime=0)
    result.update(freeze_sha256=digest(config), output_sha256=digest(payload))
    order.SUPPORT._write_equal(root/OUTPUT, payload)
    order.SUPPORT._write_equal(root/RECEIPT, encoded(result))
    print(json.dumps({k: v for k, v in result.items() if k!='summaries'}, sort_keys=True))


if __name__ == '__main__':
    main()
