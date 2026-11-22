# SPDX-License-Identifier: AGPL-3.0-or-later
"""Source-bound 120-second parallel-PPP difference audit on opened ESA data."""

import json
import math
from pathlib import Path

from .esa_full_parallel_gnss import AIR1, BASE, INVENTORY, _sha
from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
from .esa_parallel_gnss import MATCH_TOLERANCE_S, _axis_summary, match_times
from .esa_parallel_gnss_time import corrected_neu
from .esa_ppp_acquisition import TARGETS, verify_complete
from .esa_receiver_sequence_wrap import records_with_sequence_wrap

VERSION = 'esa-parallel-gnss-120s-v1'
FULL = 'docs/prediction-observed-development/full-parallel-gnss-v2-result.json'
PLAN = 'docs/prediction-observed-development/PARALLEL_GNSS_120S_PLAN.md'
WIDTH_S = 120
FAST_MIN_MPS = 50.
FAST_FRACTION = .9
MIN_MATCHES = 80


def window_id(time_s):
    if not math.isfinite(time_s) or time_s < 0:
        raise ValueError('finite nonnegative GPS-week time required')
    return int(math.floor(time_s/WIDTH_S))


def _window_summary(rows):
    if not rows or any(len(row) != 3 for row in rows):
        raise ValueError('nonempty complete matched window required')
    pairs = [row[2] for row in rows]
    fast = sum(row[1] for row in rows)
    first, last = pairs[0], pairs[-1]
    return dict(matched_epochs=len(rows), fast_epochs=fast,
        fast_fraction=fast/len(rows), fast_window=fast/len(rows)>=FAST_FRACTION
        and len(rows)>=MIN_MATCHES,
        first_time_s=rows[0][0], last_time_s=rows[-1][0],
        time_adjusted=_axis_summary(pairs),
        end_minus_start_m=[b-a for a,b in zip(first,last,strict=True)])


def summarize_windows(reference, matched):
    if not reference:
        raise ValueError('complete reference required')
    windows = {}
    previous = -1
    for index, other in matched:
        if type(index) is not int or index <= previous or index >= len(reference):
            raise ValueError('unique ordered reference match required')
        previous = index
        row = reference[index]
        if abs(other['time_s']-row['time_s']) > MATCH_TOLERANCE_S:
            raise ValueError('matched times exceed frozen tolerance')
        _, adjusted = corrected_neu(row, other)
        speed = math.hypot(row['north_mps'], row['east_mps'])
        key = window_id(row['time_s'])
        windows.setdefault(key, []).append((row['time_s'], speed>=FAST_MIN_MPS, adjusted))
    result = [dict(window_id=key, start_time_s=key*WIDTH_S,
                   end_time_s=(key+1)*WIDTH_S, **_window_summary(rows))
              for key, rows in sorted(windows.items())]
    if sum(row['matched_epochs'] for row in result) != len(matched):
        raise ValueError('not every matched receiver pair was retained')
    return result


def _quantile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[int(math.ceil(fraction*len(ordered)))-1]


def summarize_fast(windows):
    selected = [row for row in windows if row['fast_window']]
    fields = {}
    for name in ('rms', 'centered_rms'):
        values = [row['time_adjusted'][name] for row in selected]
        fields[name] = dict(median=[_quantile([v[i] for v in values], .5) for i in range(3)],
                            p95=[_quantile([v[i] for v in values], .95) for i in range(3)],
                            maximum=[max((v[i] for v in values),default=None)
                                     for i in range(3)])
    return dict(fast_windows=len(selected), matched_epochs=sum(row['matched_epochs']
                for row in selected), **fields)


def build(root):
    from .airquantumgrav_receiver import records
    root = Path(root).resolve()
    base = root/BASE
    inventory = json.loads((root/INVENTORY).read_bytes())
    full = json.loads((root/FULL).read_bytes())
    if (inventory.get('source_file') != AIR1 or inventory.get('epochs') != 64080
            or full.get('version') != 'esa-full-parallel-gnss-v2'
            or full.get('reference_sha256') != inventory.get('sha256')
            or full.get('protected_group_reads') != 0):
        raise ValueError('verified opened full-flight receiver source required')
    path = base/AIR1
    if _sha(path) != inventory['sha256']:
        raise ValueError('air1 source differs from inventory')
    with path.open() as stream:
        reference = list(records(stream))
    sources = []
    for name, size in TARGETS.items():
        target = base/name
        receipt = json.loads((base/(name+'.receipt.json')).read_bytes())
        digest = verify_complete(target, size, receipt)
        original = next(item for item in full['sources'] if item['filename']==name)
        if digest != original['source_sha256']:
            raise ValueError('parallel source differs from completed full audit')
        sequence_audit = {}
        with target.open() as stream:
            parsed = records_with_sequence_wrap(stream,
                expected_rollovers=EXPECTED_ROLLOVERS[name], audit=sequence_audit)
            matched = match_times(reference, parsed)
            for _ in parsed:
                pass
        if (sequence_audit != original['sequence_audit']
                or len(matched) != original['matched_epochs']):
            raise ValueError('full-flight pair count or sequence audit differs')
        windows = summarize_windows(reference, matched)
        sources.append(dict(filename=name, source_sha256=digest,
            matched_epochs=len(matched), windows=windows,
            fast_summary=summarize_fast(windows)))
    return dict(version=VERSION, plan_sha256=_sha(root/PLAN),
        code_sha256=_sha(Path(__file__)), reference_sha256=inventory['sha256'],
        full_result_sha256=_sha(root/FULL), window_width_s=WIDTH_S,
        fast_min_horizontal_mps=FAST_MIN_MPS, fast_fraction_min=FAST_FRACTION,
        min_matches=MIN_MATCHES, sources=sources, uses_imu=False,
        uses_model_fits=False, protected_group_reads=0,
        absolute_accuracy_established=False, aircraft_error_law_qualified=False,
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic, encoded
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    output = Path(args.output)
    if output.exists():
        raise ValueError('fresh 120-second receiver result required')
    result = build(args.root)
    atomic(output, encoded(result))
    print([(row['filename'], row['fast_summary']) for row in result['sources']])


if __name__ == '__main__':
    main()
