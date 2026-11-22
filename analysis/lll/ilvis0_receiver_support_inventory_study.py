# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen GNSS-only local-window inventory for the 53 selected ILVIS0 stretches."""

import csv
from dataclasses import asdict
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

from .ilvis0_receiver_support import (
    SupportPolicy, motion_from_enhanced_positions, select_support)


IDENTITY = 'ilvis0-receiver-support-inventory-20261113'
SOURCE = 'primary_receiver_enhanced_position'
PARENT = 'data/ilvis0-receiver-gap-inventory-20261113'
TARGET_SPACING_S = 10.
EDGE_MARGIN_S = 15.


def policy():
    """The receiver-only development rule fixed in the public plan."""
    return SupportPolicy(
        half_windows_s=(5., 10., 15.), maximum_gap_s=1.5,
        minimum_samples=5, minimum_speed_mps=190.,
        maximum_speed_mps=350., maximum_course_span_deg=1.5,
        maximum_speed_span_mps=10., maximum_vertical_rate_span_mps=1.)


def inventory_block(rows, policy, *, target_spacing_s, edge_margin_s):
    """Preserve every candidate window at fixed receiver-only target times."""
    if (not isinstance(policy, SupportPolicy) or
            not math.isfinite(target_spacing_s) or target_spacing_s <= 0. or
            not math.isfinite(edge_margin_s) or edge_margin_s < 0.):
        raise ValueError('fixed support policy, spacing and edge margin required')
    motion = motion_from_enhanced_positions(
        rows, maximum_gap_s=policy.maximum_gap_s)
    times = motion['times_s']
    available = times[-1]-times[0]-2.*edge_margin_s
    count = max(0, math.floor((available+1e-9)/target_spacing_s)+1)
    targets = [select_support(
        times, motion['speed_mps'], motion['course_deg'],
        motion['vertical_rate_mps'],
        target_s=times[0]+edge_margin_s+index*target_spacing_s,
        policy=policy) for index in range(count)]
    return dict(source=SOURCE, motion_version=motion['version'],
                first_receiver_gps_s=times[0], last_receiver_gps_s=times[-1],
                receiver_positions=len(times),
                target_spacing_s=float(target_spacing_s),
                edge_margin_s=float(edge_margin_s),
                targets=targets,
                supported_targets=sum(row['selected_indices'] is not None
                                      for row in targets),
                scientific_decision='abstain',
                imu_observations_used=False, fused_navigation_used=False)


def write_definition(root='.'):
    """Bind all 53 prior outcomes and the 52 hash-checked receiver tables."""
    from .studies.artifacts import atomic, encoded
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure

    root = Path(root).resolve()
    parent = ClosedStudy(root, PARENT)
    try:
        if (parent.summary['total'] != 53 or parent.summary['completed'] != 53 or
                sum(row['passed'] for row in parent.rows.values()) != 52):
            raise ValueError('closed 53-stretch receiver-gap inventory required')
        inputs = {'parent_completion':PARENT+'/completion.json',
                  'parent_summary':PARENT+'/summary.json'}
        segments = []
        for old in sorted(parent.tasks.values(), key=lambda row: row['index']):
            saved = parent.artifact(old['identity'], 'summary.json')
            segment = dict(segment_id=old['identity'], filename=old['filename'],
                           source_sha256=old['source_sha256'],
                           gap_inventory_passed=saved['passed'])
            if saved['passed']:
                blocks = saved['block_inventory']['blocks']
                if (len(blocks) != 1 or not blocks[0]['accepted'] or
                        saved['accepted_blocks'] != 1 or
                        saved['block_inventory']['gaps']):
                    raise ValueError('prior receiver block inventory differs')
                key = 'positions_'+old['source_task']
                record = parent.manifest['inputs'][old['input_key']]
                if record['sha256'] != old['table_sha256']:
                    raise ValueError('prior position table hash differs')
                inputs[key] = record['source']
                segment.update(input_key=key,
                               table_sha256=record['sha256'],
                               first_table_row=blocks[0]['first_table_row'],
                               last_table_row=blocks[0]['last_table_row'])
            else:
                if saved['reason'] != 'prior_receiver_decoder_failure':
                    raise ValueError('unrecognized prior receiver failure')
                segment['reason'] = saved['reason']
            segments.append(segment)
        if len(segments) != 53 or sum(row['gap_inventory_passed']
                                      for row in segments) != 52:
            raise ValueError('prior receiver cohort differs')
        adapter = 'analysis/lll/ilvis0_receiver_support_inventory_study.py'
        seeds = (adapter, 'analysis/lll/ilvis0_receiver_support.py',
                 'analysis/tests/test_ilvis0_receiver_support_inventory_study.py',
                 'docs/ilvis0-receiver-support-inventory/PLAN.md')
        task = dict(identity='receiver-support-all-53', shard=0,
                    input_key='parent_completion', segments=segments,
                    parent_manifest_sha256=parent.completion['manifest_sha256'],
                    support_policy=asdict(policy()),
                    target_spacing_s=TARGET_SPACING_S,
                    edge_margin_s=EDGE_MARGIN_S,
                    limits=dict(native_calls=0, packet_visits=0,
                                bound_calls=0, bound_steps=0))
        definition = dict(id=IDENTITY,
            scope='53 preselected stretches; receiver-only enhanced-position '
                  'support; zero IMU reads and model fits',
            adapter=adapter, sources=source_closure(root, seeds),
            inputs=inputs, tasks=[task], workers=1, threads=1,
            maximum_wall_s=300)
        target = root/'docs/ilvis0-receiver-support-inventory/study-definition.json'
        raw = encoded(definition)
        if target.is_file():
            if target.read_bytes() != raw:
                raise ValueError('frozen receiver-support definition differs')
        else:
            atomic(target, raw)
        return definition
    finally:
        parent.close()


def evaluate(task, context):
    """Use only staged primary-receiver rows and the frozen support policy."""
    completion = json.loads(context.input_path('parent_completion').read_bytes())
    if completion['manifest_sha256'] != task['parent_manifest_sha256']:
        raise ValueError('parent receiver inventory hash changed')
    settings = dict(task['support_policy'])
    settings['half_windows_s'] = tuple(settings['half_windows_s'])
    fixed_policy = SupportPolicy(**settings)
    details = []
    for item in task['segments']:
        if not item['gap_inventory_passed']:
            details.append(dict(segment_id=item['segment_id'],
                                filename=item['filename'],
                                disposition='abstain', reason=item['reason'],
                                receiver_targets=0, supported_targets=0))
            continue
        blob = context.input_path(item['input_key']).read_bytes()
        if hashlib.sha256(blob).hexdigest() != item['table_sha256']:
            raise ValueError('staged enhanced-position table hash changed')
        rows = list(csv.DictReader(io.StringIO(gzip.decompress(blob).decode('utf-8'))))
        first, last = item['first_table_row'], item['last_table_row']
        if not 0 <= first <= last < len(rows):
            raise ValueError('saved receiver block rows outside table')
        result = inventory_block(
            rows[first:last+1], fixed_policy,
            target_spacing_s=task['target_spacing_s'],
            edge_margin_s=task['edge_margin_s'])
        details.append(dict(segment_id=item['segment_id'],
                            filename=item['filename'],
                            disposition='screened',
                            first_table_row=first, last_table_row=last,
                            receiver_targets=len(result['targets']),
                            supported_targets=result['supported_targets'],
                            support=result))
    if len(details) != 53 or sum(row['disposition'] == 'screened'
                                 for row in details) != 52:
        raise ValueError('receiver support did not preserve full cohort')
    artifact = context.save('support-windows.json', dict(
        version='ilvis0-receiver-support-inventory-v1',
        policy=asdict(fixed_policy), segments=details,
        receiver_only=True, scientific_decision='abstain'))
    return dict(passed=True, stretches=53, screened=52,
                prior_decoder_abstentions=1,
                receiver_targets=sum(row['receiver_targets'] for row in details),
                supported_targets=sum(row['supported_targets'] for row in details),
                result_artifact=artifact, imu_observations_used=False,
                earth_model_fits=0, scientific_decision='abstain')
