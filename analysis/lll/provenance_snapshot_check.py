# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify the frozen provenance ledger after later findings-source changes."""

import csv
import io
import json
from pathlib import Path

from .evidence_groups import build
from .studies.artifacts import ArchiveStore, digest


LEDGER = 'docs/analysis-provenance/ledger.json'
RECEIPT = 'docs/analysis-provenance/provenance-receipt.json'
FINDINGS_RECEIPT = 'docs/ilvis0-current-findings-20261015/findings-receipt.json'
FINDINGS = 'docs/ilvis0-current-findings-20261015/'
TRAJECTORY_INPUTS = ('stretch-analytics.csv', 'shared-leg-pairs.csv')


def _checked(data, expected, name):
    if digest(data) != expected:
        raise ValueError('frozen provenance hash differs: ' + name)
    return data


def _rows(data):
    return list(csv.DictReader(io.StringIO(data.decode())))


def verify(root):
    """Check exact archived inputs and current grouping without rewriting them."""
    root = Path(root).resolve()
    store = ArchiveStore(root)
    try:
        catalog = store.catalog()
        read = lambda name: store._read(name, catalog)
        ledger = json.loads(read(LEDGER))
        receipt = json.loads(read(RECEIPT))
        if ledger['inputs'] != receipt['inputs']:
            raise ValueError('provenance input ledger and receipt differ')
        for name, sha in receipt['artifacts'].items():
            # The public guide has since been revised. Its receipt-bound bytes
            # are retained separately so the old receipt remains checkable.
            path = ('docs/analysis-provenance/receipt-README.md'
                    if name == 'README.md' else
                    'docs/analysis-provenance/' + name)
            _checked(read(path), sha, name)

        historical_sha = ledger['inputs'][FINDINGS_RECEIPT]
        historical = json.loads(_checked(
            store._object(historical_sha, catalog), historical_sha, FINDINGS_RECEIPT))
        current = json.loads(read(FINDINGS_RECEIPT))
        if historical['inputs'] != current['inputs']:
            raise ValueError('underlying findings input receipts changed')
        for name in TRAJECTORY_INPUTS:
            data = read(FINDINGS + name)
            _checked(data, historical['artifacts'][name], FINDINGS + name)
            _checked(data, current['artifacts'][name], FINDINGS + name)
        for name, sha in ledger['inputs'].items():
            if name != FINDINGS_RECEIPT:
                _checked(read(name), sha, name)

        source = build(
            _rows(read(FINDINGS + TRAJECTORY_INPUTS[0])),
            _rows(read(FINDINGS + TRAJECTORY_INPUTS[1])),
            _rows(read('docs/external-imu-data/esa-live-imu-files.csv')),
            json.loads(read('docs/external-imu-data/ESA_CONFIRMATION_POLICY.json')),
        )
        if source != {key: value for key, value in ledger.items() if key != 'inputs'}:
            raise ValueError('frozen provenance grouping differs from saved inputs')
        return dict(verified=True, records=len(ledger['records']),
                    conservative_groups=len(ledger['groups']),
                    historical_receipt_recovered=True,
                    current_receipt_differs=digest(read(FINDINGS_RECEIPT)) != historical_sha,
                    original_files_read=0, native_predictions=0)
    finally:
        store.close()


if __name__ == '__main__':
    print(json.dumps(verify('.'), sort_keys=True))
