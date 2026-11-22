# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite saved-receiver comparison of motion-window repeatability."""

import argparse
import csv
from dataclasses import asdict
import gzip
import hashlib
import io
import json
from pathlib import Path

from .ilvis0_receiver_support import SupportPolicy
from .ilvis0_receiver_support_inventory_study import policy
from .ilvis0_receiver_window_pairs import compare_pair


IDENTITY = 'ilvis0-receiver-window-pairs-20261114'
PARENT = 'data/ilvis0-receiver-overlap-20261110'


def definition(root):
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    root = Path(root).resolve()
    parent = ClosedStudy(root, PARENT)
    try:
        if (parent.completion['state'] != 'complete' or
                parent.summary['total'] != 11 or
                parent.summary['completed'] != 11 or
                parent.summary['passed'] is not True):
            raise ValueError('eleven passing sealed receiver overlap pairs required')
        inputs = {'parent_completion': PARENT+'/completion.json'}
        tasks = []
        fixed = asdict(policy())
        fixed['half_windows_s'] = list(fixed['half_windows_s'])
        for index, prior in enumerate(parent.manifest['tasks']):
            identity = prior['identity']
            if (parent.rows[identity]['passed'] is not True or
                    parent.rows[identity]['status'] != 'complete'):
                raise ValueError('closed receiver pair differs from selection')
            parent.envelope(identity)
            entry = dict(identity=identity, index=index, shard=0,
                         left_task=prior['left_task'],
                         right_task=prior['right_task'],
                         parent_manifest_sha256=parent.completion['manifest_sha256'],
                         parent_summary_sha256=parent.completion['summary_sha256'],
                         support_policy=fixed, minimum_matches=100,
                         target_spacing_s=10., edge_margin_s=15.,
                         limits=dict(native_calls=0, packet_visits=0,
                                     bound_calls=0, bound_steps=0))
            for side in ('left', 'right'):
                key = prior[side+'_key']
                record = parent.manifest['inputs'][key]
                if record['sha256'] != prior[side+'_sha256']:
                    raise ValueError('prior receiver table hash differs')
                inputs[key] = record['source']
                entry[side+'_key'] = key
                entry[side+'_sha256'] = record['sha256']
            entry['input_key'] = entry['left_key']
            tasks.append(entry)
        seeds = (
            'analysis/lll/ilvis0_receiver_window_pairs_study.py',
            'analysis/lll/ilvis0_receiver_window_pairs.py',
            'analysis/lll/ilvis0_receiver_support.py',
            'analysis/lll/ilvis0_receiver_overlap.py',
            'analysis/lll/ilvis0_receiver_support_inventory_study.py',
            'analysis/tests/test_ilvis0_receiver_window_pairs.py',
            'analysis/tests/test_ilvis0_receiver_window_pairs_study.py',
            'docs/ilvis0-receiver-window-pairs/PLAN.md')
        return dict(id=IDENTITY, scope='eleven sealed paired primary receiver '
                    'streams; fixed motion-window policy; no IMU or model fit',
                    adapter='analysis/lll/ilvis0_receiver_window_pairs_study.py',
                    sources=source_closure(root, seeds), inputs=inputs,
                    tasks=tasks, workers=1, threads=1, maximum_wall_s=300)
    finally:
        parent.close()


def prepare(root='.'):
    from .studies.artifacts import atomic, encoded
    from .studies.runtime import Definition

    root = Path(root).resolve()
    target = root/'docs/ilvis0-receiver-window-pairs/study-definition.json'
    data = definition(root)
    raw = encoded(data)
    if target.is_file() and target.read_bytes() != raw:
        raise ValueError('frozen receiver-pair definition differs')
    if not target.is_file():
        atomic(target, raw)
    manifest = Definition.from_dict(data, root).prepare(root)
    return dict(path='data/'+IDENTITY, tasks=len(data['tasks']),
                allocation=manifest['allocation'])


def _rows(context, task, side):
    key = task[side+'_key']
    blob = context.input_path(key).read_bytes()
    if hashlib.sha256(blob).hexdigest() != task[side+'_sha256']:
        raise ValueError('staged receiver table hash changed')
    return list(csv.DictReader(io.StringIO(
        gzip.decompress(blob).decode('utf-8'))))


def evaluate(task, context):
    completion = json.loads(context.input_path('parent_completion').read_bytes())
    fixed = asdict(policy())
    fixed['half_windows_s'] = list(fixed['half_windows_s'])
    if (completion['manifest_sha256'] != task['parent_manifest_sha256'] or
            completion['summary_sha256'] != task['parent_summary_sha256'] or
            task['support_policy'] != fixed):
        raise ValueError('parent or fixed receiver support policy differs')
    settings = dict(task['support_policy'])
    settings['half_windows_s'] = tuple(settings['half_windows_s'])
    result = compare_pair(
        _rows(context, task, 'left'), _rows(context, task, 'right'),
        policy=SupportPolicy(**settings),
        minimum_matches=task['minimum_matches'],
        target_spacing_s=task['target_spacing_s'],
        edge_margin_s=task['edge_margin_s'])
    result.update(pair_id=task['identity'],
                  left_task=task['left_task'], right_task=task['right_task'],
                  earth_model_fits=0, absolute_receiver_accuracy_established=False)
    artifact = context.save('pair-window-comparison.json', result)
    return dict(passed=True, pair_id=task['identity'],
                matched_epochs=result['matched_epochs'],
                targets=result['targets'], disagree=result['disagree'],
                result_artifact=artifact, earth_model_fits=0,
                imu_observations_used=False,
                scientific_decision='abstain')


def launch(root='.'):
    from .ilvis0_control_shards import launch as run_study
    from .studies.validation_resume import _other_threads

    root = Path(root).resolve()
    return run_study(root/'data'/IDENTITY,
                     reserved_threads=_other_threads(root, 1))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run'))
    parser.add_argument('--root', default='.')
    args = parser.parse_args(argv)
    result = prepare(args.root) if args.action == 'prepare' else launch(args.root)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
