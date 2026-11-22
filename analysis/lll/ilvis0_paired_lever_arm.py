# SPDX-License-Identifier: AGPL-3.0-or-later
"""Withheld check of rigid mounting displacement on two archived recorder pairs."""

import argparse
from contextlib import closing
import hashlib
import json
import math
from pathlib import Path

from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_pair_alignment import MIN_HALF_SECONDS, MIN_SINGULAR_RATIO
from .ilvis0_paired_accelerometers import CLOCKS, FOLDER, LEGS, MAX_PACKETS, WINDOW_SUPPORT
from .ilvis0_paired_gyro_clock import ID as PARENT, RESULT as PRIOR, PacketRates, alignment
from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-paired-lever-arm-v1'
SCOPE = 'Earlier-only mounting displacement and later recorder disagreement on two NASA legs'
PLAN = FOLDER+'PAIRED_LEVER_ARM_PLAN.md'
RESULT = FOLDER+'paired-lever-arm-result.json'
REQUEST = FOLDER+'paired-lever-arm-qualification.json'
REPORT = FOLDER+'paired-lever-arm-tests.xml'
TEST = 'analysis/tests/test_ilvis0_paired_lever_arm.py'
TESTS = ('test_tangential_and_centripetal_columns_have_rigid_body_sign',
         'test_neighboring_windows_are_kept_inside_the_frozen_half',
         'test_displacement_uses_earlier_only_and_declines_unidentifiable_designs')
PRIOR_SHA = 'bdf0ddc98d184644cc92b40298ee6a26d95125fed4ff5a2db8d8e054ad1138be'
WIDTHS = (1., 10.)
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=6, bound_steps=10*MAX_PACKETS)


def angular_design(omega, centripetal, width):
    import numpy as np

    alpha = (omega[2:]-omega[:-2])/(2.*width)
    x, y, z = alpha.T
    zero = np.zeros_like(x)
    skew = np.column_stack((zero, -z, y, z, zero, -x, -y, x, zero)).reshape(-1, 3, 3)
    return skew+centripetal[1:-1]


def eligible(starts, width, duration, support):
    import numpy as np

    valid = support[:-2] & support[1:-1] & support[2:]
    first, last = starts[:-2], starts[2:]+width
    return (np.flatnonzero(valid & (first >= 0.) & (last <= duration/2.+1e-9))+1,
            np.flatnonzero(valid & (first >= duration/2.-1e-9) & (last <= duration+1e-9))+1)


def fit_and_score(design, difference, train, hold):
    import numpy as np

    def rms(values):
        mean_square = (values**2).mean(axis=0)
        return dict(vector_rms_mps2=float(np.sqrt(mean_square.sum())), component_rms_mps2=np.sqrt(mean_square).tolist())

    earlier, target = difference[train], difference[hold]
    baseline = earlier.mean(axis=0)
    mean_design = design[train].mean(axis=0)
    centered = (design[train]-mean_design).reshape(-1, 3)
    singular = np.linalg.svd(centered, compute_uv=False)
    ratio = float(singular[-1]/singular[0]) if singular[0] > 0. else 0.
    summary = dict(baseline_offset_mps2=baseline.tolist(), baseline_later=rms(target-baseline),
                   displacement_singular_values=singular.tolist(), displacement_ratio=ratio)
    if ratio < MIN_SINGULAR_RATIO:
        return dict(summary, status='unidentifiable_displacement')
    displacement = np.linalg.lstsq(centered, (earlier-baseline).ravel(), rcond=None)[0]
    offset = baseline-mean_design@displacement
    return dict(summary, status='scored', offset_mps2=offset.tolist(), displacement_m=displacement.tolist(),
                displacement_norm_m=float(np.linalg.norm(displacement)), lever_later=rms(target-offset-design[hold]@displacement))


def compare(left, right, *, duration, width):
    import numpy as np

    starts = width*np.arange(math.floor(duration/width))
    gyro, force = [], []
    centripetal = None
    valid = np.ones(len(starts), dtype=bool)
    for ends, dt, angles, dv in (left, right):
        clock = PacketRates(ends, dt, angles)
        omega, support = clock.windows(starts, width)
        f, _ = PacketRates(ends, dt, dv).windows(starts, width)
        gyro.append(omega)
        force.append(f)
        valid &= support >= WINDOW_SUPPORT
        if centripetal is None:
            rates = angles/dt[:, None]
            outer = rates[:, :, None]*rates[:, None, :]
            square = outer-np.trace(outer, axis1=1, axis2=2)[:, None, None]*np.eye(3)
            accumulated = np.concatenate((np.zeros((1, 3, 3)), np.cumsum(square*dt[:, None, None], axis=0)))
            first, last, elapsed = clock.bounds(starts, width)
            averaged = np.full((len(starts), 3, 3), np.nan)
            good = elapsed >= WINDOW_SUPPORT*width
            averaged[good] = (accumulated[last[good]]-accumulated[first[good]])/elapsed[good, None, None]
            centripetal = averaged
    earlier, later = eligible(starts, width, duration, valid)
    geometry = dict(earlier_windows=len(earlier), later_windows=len(later))
    if min(len(earlier), len(later))*width < MIN_HALF_SECONDS:
        return dict(geometry, status='incomplete_support')
    gyro_ratio, orientation = alignment(gyro[0][earlier], gyro[1][earlier])
    if orientation is None:
        return dict(geometry, status='unidentifiable_rotation', gyro_ratio=gyro_ratio)
    _, rotation, rate_offset = orientation
    difference = force[0]-force[1]@rotation.T
    design = angular_design(gyro[0], centripetal, width)
    fit = fit_and_score(design, difference[1:-1], earlier-1, later-1)
    return dict(geometry, gyro_ratio=gyro_ratio, rotation=rotation.tolist(), gyro_offset_rad_s=rate_offset.tolist(), **fit)


def task_for(identity):
    return dict(identity=identity, input_key=identity, limits=LIMITS)


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, environment


def prepare(root):
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the existing paired displacement comparison')
    prior = (root/PRIOR).read_bytes()
    if digest(prior) != PRIOR_SHA:
        raise ValueError('exact completed paired-recorder receipt required')
    saved = json.loads(prior)
    sources, env = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=env,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    staged = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (saved['closures'][parent.prefix] != parent.completion or not parent.summary['passed']
                or set(parent.rows) != set(LEGS)):
            raise ValueError('both original comparison pairs must be sealed')
        for identity in LEGS:
            if parent.envelope(identity)['result'] != saved['rows'][identity]:
                raise ValueError('archived recorder comparison differs from its seal')
            layout = parent.input(identity)
            for side in layout['sides']:
                key = side['original']
                record = parent.manifest['inputs'][key]
                path = safe_path(root, record['source'])
                if not record['source'].startswith('data/ilvis0-ready/') or not path.is_file():
                    raise ValueError('original frozen open recorder file required')
                with path.open('rb') as stream:
                    if hashlib.file_digest(stream, 'sha256').hexdigest() != layout['compressed_shas'][key]:
                        raise ValueError('the frozen recorder file has changed')
                inputs[key] = record['source']
            staged[identity] = encoded(layout)
    for key, value in staged.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                      sources=sources,tasks=[task_for(identity) for identity in LEGS], workers=2,threads=1,maximum_wall_s=300.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np
    from .ilvis0_segments import extract_segment

    identity = task['identity']
    declared = {k: v for k, v in task.items() if k not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or identity not in LEGS or declared != task_for(identity):
        raise ValueError('exact earlier paired legs are required')
    layout = json.loads(context.input_path().read_bytes())
    streams = []
    for side, imu_type in zip(layout['sides'], LEGS[identity], strict=True):
        key = side['original']
        if context.manifest['inputs'][key]['sha256'] != layout['compressed_shas'][key]:
            raise ValueError('the recorder differs from its preserved hash')
        context.charge(bound_calls=1, bound_steps=MAX_PACKETS)
        values, _, _, provenance = extract_segment(context.input_path(key), side['context'], side['segment'])
        if (not 2 <= len(values) <= MAX_PACKETS or side['segment']['imu_type'] != imu_type
                or provenance['group1_observations_used']):
            raise ValueError('unchanged recorder type and original packet allowance required')
        dv = values[:, 3:6]*provenance['velocity_scale_mps_per_count']
        streams.append((values[:, 1]-layout['begin'], values[:, 2], values[:, 9:12], dv))
    rows = []
    for clock in CLOCKS:
        timed = streams
        if clock == 'nominal_200Hz':
            timed = [(end[0]-dt[0]+.005*np.arange(1, len(dt)+1), np.full(len(dt), .005), a, dv)
                     for end, dt, a, dv in streams]
        for width in WIDTHS:
            context.charge(bound_calls=1, bound_steps=2*MAX_PACKETS)
            metrics = compare(*timed, duration=layout['end']-layout['begin'], width=width)
            rows.append(dict(clock=clock, width=width, **metrics))
    result = dict(pair=identity, comparisons=rows, passed=True, new_earth_model_fits=0, scientific_decision='abstain')
    context.save('paired-lever-arm.json', result)
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        rows = {}
        for identity in LEGS:
            record = study.envelope(identity)
            result = record['result']
            if (record['status'] != 'complete' or record['charged'] != LIMITS or not result['passed']
                    or result != study.artifact(identity, 'paired-lever-arm.json')):
                raise ValueError('complete exact charged paired outcome required')
            rows[identity] = result
        value = dict(rows=rows, completion=study.completion)
    _write_equal(root/RESULT, encoded(value))
    return dict(pairs=len(rows), scored=sum(r['status'] == 'scored' for row in rows.values() for r in row['comparisons']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    value = qualification(root, check=False) if action == 'request' else {'prepare':prepare,'report':report}[action](root)
    print(json.dumps(value, sort_keys=True))
