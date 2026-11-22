# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check logged ground gyro changes against the measured force direction."""

from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sys

from .airquantumgrav_packet_slice import held_measurements
from .esa_component_preflight import FOLDER, RECORDS, WIDTH
from .esa_direction_holdout_forecast import frozen_input
from .esa_girafe_platform_timing import held_cell_means
from .esa_ground_rate_scale import FIRST, INVENTORY, SECOND, SOURCE
from .esa_gyro_force_direction import angles, midpoint_attitudes
from .force_direction_alignment import unit_vectors
from .studies.artifacts import atomic, digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'esa-ground-tilt-closure-v1'
SCOPE = 'ground force-direction comparison of uncorrected gyro on two fixed ESA 187 stops'
PLAN = FOLDER+'ESA_GROUND_TILT_CLOSURE_PLAN.md'
RESULT = FOLDER+'esa-ground-tilt-closure-result.json'
INPUTS = {'first': FIRST, 'second': SECOND, 'inventory': INVENTORY}
DIGESTS = {
    'first': 'e587348ea92fd3918183bd2b7986e959b4038e77134fc1ded72396fd4e8a12e3',
    'second': '5c180edc81e119abb0da8c5926b4563118c16c64c27d06b129c322ec2ac21e03',
    'inventory': 'ce0b7465e45e3d0f7c57117de6f26b5243a753c077573f0cd3707fa3a3797342',
}
STOPS = (('first', 'raw_imu', 811_808), ('second', 'second_raw_imu', 553_344))
SOURCE_BYTES = (RECORDS+1)*WIDTH
SPANS = (1, 10)
TASK = dict(identity='compare-logged-tilt', input_key='inventory', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+3*len(STOPS),
                        bound_steps=SOURCE_BYTES+3*sum(count for _, _, count in STOPS)))


def gyro_steps(edges, rates, centers):
    """Compose the original left-held intervals between each pair of centers."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    edges, rates, centers = (np.asarray(vector, float) for vector in (edges, rates, centers))
    if (edges.ndim != 1 or centers.ndim != 1 or len(edges) < 2 or len(centers) < 2
            or rates.shape != (len(edges)-1, 3)
            or not all(np.isfinite(vector).all() for vector in (edges, rates, centers))
            or np.any(np.diff(edges) <= 0.) or np.any(np.diff(centers) <= 0.)
            or centers[0] < edges[0] or centers[-1] > edges[-1]):
        raise ValueError('ordered centers must be supported by gyro intervals')
    start = np.searchsorted(edges, centers[:-1], side='right')-1
    end = np.searchsorted(edges, centers[1:], side='left')
    rotations = []
    for lower, upper, first, last in zip(centers[:-1], centers[1:], start, end, strict=True):
        left = np.maximum(edges[first:last], lower)
        right = np.minimum(edges[first+1:last+1], upper)
        increments = rates[first:last]*(right-left)[:, None]
        midpoint = midpoint_attitudes(increments)[-1]
        rotations.append(midpoint*Rotation.from_rotvec(increments[-1]/2.))
    return Rotation.concatenate(rotations)


def tilt_pairs(force, rotations, *, span):
    """Compare later force directions with exact gyro and no-change predictions."""
    import numpy as np
    from scipy.spatial.transform import Rotation

    unit = unit_vectors(force)
    if type(span) is not int or not 1 <= span < len(unit) or len(rotations) != len(unit)-1:
        raise ValueError('one gyro rotation per consecutive center and a complete span required')
    starts = np.arange(0, len(unit)-span, span)
    if span == 1:
        composed = rotations
    else:
        totals = []
        for i in starts:
            rotation = rotations[i]
            for following in rotations[i+1:i+span]:
                rotation = rotation*following
            totals.append(rotation)
        composed = Rotation.concatenate(totals)

    earlier, later = unit[starts], unit[starts+span]
    predicted = composed.inv().apply(earlier)
    observed_change = later-earlier
    gyro_change = predicted-earlier
    observed_centered = observed_change-observed_change.mean(axis=0)
    predicted_centered = gyro_change-gyro_change.mean(axis=0)
    observed_norm = np.linalg.norm(observed_centered)
    predicted_norm = np.linalg.norm(predicted_centered)
    centered_error = np.linalg.norm(predicted_centered-observed_centered)
    actual_angles = np.rad2deg(angles(earlier, later))*3600.
    predicted_angles = np.rad2deg(angles(earlier, predicted))*3600.
    residual_angles = np.rad2deg(angles(predicted, later))*3600.
    return dict(pairs=len(starts), span_s=span, first_center_indices=starts.tolist(),
                no_motion_rms_arcsec=float(np.sqrt(np.mean(actual_angles**2))),
                gyro_change_rms_arcsec=float(np.sqrt(np.mean(predicted_angles**2))),
                gyro_prediction_rms_arcsec=float(np.sqrt(np.mean(residual_angles**2))),
                centered_change_similarity=float(np.sum(observed_centered*predicted_centered)/
                                                 (observed_norm*predicted_norm))
                if min(observed_norm, predicted_norm) > 1e-15 else None,
                centered_error_reduction=float(1.-(centered_error/observed_norm)**2)
                if observed_norm > 1e-15 else None,
                no_motion_errors_arcsec=actual_angles.tolist(),
                gyro_change_arcsec=predicted_angles.tolist(),
                prediction_errors_arcsec=residual_angles.tolist(),
                observed_direction_changes=observed_change.tolist(),
                gyro_direction_changes=gyro_change.tolist())


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing frozen ground tilt check')
    for key, path in INPUTS.items():
        if digest((root/path).read_bytes()) != DIGESTS[key]:
            raise ValueError('unchanged ground selections and original inventory required')
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=INPUTS, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_ground_tilt_closure.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact declared comparison required')
    inputs = {key: frozen_input(context, key, sha) for key, sha in DIGESTS.items()}
    source = safe_path(context.root.parents[1], SOURCE)
    inventory = inputs['inventory']
    source_hash = inventory['source_sha256']
    if (inventory['source_file'] != source.name or inventory['records'] != RECORDS
            or inputs['second']['first_raw_sha256'] != DIGESTS['first']
            or any(inputs[key]['source_sha256'] != source_hash or inputs[key]['uses_model_fits'] is not False
                   for key, _, _ in STOPS)):
        raise ValueError('unchanged original recording and selected stops required')

    with source.open('rb') as stream:
        before = os.fstat(stream.fileno())
        context.charge(bound_calls=1, bound_steps=SOURCE_BYTES)
        if before.st_size != SOURCE_BYTES or hashlib.file_digest(stream, 'sha256').hexdigest() != source_hash:
            raise ValueError('iMAR original differs from inventory')
        stream.seek(0)
        header = stream.read(WIDTH)
        for key, row_name, count in STOPS:
            expected = inputs[key][row_name]
            lower, upper = expected['first_sample_time_s'], expected['last_sample_time_s']
            context.charge(bound_calls=1, bound_steps=count)
            edges, force, rates = held_measurements(stream, header, row_bytes=WIDTH, row_count=RECORDS,
                                                    maximum_samples=count, lower=lower, upper=upper)
            if (len(force) != count or expected['samples'] != count+1
                    or edges[0] != lower or edges[-1] != upper):
                raise ValueError('exact support bounded by earlier ground-stop timestamps required')
            context.charge(bound_calls=1, bound_steps=count)
            cells = lower+np.arange(int(upper-lower)+1)
            force_means = held_cell_means(edges, force, cells)
            centers = (cells[:-1]+cells[1:])/2.
            context.charge(bound_calls=1, bound_steps=count)
            rotations = gyro_steps(edges, rates, centers)
            result = dict(intervals=count, first_time_s=lower, last_time_s=upper,
                          unused_partial_force_s=float(upper-cells[-1]), center_times_s=centers.tolist(),
                          mean_force_directions=unit_vectors(force_means).tolist(),
                          mean_force_magnitudes_mps2=np.linalg.norm(force_means, axis=1).tolist(),
                          comparisons=[tilt_pairs(force_means, rotations, span=span) for span in SPANS])
            context.save_bytes(f'{key}.json', encoded(result))
        after = os.fstat(stream.fileno())
        if (before.st_size, before.st_ctime_ns, before.st_mtime_ns) != (after.st_size, after.st_ctime_ns, after.st_mtime_ns):
            raise ValueError('original iMAR file changed while being read')
    return dict(passed=True, stops=len(STOPS), original_source_sha256=source_hash,
                model_fits=0, protected_reads=0, scientific_decision='abstain')


def report(root):
    names = ('pairs', 'span_s', 'no_motion_rms_arcsec', 'gyro_change_rms_arcsec',
             'gyro_prediction_rms_arcsec', 'centered_change_similarity', 'centered_error_reduction')
    identity = TASK['identity']
    stops = {}
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('closed comparison and its exact charges required')
        for key, _, count in STOPS:
            raw = study.artifact(identity, f'{key}.json', raw=True)
            saved = json.loads(raw)
            if saved['intervals'] != count or tuple(row['span_s'] for row in saved['comparisons']) != SPANS:
                raise ValueError('closed result does not match the declared support')
            stops[key] = dict(intervals=count, artifact_sha256=digest(raw),
                comparisons=[{name: row[name] for name in names} for row in saved['comparisons']])
        result = dict(stops=stops, manifest_sha256=study.completion['manifest_sha256'],
                      inputs_sha256=DIGESTS, charged=TASK['limits'], scientific_decision='abstain')
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('closed public summary differs')
    return dict(sha256=digest(raw), stops=stops)


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
