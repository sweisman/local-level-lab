# SPDX-License-Identifier: AGPL-3.0-or-later
"""Evaluate two measured force magnitudes against matched shape predictions."""

from contextlib import closing
from pathlib import Path
import sys

from . import esa_direction_angle_pairs as pairs
from . import esa_direction_window_transfer as transfer
from .esa_doppler_force import CENTERS, GRAVITY_LAWS, WIDTHS, coordinate_rates, predicted_force_batch, rate_operator
from .esa_rinex_code_comparison import coordinates
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-girafe-force-contrast-v4'
SCOPE = 'compare matched shape predictions with the saved GIRAFE and raw iMAR magnitudes on ESA 187'
PLAN = transfer.FOLDER + 'ESA_GIRAFE_FORCE_CONTRAST_PLAN.md'
ACCOUNTING = transfer.FOLDER + 'ESA_GIRAFE_FORCE_CONTRAST_ACCOUNTING.md'
BATCH = transfer.FOLDER + 'ESA_GIRAFE_FORCE_CONTRAST_BATCH.md'
LEDGER = transfer.FOLDER + 'ESA_GIRAFE_FORCE_CONTRAST_LEDGER_BLOCK.md'
RESULT = transfer.FOLDER + 'esa-girafe-force-contrast-result.json'
V2 = 'data/esa-girafe-force-contrast-v2'
V2_SHA = '00b1d04f123ac9b9dd46f91f27ba3d79fbedc5298a7f613a53029160f0a6c386'
V3 = 'data/esa-girafe-force-contrast-v3'
V3_SHA = '376f7bf0e5fc84e8c5321605f5be5d9380c11b1d47a567902d5c10a0bafc06c0'
CONTRASTS = {
    'zero_field': ('sphere_still', 'flat_still'),
    'specified_field': ('sphere_rotating', 'flat_geographic_field'),
}
MODELS = tuple(model for pair in CONTRASTS.values() for model in pair)
AVERAGES_PER_SUPPORT = len(MODELS)*len(GRAVITY_LAWS)
AVERAGES = len(CENTERS)*AVERAGES_PER_SUPPORT
TASKS = pairs.TASKS
LAST, = (task for task in TASKS if task['identity'] == 'turn-41116')
PENDING = LAST | dict(input_key=LAST['identity'], limits=dict(native_calls=0, packet_visits=0,
    bound_calls=3*len(WIDTHS)*len(CENTERS), bound_steps=3*sum(4*(width-1)*AVERAGES for width in WIDTHS)))


def _require_split(study, expected_sha, expected_passes, failure):
    passed = {name for name, row in study.rows.items() if row['passed']}
    interrupted = set(study.rows)-passed
    if (study.completion['manifest_sha256'] != expected_sha or study.completion['state'] != 'terminal'
            or passed != expected_passes or interrupted != {failure}
            or study.envelope(failure)['result']['error_type'] != 'BudgetStopped'):
        raise ValueError('original passes and the recorded cooperative time cap are required')


def _check_scalar(study):
    expected = {task['identity'] for task in TASKS if task['payload']['kind'] == 'straight'}
    _require_split(study, V2_SHA, expected, 'turn-22936')


def _check_batched(study):
    expected = {task['identity'] for task in TASKS if task['payload']['kind'] == 'turn'}-{'turn-41116'}
    _require_split(study, V3_SHA, expected, 'turn-41116')


def earlier_offset_difference(measured, predicted, *, earlier):
    import numpy as np

    m, p = (np.asarray(a, float) for a in (measured, predicted))
    if (m.shape != p.shape or m.ndim != 1 or not 0 < earlier < len(m)
            or not np.isfinite(m).all() or not np.isfinite(p).all()):
        raise ValueError('finite matched earlier and later measurements required')
    difference = m-p
    offset = float(np.mean(difference[:earlier]))
    return offset, difference[earlier:]-offset


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing force-contrast freeze must stay intact')
    with closing(ClosedStudy(root, V3)) as parent:
        _check_batched(parent)
        key = PENDING['identity']
        target = directory / key
        atomic(target, parent.input(key, raw=True))
        inputs = {key: target.relative_to(root).as_posix()}
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=[PENDING],
        sources=source_closure(root, [adapter, PLAN, ACCOUNTING, BATCH, LEDGER,
            'analysis/tests/test_esa_girafe_force_contrast.py', 'analysis/tests/test_receiver_force_batch.py']),
        workers=1, threads=1, maximum_wall_s=60.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _source_predictions(rows, reference_times, width, charge):
    import numpy as np

    time = np.asarray(reference_times)
    coordinate = np.asarray(coordinates(rows))
    coordinate[:, 1] = np.unwrap(coordinate[:, 1])
    rates = coordinate_rates(coordinate, [[r[k] for k in ('north_mps', 'east_mps', 'up_mps')] for r in rows])
    predictions = {law: {model: [] for model in MODELS} for law in GRAVITY_LAWS}
    half = width//2
    for index in CENTERS:
        charge(bound_calls=1, bound_steps=4*(width-1)*AVERAGES_PER_SUPPORT)
        sl = slice(index-half, index+half+1)
        relative = time[sl]-time[index]
        op, kernel = rate_operator(relative)
        coefficients = op @ rates[sl]
        for law, models in predictions.items():
            for model, output in models.items():
                output.append(predicted_force_batch(relative, kernel, coordinate[index],
                    coefficients, model, law, coordinate[0, 2]))
    return predictions


def _offset_rms(measured, predicted):
    import numpy as np

    offset, later = earlier_offset_difference(measured, predicted, earlier=transfer.TRAINING)
    return dict(earlier_offset_mps2=offset, rms_mps2=float(np.sqrt(np.mean(later**2))))


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared != PENDING:
        raise ValueError('exact GIRAFE contrast task required')
    data = transfer.FrozenInputs(context).input(task['identity'])
    measured = data['measured']
    sources = {'air1': data['primary']}
    sources.update({name: entry['rows'] for name, entry in data['alternatives'].items() if entry['matched'] == 400})
    reference_times = [row['time_s'] for row in data['primary']]
    result = []
    for width in measured['widths']:
        width_reports = width['width_reports']
        if width_reports not in WIDTHS:
            raise ValueError('force averaging width changed')
        logged, = (a for a in width['alignments'] if a['girafe_clock_shift_s'] == 0.)
        signals = dict(girafe=logged['girafe_magnitude_mps2'], imar=width['imar_magnitude_mps2']['raw'])
        predictions = {}
        for source, rows in sources.items():
            predictions[source] = _source_predictions(rows, reference_times, width_reports, context.charge)
        comparisons = []
        for source, source_laws in predictions.items():
            for law, models in source_laws.items():
                contrasts = {key: _offset_rms(models[globe], models[disc])
                             for key, (globe, disc) in CONTRASTS.items()}
                scores = {sensor: {model: _offset_rms(values, prediction)
                                   for model, prediction in models.items()} for sensor, values in signals.items()}
                receiver_effect = {model: _offset_rms(models[model], predictions['air1'][law][model])
                                   for model in MODELS} if source != 'air1' else {}
                comparisons.append(dict(source=source, gravity=law, models_mps2=models, contrasts=contrasts,
                                        scores=scores, receiver_effect_vs_air1=receiver_effect))
        result.append(dict(width_reports=width_reports, sensor_magnitudes_mps2=signals,
                           sensor_difference=_offset_rms(signals['girafe'], signals['imar']),
                           comparisons=comparisons))
    row = dict(window=measured['window'], kind=measured['kind'], widths=result,
               receiver_counts={'air1': 400, **{k: v['matched'] for k, v in data['alternatives'].items()}},
               scientific_decision='abstain')
    context.save_bytes('force-contrast.json', encoded(row))
    return dict(passed=len(result) == len(WIDTHS), scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study, closing(ClosedStudy(root, V2)) as scalar, closing(
            ClosedStudy(root, V3)) as batched:
        _check_scalar(scalar)
        _check_batched(batched)
        last = PENDING['identity']
        if not study.summary['passed'] or set(study.rows) != {last}:
            raise ValueError('complete final turning-window force contrast required')
        windows = []
        for task in TASKS:
            name = task['identity']
            source = study if name == last else (scalar if task['payload']['kind'] == 'straight' else batched)
            row = source.artifact(name, 'force-contrast.json')
            n = sum(count == 400 for count in row['receiver_counts'].values())
            charge = source.rows[name]['charged']
            calls_per_width = len(CENTERS) if name == last else AVERAGES
            if (charge['bound_calls'] != n*len(WIDTHS)*calls_per_width
                    or charge['bound_steps'] != n*sum(4*(w-1)*AVERAGES for w in WIDTHS)):
                raise ValueError('force contrast scores and forecast charges differ')
            windows.append(row)
        charged = {key: sum(s.summary['charged'][key] for s in (scalar, batched, study))
                   for key in study.summary['charged']}
        result = dict(windows=windows, charged=charged, scalar_manifest_sha256=V2_SHA,
                      batched_manifest_sha256=V3_SHA, scalar_charged=scalar.summary['charged'],
                      batched_charged=batched.summary['charged'], support_charged=study.summary['charged'],
                      manifest_sha256=study.completion['manifest_sha256'], protected_reads=0,
                      gyro_samples_used=0, native_fits=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved GIRAFE force contrast report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_girafe_force_contrast {prepare,report}')
