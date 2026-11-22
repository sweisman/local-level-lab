# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the earlier height-error correction on seven other NASA groups."""

from contextlib import closing
import csv
import io
import json
from pathlib import Path

from . import ilvis0_forecast_error_transfer as common


ID = 'ilvis0-height-error-transfer-v1-20261120'
SCOPE = 'Earlier-only height error correction on seven other retrospective NASA groups'
PLAN = common.BASE+'HEIGHT_TRANSFER_PLAN.md'
RESULT = common.BASE+'height-transfer.json'
DEVELOPMENT_SHA = '51874312089073be74e685fdcd6aebf147a0ff847e944cf64ad2ef22658f327e'
GROUP_LEDGER = 'docs/paper-development-dataset-v2/stretches.csv'
GROUP_LEDGER_SHA = '1a91390eb68ef870d7d88a71dd2386c091ccdb2bc656548e3ada6e7789732216'
PARENTS = (
    ('docs/prediction-rolling-origin/verified-report.json', 'ec3caf419124da3c76ef9846622a78c8a358de6a2de926f274fbd3391d182066', 3),
    (common.BASE+'verified-report.json', '8d7ae77be8d755896a94c521ff740edd2c88d55d2cb2a32d8014e912d818c101', 4),
)


def evaluate(task, context):
    return common.evaluate_pair(task,context,scope=SCOPE,height_only=True)


def prepare(root):
    from .studies.artifacts import atomic, digest
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('use the existing seven-group height correction freeze')
    raw = (root/common.RESULT).read_bytes()
    if digest(raw) != DEVELOPMENT_SHA:
        raise ValueError('exact earlier height-error development report required')
    used = {row['segment_id'] for row in json.loads(raw)['rows']}
    selection = (root/common.PARENT).read_bytes()
    if digest(selection) != common.PARENT_SHA:
        raise ValueError('exact earlier group selection required')
    group_raw = (root/GROUP_LEDGER).read_bytes()
    if digest(group_raw) != GROUP_LEDGER_SHA:
        raise ValueError('exact frozen group ledger required')
    group_rows = list(csv.DictReader(io.StringIO(group_raw.decode())))
    index_by_segment = {row['segment_id']:row['conservative_split_group'] for row in group_rows}
    early_groups = {row['segment_id']:row['group_id'] for row in json.loads(selection)['selection']}
    if (len(group_rows) != 53 or len(index_by_segment) != 53 or set(early_groups) != used
            or len(set(early_groups.values())) != 20
            or any(index_by_segment[s] != group for s,group in early_groups.items())):
        raise ValueError('twenty distinct earlier groups required')
    used_groups = set(early_groups.values())
    inputs = {'plan':PLAN, 'development':common.RESULT, 'development_selection':common.PARENT,
              'group_ledger':GROUP_LEDGER}
    segments = []
    staged = {}
    for index, (filename, expected, count) in enumerate(PARENTS):
        raw = (root/filename).read_bytes()
        if digest(raw) != expected:
            raise ValueError('sealed retrospective parent report differs')
        inputs[f'parent_{index}'] = filename
        report = json.loads(raw)
        rows = [row for row in report['rows'] if row['clock']=='header_elapsed' and not row['profile']]
        with closing(ClosedStudy(root,report['study'])) as study:
            if (len(rows) != count or len(study.tasks) != len(study.rows)
                    or any(study.completion[k] != report[k] for k in ('manifest_sha256','summary_sha256'))):
                raise ValueError('complete original forecast cohort required')
            paths, selected = common.extract_pairs(study,rows)
            groups = {index_by_segment[s] for s in selected}
            if len(groups) != count or used.intersection(selected) or used_groups.intersection(groups):
                raise ValueError('no repeated recording group from the development check')
            used.update(selected)
            used_groups.update(groups)
            segments.extend(selected)
            staged.update(paths)
    base.mkdir(parents=True)
    for key, raw in staged.items():
        path = base/(key+'.json')
        atomic(path,raw)
        inputs[key] = path.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[common.task_for(segment) for segment in segments], sources=source_closure(root,[adapter,PLAN]),
        workers=1, threads=1, maximum_wall_s=90.),root).prepare(root)
    print(json.dumps(dict(study=ID,limits=manifest['limits']),sort_keys=True))


def collect(root):
    common.collect_study(root,name=ID,output=RESULT,count=7,paired_count=3,height_only=True)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','collect'))
    args = parser.parse_args()
    {'prepare':prepare,'collect':collect}[args.action](Path.cwd())
