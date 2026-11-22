# SPDX-License-Identifier: AGPL-3.0-or-later
"""Six-coordinate earlier-only accelerometer calibration on ESA flight 187."""

from contextlib import closing
from pathlib import Path
import sys

from .esa_direction_bias_training import PARENT, PARENT_SHA
from .esa_force_direction_transfer import FOLDER, TRAINING, FrozenInputs, verified_force_settings
from .esa_gyro_direction_calibration import REPORT as BOUNDS
from .force_accel_calibration import fit_calibration
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-direction-accel-calibration-v1'
SCOPE = 'fit six accelerometer coordinates on the earlier ESA force directions'
PLAN = FOLDER + 'ESA_DIRECTION_ACCEL_CALIBRATION_PLAN.md'
RESULT = FOLDER + 'esa-direction-accel-calibration-result.json'
BOUNDS_SHA = '518941335b83e252acd43ccc690e973903926420ae3d7b5e1c5ca02e1059c4c4'
MAX_CALLS = 200
STARTS = ((0.,)*6, (.5, -.5, .5, -.5, .5, -.5), (-.5, .5, -.5, .5, -.5, .5))
N = 36*len(STARTS)
TASK = dict(identity='six-axis-transfer', input_key='interval', payload=dict(calibration_starts=N),
    limits=dict(native_calls=0, packet_visits=0, bound_calls=N, bound_steps=N*MAX_CALLS))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID + '-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing six-axis freeze must be preserved')
    inputs = {'bounds': BOUNDS}
    with closing(ClosedStudy(root, 'data/' + PARENT)) as previous:
        if previous.completion['manifest_sha256'] != PARENT_SHA or not previous.summary['passed']:
            raise ValueError('exact closed direction study required')
        for key in ('doppler', 'matching', 'direction', 'matched', 'training', 'interval', 'saved-input-binding'):
            target = directory / key
            atomic(target, previous.input(key, raw=True))
            inputs[key] = target.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[TASK],
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_force_accel_calibration.py']),
        workers=1, threads=1, maximum_wall_s=90.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    import numpy as np

    if context.manifest['scope'] != SCOPE or task['payload'] != TASK['payload']:
        raise ValueError('exact joint direction calibration task required')
    inputs = FrozenInputs(context)
    bound_report = inputs.input('bounds')['result']
    if digest(encoded(bound_report)) != BOUNDS_SHA:
        raise ValueError('the existing accelerometer working bounds are required')
    limits = bound_report['working_limits']
    rows = []
    for width, source, nominal, axes, channels, fields in verified_force_settings(inputs, all_axes=True):
        if not np.allclose(nominal, channels.sum(axis=2), atol=1e-12, rtol=0.):
            raise ValueError('axis contributions do not reproduce the nominal force')
        for field, vectors in fields.items():
            scores = {}
            for shape, reference in vectors.items():
                fits = []
                for start in STARTS:
                    context.charge(bound_calls=1, bound_steps=MAX_CALLS)
                    fit = fit_calibration(reference, channels, axes, training=TRAINING,
                        bias_limit=limits['accel_bias'], gain_limit=limits['accel_gain'],
                        start=start, max_calls=MAX_CALLS)
                    fits.append(fit)
                eligible = [i for i, fit in enumerate(fits) if fit['passed']]
                primary = min(eligible, key=lambda i: (fits[i]['training_mean_squared_chord'], i)) if eligible else None
                scores[shape] = dict(starts=fits, primary=primary)
            g, d = (scores[shape]['primary'] for shape in ('globe', 'disc'))
            gap = (scores['disc']['starts'][d]['later_rms_deg']-scores['globe']['starts'][g]['later_rms_deg']
                   if g is not None and d is not None else None)
            rows.append(dict(source=source, width_reports=width, field=field, scores=scores,
                             disc_minus_globe_later_deg=gap))
    context.save_bytes('six-axis-scores.json', encoded(dict(rows=rows, bias_limit_mps2=limits['accel_bias'],
        gain_limit=limits['accel_gain'], raw_gyro_fixed=True, later_data_used_for_selection=False,
        original_data_reads=0, protected_reads=0, full_inertial_fits=0, scientific_decision='abstain')))
    return dict(passed=len(rows)*2*len(STARTS) == N, matched_settings=len(rows), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/' + ID)) as run:
        if not run.summary['passed'] or run.summary['charged']['bound_calls'] != N:
            raise ValueError('complete matched joint calibration required')
        result = run.artifact(TASK['identity'], 'six-axis-scores.json')
        result.update(study_manifest_sha256=run.completion['manifest_sha256'], charged=run.summary['charged'])
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved joint calibration report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_direction_accel_calibration {prepare,report}')
