# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only fit of a two-term zenith-delay error on the saved GPS path."""

from contextlib import closing
import gzip
import json
import math
from pathlib import Path
import sys

from .esa_carrier_phase_continuous import COUNT, END, START
from .esa_carrier_phase_later import CUT, LATER, phase_step_geometry
from .esa_carrier_satellite_influence import ID as GEOMETRY, TASKS, ecef_track
from .esa_raw_receiver_score import GEOMETRY_MANIFEST
from .esa_receiver_accuracy_replay import ID as ACCURACY, LAWS, score_setting
from .esa_rinex_window import FOLDER
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-carrier-delay-fit-v1'
PLAN = FOLDER+'ESA_CARRIER_DELAY_FIT_PLAN.md'
RESULT = FOLDER+'esa-carrier-delay-fit-result.json'
SCOPE = 'earlier-only two-term zenith-delay check on the sealed ESA 187 GPS carrier path'
ACCURACY_MANIFEST = '20872911729dad250e95d7fdfd8797ade63c2705f7912e1bfd90f883138f5df7'
TRAIN_STEPS = 2*(CUT-1)
TASK = dict(identity='carrier-delay-fit', input_key='track', payload=dict(steps=COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=COUNT, bound_steps=32*COUNT))


def mapping_difference(first_mapping, last_mapping, first_s, last_s):
    import numpy as np

    return np.column_stack((last_mapping-first_mapping,
                            (last_s*last_mapping-first_s*first_mapping)/400.))


def advance(earlier, later, delay, position, withheld):
    """Project against the later position and clock, including earlier displacement."""
    import numpy as np

    from .gnss_carrier_phase import MAX_CONDITION

    if np.linalg.cond(later) >= MAX_CONDITION:
        raise ValueError('ill-conditioned satellite geometry')
    basis, triangular = np.linalg.qr(later, mode='reduced')
    gain = np.linalg.solve(triangular, basis.T)
    source = delay-earlier[:, :3] @ position
    end_shift = -gain @ source
    orthogonal = source + later @ end_shift
    leverage = np.sum(basis**2, axis=1)
    return end_shift[:3], orthogonal, (1.-leverage)*withheld


def estimate(columns, residuals, cutoff):
    import numpy as np

    earlier, later = np.concatenate(columns[:cutoff]), np.concatenate(columns[cutoff:])
    earlier_y, later_y = np.concatenate(residuals[:cutoff]), np.concatenate(residuals[cutoff:])
    theta, _, rank, singular = np.linalg.lstsq(earlier, earlier_y, rcond=None)
    if rank != 2:
        raise ValueError('earlier delay design must have rank two')

    def errors(matrix, observed):
        shape = matrix @ theta
        return dict(observations=len(observed),
                    before_rms_m=float(np.sqrt(np.mean(observed**2))),
                    after_rms_m=float(np.sqrt(np.mean((observed-shape)**2))))

    return dict(coefficients=theta.tolist(), earlier_singular_values=singular.tolist(),
                earlier=errors(earlier, earlier_y), later=errors(later, later_y))


def endpoints(first, second, points, saved, support, navigation, ionosphere):
    import numpy as np

    from .gnss_carrier_phase import _atmosphere, _geometry
    from .gnss_position import geodetic, local_rotation

    start, finish = points
    prns, ((a, _), (b, _)), _ = phase_step_geometry(first, second, navigation, support)
    mask_a, _, _ = _atmosphere(start, a, first['seconds'], ionosphere)
    mask_b, _, _ = _atmosphere(start, b, second['seconds'], ionosphere)
    mask = mask_a & mask_b
    end_mask, _, _ = _atmosphere(finish, b, second['seconds'], ionosphere)
    if np.asarray(prns)[mask].tolist() != saved['satellites'] or not end_mask[mask].all():
        raise ValueError('archived satellite mask did not reproduce')

    def mapped(point, satellites):
        satellites = satellites[mask]
        latitude, longitude, _ = geodetic(point)
        delta = satellites-point
        sine = (delta @ local_rotation(latitude, longitude)[2]) / np.linalg.norm(delta, axis=1)
        return _geometry(point, satellites)[1], 1./sine

    return mapped(start, a), mapped(finish, b)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing delay study must be preserved')
    with closing(ClosedStudy(root, 'data/'+GEOMETRY)) as geometry, closing(
            ClosedStudy(root, 'data/'+ACCURACY, store=geometry.store)) as accuracy:
        if (geometry.completion['manifest_sha256'] != GEOMETRY_MANIFEST
                or accuracy.completion['manifest_sha256'] != ACCURACY_MANIFEST
                or not geometry.summary['passed'] or not accuracy.summary['passed']):
            raise ValueError('verified frozen geometry and accuracy replay required')
        materials = {key: geometry.input(key, raw=True) for key in (
            'rinex', 'navigation', 'clock', 'continuity', 'track', 'shape', 'operator', 'baseline'
        )}
        materials['rows'] = encoded([row for task in TASKS for row in
                                      geometry.artifact(task['identity'], 'satellite-influence.json')])
        materials['forecasts'] = accuracy.input('forecasts', raw=True)
        materials['accuracy'] = accuracy.artifact('gps_carrier', 'accuracy.json', raw=True)
    inputs = dict(plan=PLAN)
    for name, raw in materials.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter, tasks=[TASK],
        workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_carrier_delay_fit.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def project_steps(context, track, rows):
    import numpy as np

    from .esa_carrier_clock_step import normalized_epochs
    from .esa_carrier_phase_support import phase_epochs
    from .esa_rinex_code import read_navigation

    points = ecef_track(track)
    epochs = list(phase_epochs(gzip.decompress(context.input_path('rinex').read_bytes())))
    navigation, ionosphere = read_navigation(gzip.decompress(context.input_path('navigation').read_bytes()).decode('ascii'))
    clock = json.loads(context.input_path('clock').read_bytes())['result']
    continuity = json.loads(context.input_path('continuity').read_bytes())['result']['per_pair']
    seconds = np.array([row['seconds'] for row in track], dtype=float)
    elapsed = seconds-seconds[0]
    if (len(track) != COUNT+1 or [row['index'] for row in rows] != list(range(START, END))
            or not np.allclose(elapsed, np.arange(COUNT+1)*.5, rtol=0, atol=.002)):
        raise ValueError('exact archived step indices and time grid required')

    position = np.zeros((COUNT+1, 3, 2))
    columns, residuals = [], []
    for offset, row in enumerate(rows):
        context.charge(bound_calls=1, bound_steps=32)
        index = row['index']
        first, last = epochs[index:index+2]
        support = continuity[index]['accepted_prns']
        if index == clock['pair_index']:
            first, last = normalized_epochs(first, last, clock['integer_clock_step_s'], clock['corrected_elapsed_s'])
            support = clock['supported_prns']
        (a, ma), (b, mb) = endpoints(first, last, points[offset:offset+2], row, support, navigation, ionosphere)
        delay = mapping_difference(ma, mb, elapsed[offset], elapsed[offset+1])
        withheld = np.asarray(row['withheld_range_error_m'])
        position[offset+1], projected, residual = advance(a, b, delay, position[offset], withheld)
        gain = np.linalg.pinv(b)[:3].T
        if (not np.allclose(-gain*withheld[:, None], row['correction_ecef_m'], rtol=1e-8, atol=1e-10)
                or not math.isclose(float(np.sqrt(np.mean(residual**2))), row['perpendicular_rms_m'], abs_tol=1e-10)):
            raise ValueError('archived satellite influence or perpendicular errors did not reproduce')
        columns.append(projected)
        residuals.append(residual)
    return points, position, columns, residuals


def evaluate(task, context):
    import numpy as np

    from .esa_changing_drift_transfer import _chart
    from .gnss_position import geodetic
    from .innovations_snapshot import restore

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != TASK:
        raise ValueError('exact frozen carrier delay task required')

    def load(key):
        return json.loads(context.input_path(key).read_bytes())

    track = load('track')['positions']
    points, position, columns, residuals = project_steps(context, track, load('rows'))
    fit = estimate(columns, residuals, TRAIN_STEPS)
    corrected = [geodetic(row) for row in (points+position @ fit['coefficients'])[::2]]
    original = [row['position'] for row in track[::2]]
    shape = load('shape')
    operator = restore(context.input_path('operator').read_bytes(), expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    origin = np.asarray(original[0])
    shift = _chart(corrected, origin)-_chart(original, origin)
    direction = np.r_[np.zeros(3*CUT), shape['direction']]
    score_change = float(direction @ operator.whiten(shift.ravel()))
    forecasts, archived = load('forecasts'), load('accuracy')['settings']
    if tuple(sorted(forecasts)) != LAWS or len(original) != CUT+LATER:
        raise ValueError('all saved settings and matching times required')
    for law in LAWS:
        live = score_setting(forecasts[law], original[CUT:])
        for model, score in live['scores'].items():
            prior = archived[law]['scores'][model]
            if (not math.isclose(score['total_rms_m'], prior['total_rms_m'], abs_tol=1e-9)
                    or score['accuracy'] != prior['accuracy']):
                raise ValueError('saved carrier accuracy did not reproduce')
    scores = {law: score_setting(forecasts[law], corrected[CUT:]) for law in LAWS}
    baseline = load('baseline')['carrier_signed_midpoint']
    result = dict(fit=fit, steps=COUNT, earlier_steps=TRAIN_STEPS,
        later_shift_rms_m=float(np.sqrt(np.mean(np.sum(shift[CUT:]**2, axis=1)))),
        later_axes_rms_m=np.sqrt(np.mean(shift[CUT:]**2, axis=0)).tolist(),
        baseline_shape_score=baseline, shape_score=baseline+score_change,
        scores=scores, passed=True, scientific_decision='abstain')
    context.save_bytes('delay-fit.json', encoded(result))
    context.save_bytes('corrected-path.json', encoded(dict(positions=corrected)))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != COUNT:
            raise ValueError('all sealed carrier delay steps must complete')
        raw = encoded(study.artifact(TASK['identity'], 'delay-fit.json') |
                      dict(manifest_sha256=study.completion['manifest_sha256']))
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('delay fit report differs')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.esa_carrier_delay_fit {prepare,report}')
    command(Path.cwd())
