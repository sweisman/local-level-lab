# SPDX-License-Identifier: AGPL-3.0-or-later
"""Time-scale variation of unadjusted iMAR rates in fixed ground stops."""

import hashlib
import json
import math
from pathlib import Path

from .esa_ground_imu_rate import DEG_PER_HOUR

VERSION = 'esa-ground-rate-scales-v1'
SOURCE = 'data/external-imu-survey-20261018/esa-sample/187_rqh01.txt'
INVENTORY = 'docs/external-imu-data/esa-sample-report.json'
FIRST = 'docs/prediction-observed-development/ground-imu-rate-result.json'
SECOND = 'docs/prediction-observed-development/second-ground-imu-result.json'
PLAN = 'docs/prediction-observed-development/GROUND_RATE_SCALE_PLAN.md'


def summarize_scales(rows, *, windows, widths=(1, 10, 60), rate_hz=300):
    """Describe logged rates; a low-speed receiver never certifies zero yaw."""
    if (not windows or not all(type(w) is int and w > 0 for w in widths)
            or len(set(widths)) != len(widths) or rate_hz <= 0):
        raise ValueError('positive unique bin width and nominal rate required')
    ordered = sorted(windows.items(), key=lambda item: item[1][0])
    previous_end = -math.inf
    for label, bounds in ordered:
        if (not isinstance(label, str) or len(bounds) != 2
                or not all(math.isfinite(v) for v in bounds)
                or bounds[0] >= bounds[1]):
            raise ValueError('ordered finite ground windows required')
        if bounds[0] <= previous_end:
            raise ValueError('overlapping ground windows')
        previous_end = bounds[1]
    state = {label: dict(previous=None, samples=0,
                         bins={width: {} for width in widths})
             for label, _ in ordered}
    next_window = 0
    for row in rows:
        time = row['gps_time_s']
        while next_window < len(ordered) and time > ordered[next_window][1][1]:
            next_window += 1
        if next_window == len(ordered) or time < ordered[next_window][1][0]:
            continue
        label, (start, _) = ordered[next_window]
        current = state[label]
        previous = current['previous']
        if previous is not None and (time <= previous or time - previous > 1.5 / rate_hz
                                     or row['gap_above_1p5_nominal_periods']):
            raise ValueError('IMU time reversal or gap inside selected ground stop')
        rate = row['angular_rate_rads']
        if len(rate) != 3 or not all(math.isfinite(value) for value in rate):
            raise ValueError('finite complete instrument-axis rate required')
        current['previous'] = time
        current['samples'] += 1
        for width in widths:
            index = math.floor((time - start) / width)
            bucket = current['bins'][width].setdefault(index, [0, 0., 0., 0.])
            bucket[0] += 1
            for axis in range(3):
                bucket[axis + 1] += rate[axis]
    result = {}
    for label, current in state.items():
        result[label] = {}
        for width in widths:
            threshold = math.ceil(.95 * rate_hz * width)
            complete = []
            for index, bucket in sorted(current['bins'][width].items()):
                if bucket[0] >= threshold:
                    complete.append(dict(index=index, count=bucket[0],
                                         mean_xyz_deg_per_hour=[
                                             DEG_PER_HOUR * bucket[axis + 1] / bucket[0]
                                             for axis in range(3)]))
            if not complete:
                raise ValueError('no complete ground rate bins at requested width')
            mean = [sum(b['mean_xyz_deg_per_hour'][axis] for b in complete) / len(complete)
                    for axis in range(3)]
            spread = [math.sqrt(sum((b['mean_xyz_deg_per_hour'][axis] - mean[axis]) ** 2
                                    for b in complete) / len(complete))
                      for axis in range(3)]
            pairs = [(left, right) for left, right in zip(complete, complete[1:])
                     if right['index'] == left['index'] + 1]
            allan = [math.sqrt(sum((right['mean_xyz_deg_per_hour'][axis] -
                                    left['mean_xyz_deg_per_hour'][axis]) ** 2
                                   for left, right in pairs) / (2 * len(pairs)))
                     for axis in range(3)] if pairs else [None, None, None]
            result[label][str(width)] = dict(
                selected_samples=current['samples'], complete_bins=len(complete),
                omitted_partial_bins=len(current['bins'][width]) - len(complete),
                adjacent_complete_pairs=len(pairs),
                mean_xyz_deg_per_hour=mean, spread_xyz_deg_per_hour=spread,
                allan_xyz_deg_per_hour=allan, complete_bin_means=complete)
    return result


def _sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _check_minute_replay(scales, previous):
    saved = [minute for minute in previous['minute_means']
             if minute['count'] >= math.ceil(.95 * 300 * 60)]
    current = scales['60']['complete_bin_means']
    if len(saved) != len(current):
        raise ValueError('ground minute-bin replay count differs')
    for old, new in zip(saved, current):
        if (old['index'] != new['index'] or old['count'] != new['count']
                or any(abs(a - b) > 1e-7 for a, b in zip(
                    old['mean_rate_xyz_deg_per_hour'],
                    new['mean_xyz_deg_per_hour']))):
            raise ValueError('ground minute-bin replay differs')


def build(root):
    from .airquantumgrav import records

    root = Path(root).resolve()
    source, inventory_path = root / SOURCE, root / INVENTORY
    first_path, second_path = root / FIRST, root / SECOND
    inventory = json.loads(inventory_path.read_bytes())
    first, second = json.loads(first_path.read_bytes()), json.loads(second_path.read_bytes())
    parser_sha = _sha(Path(__file__).with_name('airquantumgrav.py'))
    if (inventory.get('source_file') != source.name
            or inventory.get('records') != 9168819
            or first.get('source_sha256') != inventory.get('source_sha256')
            or second.get('source_sha256') != inventory.get('source_sha256')
            or first.get('parser_sha256') != parser_sha
            or second.get('parser_sha256') != parser_sha
            or first.get('uses_model_fits') is not False
            or second.get('uses_model_fits') is not False):
        raise ValueError('two source-bound opened-development ground controls required')
    if _sha(source) != inventory['source_sha256']:
        raise ValueError('original iMAR source hash changed')
    windows = {'first': first['imu_overlap_time_s'],
               'second': second['second_imu_time_s']}
    with source.open('rb') as stream:
        scales = summarize_scales(records(stream), windows=windows)
    for label, prior in [('first', first['raw_imu']),
                         ('second', second['second_raw_imu'])]:
        if scales[label]['1']['selected_samples'] != prior['samples']:
            raise ValueError('ground overlap sample count differs')
        _check_minute_replay(scales[label], prior)
    return dict(version=VERSION, source_file=SOURCE,
                source_sha256=inventory['source_sha256'],
                inventory_sha256=_sha(inventory_path), first_result_sha256=_sha(first_path),
                second_result_sha256=_sha(second_path), parser_sha256=parser_sha,
                code_sha256=_sha(Path(__file__)), plan_sha256=_sha(root / PLAN),
                windows=windows, nominal_rate_hz=300, bin_widths_s=[1, 10, 60],
                complete_bin_fraction=.95, scales=scales, uses_model_fits=False,
                protected_group_reads=0, sensor_noise_identified=False,
                background_field_inferred=False, scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    target = Path(args.output)
    if target.exists():
        raise ValueError('fresh ground rate-scale result required')
    result = build(args.root)
    atomic(target, encoded(result))
    print(json.dumps({label: {width: {key: value for key, value in detail.items()
                                      if key in ('complete_bins', 'allan_xyz_deg_per_hour')}
                              for width, detail in scales.items()}
                      for label, scales in result['scales'].items()}))


if __name__ == '__main__':
    main()
