# SPDX-License-Identifier: AGPL-3.0-or-later
"""Quantify the orientation ambiguity of the sealed ESA north-only path pair."""

from contextlib import closing
from fractions import Fraction
import json
from pathlib import Path

from . import esa_girafe_horizontal_witness as parent
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded


ID = 'esa-girafe-tilt-identifiability-v1'
SCOPE = 'ESA 187 north-only error force direction and invariant magnitude on sealed supports'
PLAN = parent.axis.FOLDER+'ESA_GIRAFE_TILT_IDENTIFIABILITY_PLAN.md'
PARENT_SHA = 'b3bc6462ee236179f8918a7e585c788bf79c5ce55878a229f37a06ef46e790ed'
LEGACY_SCALE_RAD = .0015
SUPPORT_STEPS = 4*4*48
TASK = dict(identity='paired-force-orientation', input_key='sealed_supports', payload={},
    limits=dict(native_calls=0, packet_visits=0, bound_calls=10, bound_steps=10*SUPPORT_STEPS))


def orientation_sensitivity(original, displaced):
    import numpy as np

    a, b = (np.asarray(x, dtype=float) for x in (original, displaced))
    if any(x.shape != (3,) or not np.isfinite(x).all() for x in (a, b)):
        raise ValueError('two finite three-axis vectors required')
    a_len, b_len = np.linalg.norm(a), np.linalg.norm(b)
    if min(a_len, b_len) == 0:
        raise ValueError('nonzero force directions required')
    axis = np.cross(a, b)
    axis_length = np.linalg.norm(axis)
    angle = float(np.arctan2(axis_length, a@b))
    elevation = (float(np.arctan2(abs(axis[2]), np.linalg.norm(axis[:2])))
                 if axis_length else None)
    delta = b-a
    return dict(minimum_rotation_rad=angle, rotation_axis_elevation_rad=elevation,
        north_change_mps2=float(delta[0]), vector_change_mps2=float(np.linalg.norm(delta)),
        magnitude_change_mps2=float(delta@(a+b)/(a_len+b_len)),
        fraction_of_earlier_alignment_scale=angle/LEGACY_SCALE_RAD)


def prepare(root):
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing sealed sensitivity')
    report = (root/parent.RESULT).read_bytes()
    if digest(report) != PARENT_SHA:
        raise ValueError('exact sealed horizontal force report required')
    with closing(ClosedStudy(root,'data/'+parent.ID)) as study:
        e = study.envelope(parent.TASK['identity'])
        if (study.completion != json.loads(report)['completion'] or not e['result']['passed']
                or e['charged'] != parent.TASK['limits']):
            raise ValueError('complete verified parent with the original allowances required')
        inputs = {'sealed_supports': parent.RESULT}
        for key in ('path', 'anchor', 'metric', 'witness', 'axes'):
            name = f'data/{ID}-inputs/{key}.json'
            _write_equal(root/name, study.input(key, raw=True))
            inputs[key] = name
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_tilt_identifiability.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=30.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_rinex_code_comparison import coordinates
    from .shared_motion_carrier import displacement_at

    declared = {key: value for key, value in task.items() if key not in ('index','shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('fixed paired-force orientation task required')

    def read(key):
        return json.loads(context.input_path(key).read_bytes())

    path, anchor, metric, recorded, axes = map(read, ('path', 'anchor', 'metric', 'witness', 'axes'))
    if [r['seconds'] for r in path] != [parent.axis.START+.5*i for i in range(1, 241)]:
        raise ValueError('original complete half-second path required')
    times = np.asarray([anchor['time_s'], *(r['seconds'] for r in path)])
    reference = np.asarray([coordinates([anchor])[0], *(r['position'] for r in path)])
    knots = [dict(elapsed_s=float(Fraction(row['elapsed_s_exact'])), position_m=row['position_m'],
                 velocity_mps=row['speed_mps']) for row in recorded['knots']]
    accelerations = np.asarray([[float(Fraction(v)) for v in row['acceleration_exact_mps2']]
                                for row in recorded['knots']])
    shifted = reference.copy()
    shifted[:, 0] += [displacement_at(knots, t-anchor['time_s'], accelerations)[0]/
                      (metric[0]*axes['energy_fraction']['north']) for t in times]
    supports = read('sealed_supports')['supports']
    if len(supports) != len(parent.HALF_SPANS)*len(parent.CENTERS):
        raise ValueError('complete sealed support schedule required')
    rows = []
    for index, (half, seconds) in enumerate((h, s) for h in parent.HALF_SPANS for s in parent.CENTERS):
        context.charge(bound_calls=1, bound_steps=SUPPORT_STEPS)
        support = supports[index]
        center = parent.axis.START+seconds
        if (support['center_gps_s'], support['width_seconds']) != (center, 2*half):
            raise ValueError('unchanged earlier support required')
        sl = slice(2*(seconds-half), 2*(seconds+half)+1)
        local = times[sl]-center
        derivative, kernel = parent.acceleration_kernel(local)
        for model in parent.MODELS:
            means = []
            for label, position in (('original', reference), ('north_only', shifted)):
                force, mass = parent.supported_force(local, kernel, position[sl], derivative, model)
                values = parent.vector_summaries(force[:, :2], mass)
                if any(abs(v-support['models'][model][label][k]) > 5e-12 for k, v in values.items()):
                    raise ValueError('sealed horizontal force magnitude did not reproduce')
                means.append(mass@force)
            rows.append(dict(center_gps_s=center, width_s=2*half, model=model,
                original_ned_mps2=means[0].tolist(), displaced_ned_mps2=means[1].tolist(),
                **orientation_sensitivity(*means)))
    context.save_bytes('orientation-sensitivity.json', encoded(dict(rows=rows,
        historical_alignment_scale_rad=LEGACY_SCALE_RAD, protected_reads=0,
        scientific_decision='abstain')))
    return dict(passed=True, paired_means=len(rows), scientific_decision='abstain')
