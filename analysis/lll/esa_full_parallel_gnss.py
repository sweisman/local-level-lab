# SPDX-License-Identifier: AGPL-3.0-or-later
"""Eight fixed-window relative checks across three opened ESA PPP streams."""

import hashlib
import json
import math
from pathlib import Path

from .esa_parallel_gnss import MATCH_TOLERANCE_S, match_times
from .esa_parallel_gnss_time import axis_summary, corrected_neu
from .esa_ppp_acquisition import TARGETS, verify_complete

VERSION = 'esa-full-parallel-gnss-v1'
BASE = 'data/external-imu-survey-20261018/esa-sample'
AIR1 = '187_air1_ppp_2Hz_final.txt'
INVENTORY = 'docs/external-imu-data/esa-gnss-report.json'
WINDOWS = 'docs/prediction-observed-development/full-receiver-consistency-result.json'
PLAN = 'docs/prediction-observed-development/FULL_PARALLEL_GNSS_PLAN.md'


def _sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_window_pairs(reference, matched, windows):
    """Keep every fixed window, including one with no exact-time matches."""
    if (not reference or not windows or windows[0][0] != 0
            or windows[-1][1] != len(reference)
            or any(type(start) is not int or type(end) is not int
                   or start >= end or (i and start != windows[i-1][1])
                   for i, (start, end) in enumerate(windows))):
        raise ValueError('fixed windows must cover reference once in order')
    matched = list(matched)
    indices = [index for index, _ in matched]
    if any(type(index) is not int or not 0 <= index < len(reference)
           for index in indices) or any(a >= b for a, b in zip(indices, indices[1:])):
        raise ValueError('unique ordered matched reference indices required')
    result = []
    cursor = 0
    for start, end in windows:
        pairs = []
        while cursor < len(matched) and matched[cursor][0] < end:
            index, other = matched[cursor]
            dt = other['time_s'] - reference[index]['time_s']
            if not math.isfinite(dt) or abs(dt) > MATCH_TOLERANCE_S:
                raise ValueError('matched receiver time exceeds frozen tolerance')
            raw, adjusted = corrected_neu(reference[index], other)
            pairs.append((dt, raw, adjusted))
            cursor += 1
        result.append(dict(reference_index_range=[start, end],
                           matched_epochs=len(pairs),
                           maximum_absolute_offset_s=max((abs(p[0]) for p in pairs),
                                                         default=None),
                           raw=axis_summary([p[1] for p in pairs]) if pairs else None,
                           time_adjusted=axis_summary([p[2] for p in pairs])
                           if pairs else None))
    return result


def _fixed_windows(reference, saved):
    if len(reference) != 64080 or saved.get('reports') != 64080:
        raise ValueError('exact full opened ESA reference required')
    result = []
    for index, item in enumerate(saved['windows']):
        start, end = index * 8010, (index + 1) * 8010
        if (item['window'] != index + 1 or item['reports'] != 8010
                or reference[start]['sequence'] != item['first_sequence']
                or reference[end - 1]['sequence'] != item['last_sequence']
                or reference[start]['time_s'] != item['first_time_s']
                or reference[end - 1]['time_s'] != item['last_time_s']):
            raise ValueError('full receiver audit window changed')
        result.append((start, end))
    if len(result) != 8:
        raise ValueError('eight frozen receiver windows required')
    return result


def build(root):
    from .airquantumgrav_receiver import records

    root = Path(root).resolve()
    base, inventory_path, windows_path = root / BASE, root / INVENTORY, root / WINDOWS
    inventory = json.loads(inventory_path.read_bytes())
    saved = json.loads(windows_path.read_bytes())
    if (inventory.get('source_file') != AIR1 or inventory.get('epochs') != 64080
            or saved.get('source_sha256') != inventory.get('sha256')
            or saved.get('uses_imu') is not False
            or saved.get('uses_model_fits') is not False):
        raise ValueError('source-bound full opened receiver audit required')
    air1_path = base / AIR1
    if _sha(air1_path) != inventory['sha256']:
        raise ValueError('opened air1 PPP source changed')
    with air1_path.open() as stream:
        reference = list(records(stream))
    windows = _fixed_windows(reference, saved)
    sources = []
    for name, size in TARGETS.items():
        path = base / name
        receipt = json.loads((base / (name + '.receipt.json')).read_bytes())
        digest = verify_complete(path, size, receipt)
        with path.open() as stream:
            parsed = records(stream)
            matched = match_times(reference, parsed)
            for _ in parsed:
                pass  # retain strict validation of any trailing reports
        summary = summarize_window_pairs(reference, matched, windows)
        sources.append(dict(filename=name, source_sha256=digest,
                            receipt_sha256=_sha(base / (name + '.receipt.json')),
                            matched_epochs=sum(item['matched_epochs'] for item in summary),
                            windows=summary))
    return dict(version=VERSION, reference_file=AIR1,
                reference_sha256=inventory['sha256'],
                inventory_sha256=_sha(inventory_path),
                fixed_windows_sha256=_sha(windows_path),
                source_sha256=_sha(Path(__file__)),
                parser_sha256=_sha(Path(__file__).with_name('airquantumgrav_receiver.py')),
                time_comparison_sha256=_sha(Path(__file__).with_name('esa_parallel_gnss_time.py')),
                matching_sha256=_sha(Path(__file__).with_name('esa_parallel_gnss.py')),
                plan_sha256=_sha(root / PLAN),
                reference_reports=len(reference), match_tolerance_s=MATCH_TOLERANCE_S,
                sources=sources, receiver_shared_antenna=True, uses_imu=False,
                uses_model_fits=False, protected_group_reads=0,
                absolute_position_accuracy_established=False,
                aircraft_error_law_qualified=False, scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh full parallel receiver result required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps([(item['filename'], item['matched_epochs'])
                      for item in result['sources']]))


if __name__ == '__main__':
    main()
