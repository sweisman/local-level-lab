# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed receiver cuts for the twenty unused NASA development groups."""

import csv
import gzip
import io
import json
from pathlib import Path

from .ilvis0_remaining_prediction_groups import build as select_groups

VERSION='ilvis0-remaining-prediction-layouts-v1'
POPULATION='data/ilvis0-highspeed-segments-v2-20261008/selection.json.gz'
CONTEXT='data/ilvis0-followup-20261007/summary.json'
OUTPUT='docs/prediction-group-transfer/remaining-layouts.json'


def validate(layouts,selection):
    if (len(layouts)!=20 or len(selection)!=20
            or [row['segment_id'] for row in layouts]
               !=[row['segment_id'] for row in selection]
            or len({row['group_id'] for row in layouts})!=20):
        raise ValueError('twenty unique saved prediction groups required')
    for row in layouts:
        n=row['receiver_epochs']
        cut=row['training_epochs']
        if (type(n) is not int or n<9 or type(cut) is not int
                or cut!=2*n//3 or row['prediction_epochs']!=n-cut):
            raise ValueError('unchanged two-thirds receiver cut required')
    return layouts


def build(root):
    from .ilvis0_prediction_layout import prediction_layout
    from .studies.artifacts import ArchiveStore,digest

    root=Path(root).resolve()
    selected=select_groups(root)
    saved_csv=(root/'docs/prediction-group-transfer/remaining-groups.csv').read_bytes()
    receipt=json.loads((root/'docs/prediction-group-transfer/remaining-groups-receipt.json').read_bytes())
    if (saved_csv!=selected['csv'] or receipt!=selected['receipt']):
        raise ValueError('unchanged metadata-only twenty-group selection required')
    selection=list(csv.DictReader(io.StringIO(saved_csv.decode())))
    store=ArchiveStore(root)
    try:
        population_raw=store.read(POPULATION)
        context_raw=store.read(CONTEXT)
    finally:
        store.close()
    population=json.loads(gzip.decompress(population_raw))
    sources={row['segment']['segment_id']:row for row in population['selected']}
    contexts={row['task_id']:row for row in json.loads(context_raw)['results']}
    layouts=[]
    for row in selection:
        source=sources[row['segment_id']]
        layouts.append(prediction_layout(row,source,contexts[source['task']]))
    validate(layouts,selection)
    return dict(version=VERSION,layouts=layouts,
        selection_sha256=digest(saved_csv),
        selection_receipt_sha256=digest((root/'docs/prediction-group-transfer/remaining-groups-receipt.json').read_bytes()),
        input_sha256={POPULATION:digest(population_raw),CONTEXT:digest(context_raw)},
        source_sha256=digest(Path(__file__).read_bytes()),
        layout_source_sha256=digest(Path(prediction_layout.__code__.co_filename).read_bytes()),
        original_reads=0,observed_starts=0,protected_esa_reads=0,
        scientific_decision='abstain')


def main(argv=None):
    import argparse
    from .studies.artifacts import atomic,encoded
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--output',default=OUTPUT)
    args=parser.parse_args(argv)
    output=Path(args.output)
    if output.exists():
        raise ValueError('fresh remaining-group layout receipt required')
    result=build(args.root)
    atomic(output,encoded(result))
    print(dict(groups=len(result['layouts']),
               selection_sha256=result['selection_sha256']))


if __name__=='__main__':main()
