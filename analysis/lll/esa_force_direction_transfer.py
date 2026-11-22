# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only orientation transfer on the sealed ESA force supports."""

from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from .esa_doppler_force import (BASE, CENTERS, DIRECTORY, FOLDER, MATCH_SHA, MATRIX, MATRIX_SHA,
                              VELOCITY_SHA, WIDTHS, paths, rate_operator)
from .esa_gyro_direction_calibration import EARLIER, EARLIER_SHA, MATCHED, MATCHED_SHA, fixed_support, packet_inputs
from .esa_gyro_force_direction import FLAT, STILL, angles, midpoint_attitudes, predictions
from .esa_matched_gyro_direction import DISC_WITH_FIELD, FieldFrame, GLOBE, background_axes, support
from .force_direction_alignment import aligned_direction_scores
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-force-direction-transfer-v1'
SCOPE = 'fit one earlier force-direction rotation per matching scenario on ESA 187'
PLAN = FOLDER + 'ESA_FORCE_DIRECTION_TRANSFER_PLAN.md'
RESULT = FOLDER + 'esa-force-direction-transfer-result.json'
BIAS = (-.10, 0., .0225, .05, .10)
FIELDS = ('zero_field', 'full_field_logged', 'full_field_removed_from_gyro')
TRAINING = 8
INTERVALS = 119865
ALIGNMENTS = len(BIAS)*len(FIELDS)*len(WIDTHS)*3*2
TASK = dict(identity='all-direction-alignments', input_key='interval', payload=dict(alignments=ALIGNMENTS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=ALIGNMENTS, bound_steps=0))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if (root / 'data' / ID).exists() or directory.exists():
        raise ValueError('existing force-direction transfer freeze must stay intact')
    inputs = dict(doppler=DIRECTORY+'/velocity.json.gz', matching=BASE+'comparison.json', direction=EARLIER,
                  matched=MATCHED)
    with closing(ArchiveStore(root)) as store:
        for key, name in inputs.copy().items():
            target = directory / key
            atomic(target, store.read(name))
            inputs[key] = target.relative_to(root).as_posix()
        with closing(ClosedStudy(root, MATRIX, store=store)) as parent:
            if (parent.completion['manifest_sha256'] != MATRIX_SHA
                    or parent.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'):
                raise ValueError('exact opened ESA development cut required')
            for key in ('training', 'interval', 'saved-input-binding'):
                target = directory / key
                atomic(target, parent.input(key, raw=True))
                inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_force_direction_alignment.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


class FrozenInputs:
    def __init__(self, context):
        self.context = context

    def input(self, key, *, raw=False):
        data = self.context.input_path(key).read_bytes()
        return data if raw else json.loads(data)


def measured_force_basis(times, packets, *, all_axes=False):
    import numpy as np

    clock, theta, force, dt = packets
    if len(dt) != INTERVALS:
        raise ValueError('exact earlier gyro interval count required')
    frames = midpoint_attitudes(theta)
    nominal = frames.apply(force)
    axes = frames.as_matrix() if all_axes else frames.apply(np.tile([1., 0., 0.], (len(dt), 1)))
    channels = axes*force[:, None, :] if all_axes else None
    output = {}
    for width in WIDTHS:
        supports, _ = fixed_support(width, times, clock, nominal)

        def averages(values):
            return np.asarray([np.tensordot(pair.earlier_weights, values[pair.earlier], axes=1) for pair in supports] +
                              [np.tensordot(pair.later_weights, values[pair.later], axes=1) for pair in supports])

        output[width] = averages(nominal), averages(axes)
        if all_axes:
            output[width] += (averages(channels),)
    return output


def _predicted_vectors(times, coordinate, rates, width, frames, *, coefficients=None):
    import numpy as np

    elapsed = times-times[0]
    output = {name: {'globe': [], 'disc': []} for name in FIELDS}
    for index, center in enumerate(CENTERS):
        half = width//2
        sl = slice(center-half, center+half+1)
        relative = times[sl]-times[center]
        op, kernel = rate_operator(relative)
        fit = op@rates[sl] if coefficients is None else coefficients[index]
        center_args = relative, kernel, coordinate[center], fit, elapsed[center]
        zero = predictions(*center_args)
        for shape, zero_model, field_model in (('globe', STILL, GLOBE), ('disc', FLAT, DISC_WITH_FIELD)):
            output['zero_field'][shape].append(zero[zero_model])
            local = support(*center_args, field_model)
            for index, field in enumerate(('full_field_removed_from_gyro', 'full_field_logged')):
                output[field][shape].append(local.average(frames[field_model][index]))
    return {field: {shape: np.asarray(v) for shape, v in rows.items()} for field, rows in output.items()}


def verified_force_inputs(material):
    velocity = json.loads(gzip.decompress(material.input('doppler', raw=True)))['velocity']
    matching, direction, matched = (material.input(key)['result'] for key in ('matching', 'direction', 'matched'))
    if [digest(encoded(row)) for row in (velocity, matching, direction, matched)] != [
            VELOCITY_SHA, MATCH_SHA, EARLIER_SHA, MATCHED_SHA]:
        raise ValueError('unchanged earlier support and validation references required')
    times, coordinate, rates = paths(material, velocity, matching['matched_code_indices'][:400])
    return times, coordinate, rates, direction, matched, packet_inputs(material, times[-1])


def force_settings(prepared, *, all_axes=False, observed=None):
    import numpy as np

    times, coordinate, rates, direction, matched, packets = prepared
    if observed is None:
        observed = measured_force_basis(times, packets, all_axes=all_axes)
    frames = matched_field_frames(times, coordinate)
    for width, reference in zip(WIDTHS, direction['settings'], strict=True):
        nominal = observed[width][0]
        if (reference['width_reports'] != width or not np.allclose(
                np.rad2deg(angles(nominal[:TRAINING], nominal[TRAINING:])),
                reference['measured_pair_angles_deg'], rtol=0., atol=1e-10)):
            raise ValueError('nominal logged force directions did not reproduce')
        for source, path in rates.items():
            vectors = _predicted_vectors(times, coordinate, path, width, frames)
            prior = next(row['by_shape'] for row in matched['settings']
                         if row['source'] == source and row['width_reports'] == width)
            for field, index in (('full_field_logged', -1), ('full_field_removed_from_gyro', 0)):
                for shape, model in (('globe', GLOBE), ('disc', DISC_WITH_FIELD)):
                    v = vectors[field][shape]
                    if not np.allclose(angles(v[:TRAINING], v[TRAINING:]),
                            prior[model]['grid_pair_angles_rad'][index], rtol=0., atol=1e-12):
                        raise ValueError('published predicted direction endpoints did not reproduce')
            yield width, source, *observed[width], vectors


def matched_field_frames(times, coordinate):
    elapsed = times-times[0]
    frames = {}
    for model in (GLOBE, DISC_WITH_FIELD):
        axes = background_axes(coordinate, model)
        steps = (axes[:-1]+axes[1:])/2.
        frames[model] = [FieldFrame(elapsed, steps, strength) for strength in (0., 1.)]
    return frames


def verified_force_settings(material, *, all_axes=False):
    return force_settings(verified_force_inputs(material), all_axes=all_axes)


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE or task['payload'] != TASK['payload']):
        raise ValueError('exact force rotation task required')
    rows = []
    for width, source, nominal, response, vectors in verified_force_settings(FrozenInputs(context)):
        for field, shape_vectors in vectors.items():
            for bias in BIAS:
                measured = nominal-bias*response
                scores = {}
                for shape, predicted in shape_vectors.items():
                    context.charge(bound_calls=1, bound_steps=0)
                    scores[shape] = aligned_direction_scores(predicted, measured, training=TRAINING)
                g, d = scores['globe'], scores['disc']
                gap = d['later_rms_deg']-g['later_rms_deg'] if g['status'] == d['status'] == 'scored' else None
                rows.append(dict(source=source, width_reports=width, field=field, x_bias_mps2=bias,
                                 scores=scores, disc_minus_globe_deg=gap))
    context.save_bytes('direction-scores.json', encoded(dict(rows=rows, gyro_intervals=INTERVALS,
         new_inertial_fits=0, original_data_reads=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=len(rows)*2 == ALIGNMENTS, compared_pairs=len(rows), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if not run.summary['passed'] or run.summary['charged']['bound_calls'] != ALIGNMENTS:
            raise ValueError('complete analytic alignment study required')
        outcomes = run.artifact(TASK['identity'], 'direction-scores.json')
        result = dict(manifest_sha256=run.completion['manifest_sha256'], alignments=ALIGNMENTS, **outcomes)
    raw = encoded(result)
    output = root / RESULT
    if not output.exists():
        atomic(output, raw)
    if output.read_bytes() != raw:
        raise ValueError('saved alignment report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_force_direction_transfer {prepare,report}')
