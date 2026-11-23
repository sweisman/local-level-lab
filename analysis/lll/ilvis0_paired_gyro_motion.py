# SPDX-License-Identifier: AGPL-3.0-or-later
"""Summarize recorded motion on the sealed 2009 paired-recorder overlap."""

from contextlib import closing
from hashlib import file_digest
import json
from pathlib import Path

from . import ilvis0_paired_gyro_clock as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded, safe_path


ID = 'ilvis0-paired-gyro-motion-v1'
SCOPE = 'Recorded angular travel in an existing mixed IMU8 and IMU21 NASA overlap'
PLAN = parent.FOLDER+'PAIRED_GYRO_MOTION_PLAN.md'
PARENT_SHA = 'bdf0ddc98d184644cc92b40298ee6a26d95125fed4ff5a2db8d8e054ad1138be'
LEG = 'leg-13805a9a35c4'
TASK = dict(identity=LEG, input_key='layout', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=6, bound_steps=6*parent.MAX_PACKETS))


def summaries(ends, durations, increments, overlap_s, angle_scale):
    import numpy as np

    packet = parent.PacketRates(ends, durations, increments)
    durations = np.asarray(durations)
    angle = np.linalg.norm(increments, axis=1)
    fully_inside = (packet.starts >= -1e-9) & (packet.ends <= overlap_s+1e-9)
    if not fully_inside.any():
        raise ValueError('overlap must contain complete packets')
    recorded_rate = angle[fully_inside]/durations[fully_inside]
    with_half_count = (angle[fully_inside]+np.sqrt(3)*angle_scale/2)/durations[fully_inside]
    first, last, covered = packet.bounds(np.arange(int(overlap_s), dtype=float), 1.)
    integrated = np.r_[0., np.cumsum(angle)]
    okay = covered >= .99-1e-9
    rate = (integrated[last[okay]]-integrated[first[okay]])/covered[okay]
    return dict(packets=int(fully_inside.sum()), whole_second_windows=len(rate),
        peak_packet_rad_s=float(recorded_rate.max()),
        packet_peak_with_half_count_rad_s=float(with_half_count.max()),
        p95_one_second_rad_s=float(np.quantile(rate, .95)) if len(rate) else None,
        peak_one_second_rad_s=float(rate.max()) if len(rate) else None)


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing bounded study')
    report = (root/parent.RESULT).read_bytes()
    if digest(report) != PARENT_SHA:
        raise ValueError('original verified gyro timing report required')
    parent_id = 'data/'+parent.ID
    with closing(ClosedStudy(root, parent_id)) as closed:
        if (closed.completion != json.loads(report)['closures'][parent_id]
                or not closed.envelope(LEG)['result']['passed']):
            raise ValueError('exact closed mixed-recorder task required')
        layout = closed.input(LEG)
        inputs = dict(parent=parent.RESULT)
        for side in layout['sides']:
            key = side['original']
            record = closed.manifest['inputs'][key]
            if not record['source'].startswith('data/ilvis0-ready/'):
                raise ValueError('the retained original in the NASA corpus is required')
            with safe_path(root, record['source']).open('rb') as stream:
                if file_digest(stream, 'sha256').hexdigest() != layout['compressed_shas'][key]:
                    raise ValueError('retained original hash changed')
            inputs[key] = record['source']
    layout_path = f'data/{ID}-inputs/layout.json'
    _write_equal(root/layout_path, encoded(layout))
    inputs['layout'] = layout_path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, 'analysis/tests/test_ilvis0_paired_gyro_motion.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=90.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def streams(context, layout):
    import numpy as np

    from .ilvis0_segments import extract_segment

    for side, kind in zip(layout['sides'], parent.LEGS[LEG], strict=True):
        key = side['original']
        if context.manifest['inputs'][key]['sha256'] != layout['compressed_shas'][key]:
            raise ValueError('verified original hash required')
        context.charge(bound_calls=1, bound_steps=parent.MAX_PACKETS)
        values, _, _, source = extract_segment(context.input_path(key), side['context'], side['segment'])
        if (not 0 < len(values) <= parent.MAX_PACKETS or source['group1_observations_used']
                or side['segment']['imu_type'] != kind):
            raise ValueError('retained packet allowance or source provenance differs')
        header_ends, header_dt, angles = values[:, 1]-layout['begin'], values[:, 2], values[:, 9:12]
        nominal_ends = header_ends[0]-header_dt[0]+.005*np.arange(1, len(values)+1)
        yield kind, source, angles, dict(nominal_200Hz=(nominal_ends, np.full(len(values), .005)),
                                         header_elapsed=(header_ends, header_dt))


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index','shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact mixed-recorder overlap required')
    layout = json.loads(context.input_path('layout').read_bytes())
    overlap = layout['end']-layout['begin']
    records = []
    for kind, source, angles, clocks in streams(context, layout):
        for clock, (ends, dt) in clocks.items():
            context.charge(bound_calls=1, bound_steps=parent.MAX_PACKETS)
            records.append(dict(clock=clock, imu_type=kind, source=source,
                **summaries(ends, dt, angles, overlap, source['angle_scale_rad_per_count'])))
    context.save_bytes('recorded-motion.json', encoded(dict(overlap=overlap, records=records,
        fit_starts=0, group1_observations_used=False, scientific_decision='abstain')))
    return dict(passed=True, summaries=len(records), scientific_decision='abstain')
