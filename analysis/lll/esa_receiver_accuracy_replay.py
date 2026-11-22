# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the original observed position screen against sealed receiver alternatives."""

from contextlib import closing
import json
import math
from pathlib import Path
import sys

from .esa_alternate_ppp_scoring import MODELS, rank_setting, score_errors
from .esa_carrier_phase_continuous import ID as GPS, TASK as GPS_TASK
from .esa_final_orbit_score import MATRIX, MATRIX_SHA, PPP, PPP_SHA, _load
from .esa_galileo_phase_path import ID as GALILEO, TASK as GALILEO_TASK
from .esa_glonass_phase_path import ID as GLONASS, TASK as GLONASS_TASK
from .esa_parallel_raw_receiver import FIRST_SHARED, LAST_SHARED
from .esa_rinex_window import FOLDER
from .esa_shape_receiver_replay import EARLIER, LATER, PATHS, _inputs
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-receiver-accuracy-replay-v1'
PLAN = FOLDER+'ESA_RECEIVER_ACCURACY_REPLAY_PLAN.md'
RESULT = FOLDER+'esa-receiver-accuracy-replay-result.json'
SCOPE = 'fixed six-forecast position screen across twelve sealed ESA development receiver paths'
LAWS = ('increment', 'point')
CARRIERS = ('gps_carrier', 'glonass_carrier', 'galileo_mosaic03', 'galileo_pwrpak7')
RECEIVERS = PATHS + CARRIERS
GPS_MANIFEST = '93fcfc884ffe80067ae434f2d6a9abdb272337c732847a2541d620b768781d43'
GLONASS_MANIFEST = '33c0dcbff856a13df142e2c2d90fc3d4fcd473843cb3b1a0ff23a6b253619440'
GALILEO_MANIFEST = '3e99ea3611e8417d0502f0422d9cbf20580bffdd4cb03e15cee88cf7a7f28a0d'


def task_for(name):
    return dict(identity=name, input_key=name, payload=dict(receiver=name),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=6, bound_steps=6))


def score_setting(forecasts, receiver, *, reserve=lambda: None):
    import numpy as np

    from .airquantumgrav_scoring import receiver_errors
    from .esa_shared_receiver_error import position_limit_margins
    from .ilvis0_prediction_observed import recipe

    errors, scores = {}, {}
    for model in MODELS:
        reserve()
        error = receiver_errors(forecasts[model], receiver)
        errors[model] = error
        scores[model] = score_errors(error, np.zeros_like(error), range(len(error)))
    ranked = rank_setting(scores)
    preference = ranked['shape_lower_error_family']
    picked = ranked['lower_error_globe_model'] if preference == 'globe' else 'flat_still' if preference == 'flat' else None
    limits = recipe()['accuracy_limits']
    return dict(scores=scores, ranking=ranked,
        headroom_m={field: limit-scores[picked][field] for field, limit in limits.items()} if picked else None,
        minimum_breaking_shift_rms_m=position_limit_margins(errors[picked], limits) if picked else None)


def _carrier_inputs(root, store):
    result, receipts = {}, {}
    for label, identity, manifest, task in (('gps_carrier', GPS, GPS_MANIFEST, GPS_TASK),
                                           ('glonass_carrier', GLONASS, GLONASS_MANIFEST, GLONASS_TASK),
                                           ('galileo', GALILEO, GALILEO_MANIFEST, GALILEO_TASK)):
        with closing(ClosedStudy(root, 'data/'+identity, store=store)) as run:
            if run.completion['manifest_sha256'] != manifest or not run.summary['passed']:
                raise ValueError('exact verified carrier path required')
            if label == 'galileo':
                paths = run.artifact(task['identity'], 'galileo-paths.json')['paths']
                if set(paths) != {'mosaic03', 'pwrpak7'}:
                    raise ValueError('both original Galileo tracks required')
                result.update({label+'_'+name: path for name, path in paths.items()})
            else:
                track = run.artifact(task['identity'], 'carrier-path.json')['positions'][::2]
                if [row['seconds'] for row in track] != list(range(FIRST_SHARED, LAST_SHARED+1)):
                    raise ValueError('carrier path times do not match the original score grid')
                result[label] = [row['position'] for row in track]
            receipts[label] = {k: run.completion[k] for k in ('manifest_sha256', 'summary_sha256')}
    return result, receipts


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing receiver screen must be preserved')
    times, _, _, _, paths, bindings = _inputs(root)
    previous = _load(root, PPP, PPP_SHA)
    settings = {row['law']: row for row in previous['settings'] if row['profile']}
    if tuple(sorted(settings)) != LAWS or previous['common_parent_indices'] != list(range(LATER)):
        raise ValueError('both complete original settings and all 120 later times required')
    with closing(ArchiveStore(root)) as store:
        carriers, receipts = _carrier_inputs(root, store)
        with closing(ClosedStudy(root, MATRIX, store=store)) as matrix:
            if (matrix.completion['manifest_sha256'] != MATRIX_SHA
                    or matrix.completion['summary_sha256'] != previous['matrix_summary_sha256']):
                raise ValueError('exact earlier-only forecast matrix required')
            forecasts = {}
            for law, setting in settings.items():
                forecasts[law] = {}
                for model in MODELS:
                    identity = f"{model}-1-{law}-{setting['primary_start'][model]}"
                    raw = matrix.artifact(identity, 'forecast.json', raw=True)
                    track = json.loads(raw)
                    if (digest(raw) != setting['forecast_sha256'][model]
                            or track['training_epochs'] != EARLIER or track['prediction_epochs'] != LATER
                            or track['times_s'] != times or len(track['coordinates']) != EARLIER+LATER
                            or track['prediction_receiver_positions_used'] is not False):
                        raise ValueError('unchanged raw forecast and same later times required')
                    forecasts[law][model] = track['coordinates'][EARLIER:]
            bindings.update(matrix_manifest_sha256=MATRIX_SHA, forecasts={law: setting['forecast_sha256']
                            for law, setting in settings.items()}, carrier_studies=receipts)
    paths.update(carriers)
    if set(paths) != set(RECEIVERS) or any(len(path) != EARLIER+LATER for path in paths.values()):
        raise ValueError('all twelve receiver paths must cover the full original comparison')
    materials = {name: path[EARLIER:] for name, path in paths.items()}
    materials.update(forecasts=forecasts, bindings=bindings)
    materials['original-checks'] = {law: settings[law]['by_receiver']['air1'] for law in LAWS}
    inputs = dict(plan=PLAN, earlier_receiver_report=PPP)
    for name, content in materials.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, encoded(content))
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[task_for(name) for name in RECEIVERS], workers=1, threads=1, maximum_wall_s=60.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_receiver_accuracy_replay.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    name = task['payload']['receiver']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or name not in RECEIVERS or declared != task_for(name):
        raise ValueError('exact receiver accuracy task required')
    receiver = json.loads(context.input_path(name).read_bytes())
    forecasts = json.loads(context.input_path('forecasts').read_bytes())
    if len(receiver) != LATER or tuple(sorted(forecasts)) != LAWS:
        raise ValueError('original paired receiver times and both forecast settings required')
    scores = {law: score_setting(forecasts[law], receiver,
                  reserve=lambda: context.charge(bound_calls=1, bound_steps=1)) for law in LAWS}
    if name == 'original':
        prior = json.loads(context.input_path('original-checks').read_bytes())
        if any(not math.isclose(row['total_rms_m'], prior[law]['scores'][model]['total_rms_m'], abs_tol=1e-9)
                or row['accuracy'] != prior[law]['scores'][model]['accuracy']
                for law, result in scores.items() for model, row in result['scores'].items()):
            raise ValueError('archived original raw forecast accuracy did not reproduce')
    result = dict(receiver=name, family='carrier' if name in CARRIERS else 'original' if name == 'original' else 'code',
                  settings=scores, later_epochs=LATER, passed=True, scientific_decision='abstain')
    context.save_bytes('accuracy.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != len(RECEIVERS)*6:
            raise ValueError('all twelve sealed receiver paths must complete')
        raw = encoded(dict(manifest_sha256=study.completion['manifest_sha256'],
            receivers=[study.artifact(name, 'accuracy.json') for name in RECEIVERS], scientific_decision='abstain'))
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('receiver accuracy report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_receiver_accuracy_replay {prepare,report}')
