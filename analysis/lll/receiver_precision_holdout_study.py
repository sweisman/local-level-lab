# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen, saved-data comparison of withheld errors and receiver precision."""

import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

from lll.receiver_precision_holdout import join_epochs, summarize
from lll.studies.artifacts import ArchiveStore, atomic, digest, encoded
from lll.studies.closed import ClosedStudy


PILOT = 'docs/ilvis0-retrospective-prediction-pilot-v2'
PREPARATION = 'data/receiver-precision-holdout-preparation-20261111'
STUDY = 'receiver-precision-holdout-20261111'
RECEIVER = 'docs/ilvis0-trimble-position-precision/recorded-inventory'
SCOPE = ('three preselected NASA recordings; saved withheld errors and '
         'same-receiver precision; zero new fits or original IMU reads')


def recipe():
    return dict(version='receiver-precision-holdout-v1',
                pilot=PILOT, preparation=PREPARATION,
                selected_recordings=3, settings=36,
                numerically_qualified_primaries=28,
                unqualified_settings=8,
                gps_minus_utc_s=15, match_tolerance_ms=20,
                training_coordinate_tolerance_m=.01,
                model_fits=0, original_imu_reads=0, protected_esa_reads=0,
                workers=1, threads=1, maximum_wall_s=600,
                recovery=dict(version='lll-task-resume-v1',
                              max_attempts_per_task=3,
                              max_technical_interruptions=3,
                              continuation_wall_s=600,
                              minimum_free_bytes=2 * 1024**3))


def select_primaries(tasks, outcomes):
    """Choose each start by training cost only; never inspect held-out errors."""
    if len(tasks) != 72 or set(tasks) != set(outcomes):
        raise ValueError('complete 72-task retrospective pilot required')
    grouped = {}
    for identity, task in tasks.items():
        payload = task['payload']
        key = (payload['segment_id'], payload['model'],
               payload['profile'], payload['clock'])
        grouped.setdefault(key, []).append((identity, payload['start']))
    if len(grouped) != 36 or any(len(v) != 2 or {x[1] for x in v} != {0, 1}
                                 for v in grouped.values()):
        raise ValueError('complete paired-start settings required')
    selected = []
    for key, starts in sorted(grouped.items()):
        qualified = []
        for identity, start in starts:
            result = outcomes[identity]
            if (result.get('converged') is True
                    and result.get('all_active_columns_retained') is True):
                cost = result.get('training_cost')
                if (not isinstance(cost, (int, float)) or isinstance(cost, bool)
                        or not math.isfinite(cost)):
                    raise ValueError('finite training cost required')
                qualified.append((cost, start, identity))
        chosen = min(qualified)[2] if qualified else None
        selected.append(dict(segment_id=key[0], model=key[1],
                             profile=key[2], clock=key[3],
                             chosen_identity=chosen,
                             numerical_status=('qualified' if chosen else
                                               'no_qualified_start')))
    if (len({row['segment_id'] for row in selected}) != 3
            or sum(row['chosen_identity'] is not None for row in selected) != 28):
        raise ValueError('frozen pilot numerical coverage differs')
    return selected


def _position_rows(blob):
    return list(csv.DictReader(io.StringIO(gzip.decompress(blob).decode('utf-8'))))


def stage_inputs(root):
    """Verify closed evidence and stage only three compact, hash-bound inputs."""
    root = Path(root).resolve()
    base = root / PREPARATION
    if base.exists() or (root / 'data' / STUDY).exists():
        raise ValueError('fresh receiver-precision preparation required')
    pilot = ClosedStudy(root, PILOT)
    store = ArchiveStore(root)
    try:
        selection_name = 'docs/ilvis0-prediction-pilot-preparation/selection.csv'
        selection_blob = store.read(selection_name)
        selection = list(csv.DictReader(io.StringIO(selection_blob.decode())))
        preparation_name = 'data/ilvis0-rt27-position-preparation-20261110/summary.json'
        inventory_name = 'data/ilvis0-rt27-position-inventory-20261110-v2/summary.json'
        receipt_name = RECEIVER + '/evidence-receipt.json'
        source_blobs = {name: store.read(name) for name in
                        (preparation_name, inventory_name, receipt_name)}
        preparation = json.loads(source_blobs[preparation_name])
        inventory = json.loads(source_blobs[inventory_name])
        receipt = json.loads(source_blobs[receipt_name])
        by_source = {row['source_sha256']: row for row in preparation['records']}
        passed = {row['identity'] for row in inventory['results']
                  if row['passed'] is True}
        outcomes = {identity: pilot.envelope(identity)['result']
                    for identity in pilot.tasks}
        primaries = select_primaries(pilot.tasks, outcomes)
        if (len(selection) != 3 or len(by_source) != len(preparation['records'])
                or len({row['segment_id'] for row in selection}) != 3):
            raise ValueError('three distinct preselected receiver streams required')
        staged = {}
        material = {}
        for selected in selection:
            sid = selected['segment_id']
            record = by_source[selected['source_sha256']]
            file_id = record['task']
            if file_id not in passed or record['leap_seconds'] != 15:
                raise ValueError('passed same-receiver 2009–2010 precision required')
            name = 'artifacts/' + file_id + '/positions.csv.gz'
            receiver_blob = store.read(RECEIVER + '/' + name)
            if digest(receiver_blob) != receipt['artifacts'][name]:
                raise ValueError('published precision table hash differs')
            positions = _position_rows(receiver_blob)
            if len({int(row['gps_week']) for row in positions}) != 1:
                raise ValueError('one receiver GPS week required')
            gps_week = int(positions[0]['gps_week'])
            input_blob = pilot.input(sid + '-measurements', raw=True)
            measurement = json.loads(gzip.decompress(input_blob))
            if (measurement['segment_id'] != sid
                    or measurement['layout']['segment_id'] != sid):
                raise ValueError('unchanged pilot measurement identity required')
            epoch_sets = {}
            for row in primaries:
                if row['segment_id'] != sid or row['chosen_identity'] is None:
                    continue
                identity = row['chosen_identity']
                epochs = pilot.artifact(identity, 'epochs.json')
                join_epochs(
                    epochs, positions,
                    origin_utc_week_s=measurement['layout'][
                        'first_interval_start_utc_s'],
                    expected_gps_week=gps_week,
                    training_coordinates=measurement['training_gps'])
                epoch_sets[identity] = epochs
            material[sid] = dict(segment_id=sid, filename=selected['filename'],
                                 source_sha256=selected['source_sha256'],
                                 receiver_task=file_id, gps_week=gps_week,
                                 origin_utc_week_s=measurement['layout'][
                                     'first_interval_start_utc_s'],
                                 training_gps=measurement['training_gps'],
                                 pilot_measurement_sha256=digest(input_blob),
                                 selected_epochs=epoch_sets)
            staged[sid] = dict(positions=receiver_blob,
                               material=gzip.compress(encoded(material[sid]),
                                                      mtime=0))
        source_hashes = {name: digest(blob) for name, blob in
                         source_blobs.items()}
        source_hashes[selection_name] = digest(selection_blob)
        summary = dict(version='receiver-precision-preparation-v1',
                       recipe=recipe(), primaries=primaries,
                       pilot_manifest_sha256=pilot.completion['manifest_sha256'],
                       pilot_summary_sha256=pilot.completion['summary_sha256'],
                       frozen_sources=source_hashes,
                       segments={}, model_fits=0,
                       original_imu_reads=0, protected_esa_reads=0)
        for sid, pair in staged.items():
            record = by_source[next(row['source_sha256'] for row in selection
                                    if row['segment_id'] == sid)]
            prefix = 'inputs/' + sid
            summary['segments'][sid] = dict(
                receiver_task=record['task'],
                material=dict(path=(base / (prefix + '-material.json.gz')).relative_to(
                    root).as_posix(), sha256=digest(pair['material'])),
                positions=dict(path=(base / (prefix + '-positions.csv.gz')).relative_to(
                    root).as_posix(), sha256=digest(pair['positions'])))
        base.mkdir(parents=True)
        for sid, pair in staged.items():
            prefix = base / 'inputs' / sid
            atomic(Path(str(prefix) + '-material.json.gz'), pair['material'])
            atomic(Path(str(prefix) + '-positions.csv.gz'), pair['positions'])
        atomic(base / 'summary.json', encoded(summary))
        return summary
    finally:
        pilot.close()
        store.close()


def checked_preparation(root):
    """Reuse only the exact staged bytes and original closed input versions."""
    root = Path(root).resolve()
    base = root / PREPARATION
    summary = json.loads((base / 'summary.json').read_bytes())
    if (summary.get('version') != 'receiver-precision-preparation-v1'
            or summary.get('recipe') != recipe()
            or len(summary.get('segments', {})) != 3
            or len(summary.get('primaries', [])) != 36):
        raise ValueError('complete unchanged staged comparison required')
    for part in summary['segments'].values():
        for record in part.values():
            if isinstance(record, dict) and 'path' in record:
                if digest((root / record['path']).read_bytes()) != record['sha256']:
                    raise ValueError('staged receiver comparison hash changed')
    store = ArchiveStore(root)
    pilot = ClosedStudy(root, PILOT)
    try:
        if (summary['pilot_manifest_sha256'] != pilot.completion['manifest_sha256']
                or summary['pilot_summary_sha256'] != pilot.completion['summary_sha256']):
            raise ValueError('closed retrospective pilot changed')
        for name, sha in summary['frozen_sources'].items():
            if digest(store.read(name)) != sha:
                raise ValueError('staged source evidence changed')
    finally:
        pilot.close()
        store.close()
    return summary


def qualification_sources(root):
    from lll.studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/receiver_precision_holdout_study.py',
        'analysis/lll/receiver_precision_holdout.py',
        'analysis/tests/test_receiver_precision_holdout_study.py',
        'analysis/tests/test_receiver_precision_holdout.py',
        'docs/receiver-precision-holdout/PLAN.md'])


def required_tests():
    return [
        'test_select_primaries_uses_training_cost_only_and_keeps_missing_settings',
        'test_evaluate_uses_frozen_saved_rows_and_never_refits',
        'test_exact_receiver_join_checks_earlier_coordinates_and_later_support',
        'test_receiver_join_rejects_missing_epoch_and_wrong_earlier_position']


def prepare(root, *, qualification, recovery_qualification):
    """Freeze three zero-native tasks after source and recovery qualification."""
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)

    root = Path(root).resolve()
    if (root / 'data' / STUDY).exists():
        raise ValueError('fresh finite receiver-precision study required')
    env = runtime_environment()
    request, report = checked(root, qualification,
                              sources=qualification_sources(root),
                              environment=env,
                              required_tests=required_tests(), minimum_tests=4)
    recovery_request, recovery_report = checked(
        root, recovery_qualification,
        sources=recovery_sources(root), environment=env,
        required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    summary = checked_preparation(root)
    base = root / PREPARATION
    qualification_files = dict(
        **{'software-request': request, 'software-report': report,
           'recovery-request': recovery_request,
           'recovery-report': recovery_report,
           'runtime-environment': encoded(env)})
    inputs = {'preparation': (base / 'summary.json').relative_to(root).as_posix()}
    for key, blob in qualification_files.items():
        destination = base / ('qualification-' + key)
        atomic(destination, blob)
        inputs[key] = destination.relative_to(root).as_posix()
    tasks = []
    for index, (sid, record) in enumerate(sorted(summary['segments'].items())):
        inputs['material-' + sid] = record['material']['path']
        inputs['positions-' + sid] = record['positions']['path']
        tasks.append(dict(identity=sid, index=index, shard=0,
                          input_key='material-' + sid,
                          payload=dict(segment_id=sid,
                                       receiver_task=record['receiver_task']),
                          limits=dict(native_calls=0, packet_visits=0,
                                      bound_calls=0, bound_steps=0)))
    definition = dict(id=STUDY, scope=SCOPE,
                      adapter='analysis/lll/receiver_precision_holdout_study.py',
                      sources=qualification_sources(root),
                      inputs=inputs, tasks=tasks,
                      workers=1, threads=1, maximum_wall_s=600)
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + STUDY,
                allocation=manifest['allocation'],
                limits=manifest['limits'])


def evaluate(task, context):
    """One segment of saved predictions; no numerical model evaluation."""
    design = recipe()
    if (context.manifest.get('scope') != SCOPE
            or task not in context.manifest['tasks']):
        raise ValueError('unchanged frozen receiver-precision task required')
    summary = json.loads(context.input_path('preparation').read_bytes())
    if summary['recipe'] != design or task['identity'] not in summary['segments']:
        raise ValueError('unchanged receiver-precision preparation required')
    sid = task['identity']
    material = json.loads(gzip.decompress(context.input_path(
        'material-' + sid).read_bytes()))
    positions = _position_rows(context.input_path('positions-' + sid).read_bytes())
    if material['segment_id'] != sid:
        raise ValueError('unchanged selected recording required')
    reports = []
    for row in summary['primaries']:
        if row['segment_id'] != sid:
            continue
        identity = row['chosen_identity']
        if identity is None:
            reports.append(dict(**row, report=None))
            continue
        joined = join_epochs(
            material['selected_epochs'][identity], positions,
            origin_utc_week_s=material['origin_utc_week_s'],
            expected_gps_week=material['gps_week'],
            training_coordinates=material['training_gps'])
        context.save_bytes('matched-' + identity + '.json.gz',
                           gzip.compress(encoded(joined), mtime=0))
        reports.append(dict(**row, report=summarize(joined)))
    if len(reports) != 12:
        raise ValueError('twelve settings per recording required')
    context.save('precision-comparison.json', reports)
    return dict(passed=True, segment_id=sid,
                qualified_primaries=sum(row['report'] is not None
                                        for row in reports),
                no_qualified_start=sum(row['report'] is None
                                       for row in reports),
                scientific_decision='abstain', model_fits=0,
                original_imu_reads=0, protected_esa_reads=0)
