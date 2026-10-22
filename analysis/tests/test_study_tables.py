# SPDX-License-Identifier: AGPL-3.0-or-later
import csv
from pathlib import Path
from lll.studies.tables import stretch_table


def test_public_table_uses_all_verified_csv_records():
    root=Path(__file__).resolve().parents[2]
    with (root/'docs/ilvis0-current-findings-20261015/stretch-analytics.csv').open() as stream:rows=list(csv.DictReader(stream))
    table=stretch_table(rows)
    assert len(rows)==53 and len(table.splitlines())==55
    for row in rows:assert row['segment_id'] in table and row['filename'] in table
    assert table.count('Globe preferred')==53
