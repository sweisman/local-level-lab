# SPDX-License-Identifier: AGPL-3.0-or-later
"""Full opened ESA PPP comparison after explicit printed-counter audit."""

import json
from pathlib import Path

from .esa_full_parallel_gnss import (AIR1, BASE, INVENTORY, WINDOWS, _fixed_windows,
                                     _sha, summarize_window_pairs)
from .esa_parallel_gnss import MATCH_TOLERANCE_S, match_times
from .esa_ppp_acquisition import TARGETS, verify_complete
from .esa_receiver_sequence_wrap import records_with_sequence_wrap

VERSION = 'esa-full-parallel-gnss-v2'
PLAN = 'docs/prediction-observed-development/FULL_PARALLEL_GNSS_V2_PLAN.md'
EXPECTED_ROLLOVERS = {'187_mosaic03_ppp_5Hz_final.txt': 1,
                      '187_pwrpak7_ppp_1Hz_final.txt': 0}


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
        receipt_path = base / (name + '.receipt.json')
        receipt = json.loads(receipt_path.read_bytes())
        digest = verify_complete(path, size, receipt)
        audit = {}
        with path.open() as stream:
            parsed = records_with_sequence_wrap(
                stream, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=audit)
            matched = match_times(reference, parsed)
            for _ in parsed:
                pass  # finish strict source and rollover validation
        summary = summarize_window_pairs(reference, matched, windows)
        sources.append(dict(filename=name, source_sha256=digest,
                            receipt_sha256=_sha(receipt_path),
                            sequence_audit=audit,
                            matched_epochs=sum(item['matched_epochs'] for item in summary),
                            windows=summary))
    return dict(version=VERSION, reference_file=AIR1,
                reference_sha256=inventory['sha256'],
                inventory_sha256=_sha(inventory_path),
                fixed_windows_sha256=_sha(windows_path),
                code_sha256=_sha(Path(__file__)),
                v1_code_sha256=_sha(Path(__file__).with_name('esa_full_parallel_gnss.py')),
                parser_sha256=_sha(Path(__file__).with_name('airquantumgrav_receiver.py')),
                wrap_helper_sha256=_sha(Path(__file__).with_name('esa_receiver_sequence_wrap.py')),
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
        raise ValueError('fresh v2 full parallel receiver result required')
    result = build(args.root)
    atomic(output, encoded(result))
    print(json.dumps([(item['filename'], item['matched_epochs'],
                       item['sequence_audit']) for item in result['sources']]))


if __name__ == '__main__':
    main()
