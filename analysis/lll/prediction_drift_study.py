# SPDX-License-Identifier: AGPL-3.0-or-later
"""Three-task saved-data test of earlier-only residual extrapolation."""

import gzip
import json
import math
from pathlib import Path

from lll.prediction_drift_control import evaluate as score_drift
from lll.studies.artifacts import atomic, digest, encoded
from lll.studies.closed import ClosedStudy


PILOT = 'docs/ilvis0-retrospective-prediction-pilot-v2'
PARENT = 'data/receiver-precision-holdout-20261111'
PREPARATION = 'data/prediction-drift-preparation-20261111'
STUDY = 'prediction-drift-control-20261111'
SCOPE = ('three preselected retrospective recordings; earlier-only residual '
         'mean and linear trend; no new Earth-model fits or original reads')


def recipe():
    return dict(version='prediction-drift-control-v1',
                pilot=PILOT, parent=PARENT,
                training_window_s=120., minimum_training_epochs=100,
                selected_recordings=3, settings=36,
                numerically_qualified_primaries=28,
                unqualified_settings=8, workers=1, threads=1,
                maximum_wall_s=600, model_fits=0,
                original_imu_reads=0, protected_esa_reads=0,
                recovery=dict(version='lll-task-resume-v1',
                              max_attempts_per_task=3,
                              max_technical_interruptions=3,
                              continuation_wall_s=600,
                              minimum_free_bytes=2 * 1024**3))


def baseline_metrics(prediction):
    return {key: prediction[key] for key in
            ('north_rms_m', 'east_rms_m', 'vertical_rms_m',
             'horizontal_rms_m')}


def require_baseline(actual, expected):
    mapping = dict(north_rms_m='north_rms_m',
                   east_rms_m='east_rms_m',
                   vertical_rms_m='height_rms_m',
                   horizontal_rms_m='horizontal_rms_m')
    if (set(expected) != set(mapping)
            or any(not isinstance(expected[key], (int, float))
                   or not math.isfinite(expected[key])
                   or actual['scores']['original'][source] != expected[key]
                   for key, source in mapping.items())):
        raise ValueError('saved uncorrected pilot prediction differs')


def qualification_sources(root):
    from lll.studies.dependencies import source_closure

    return source_closure(Path(root).resolve(), [
        'analysis/lll/prediction_drift_study.py',
        'analysis/lll/prediction_drift_control.py',
        'analysis/tests/test_prediction_drift_study.py',
        'analysis/tests/test_prediction_drift_control.py',
        'docs/prediction-drift-control/PLAN.md'])


def required_tests():
    return [
        'test_exact_earlier_trend_predicts_later_without_using_later_for_fit',
        'test_changed_later_values_cannot_change_earlier_correction',
        'test_unsupported_training_window_or_role_change_rejected',
        'test_study_keeps_all_settings_and_exact_original_scores',
        'test_study_rejects_changed_uncorrected_baseline']


def stage_inputs(root):
    """Stage hash-checked prior inputs and scores without an original read."""
    from lll.receiver_precision_holdout_study import checked_preparation

    root = Path(root).resolve()
    base = root / PREPARATION
    if base.exists() or (root / 'data' / STUDY).exists():
        raise ValueError('fresh finite drift preparation required')
    parent_preparation = checked_preparation(root)
    selected = parent_preparation['primaries']
    if (len(selected) != 36
            or sum(row['chosen_identity'] is not None for row in selected) != 28):
        raise ValueError('complete verified parent selection required')
    parent = ClosedStudy(root, PARENT)
    pilot = ClosedStudy(root, PILOT)
    try:
        if (parent.completion['state'] != 'complete'
                or parent.summary['completed'] != 3
                or parent.summary['charged']['native_calls'] != 0):
            raise ValueError('closed zero-fit parent study required')
        staged = {}
        references = {}
        for sid in sorted(parent.tasks):
            blob = parent.input('material-' + sid, raw=True)
            material = json.loads(gzip.decompress(blob))
            if material['segment_id'] != sid:
                raise ValueError('parent material identity changed')
            staged[sid] = blob
        for selection in selected:
            identity = selection['chosen_identity']
            if identity is None:
                continue
            saved = pilot.envelope(identity)['result']['prediction']
            reference = baseline_metrics(saved)
            references[identity] = reference
        if len(references) != 28:
            raise ValueError('all selected pilot scores required')
        summary = dict(version='prediction-drift-preparation-v1',
                       recipe=recipe(),
                       parent_preparation_sha256=digest(encoded(
                           parent_preparation)),
                       parent_manifest_sha256=parent.completion['manifest_sha256'],
                       parent_summary_sha256=parent.completion['summary_sha256'],
                       pilot_manifest_sha256=pilot.completion['manifest_sha256'],
                       pilot_summary_sha256=pilot.completion['summary_sha256'],
                       selected_settings=selected,
                       baseline_reference=references,
                       material_sha256={sid: digest(blob) for sid, blob
                                        in staged.items()},
                       model_fits=0, original_imu_reads=0,
                       protected_esa_reads=0)
        base.mkdir(parents=True)
        for sid, blob in staged.items():
            atomic(base / (sid + '-material.json.gz'), blob)
        atomic(base / 'summary.json', encoded(summary))
        return summary
    finally:
        parent.close()
        pilot.close()


def checked_preparation(root):
    from lll.receiver_precision_holdout_study import (
        checked_preparation as checked_parent_preparation)

    root = Path(root).resolve()
    base = root / PREPARATION
    summary = json.loads((base / 'summary.json').read_bytes())
    if (summary.get('recipe') != recipe()
            or len(summary.get('selected_settings', [])) != 36
            or len(summary.get('baseline_reference', {})) != 28
            or len(summary.get('material_sha256', {})) != 3):
        raise ValueError('complete unchanged drift preparation required')
    parent = ClosedStudy(root, PARENT)
    pilot = ClosedStudy(root, PILOT)
    try:
        if summary['parent_preparation_sha256'] != digest(encoded(
                checked_parent_preparation(root))):
            raise ValueError('selected parent preparation changed')
        if (summary['parent_manifest_sha256'] != parent.completion['manifest_sha256']
                or summary['parent_summary_sha256'] != parent.completion['summary_sha256']
                or summary['pilot_manifest_sha256'] != pilot.completion['manifest_sha256']
                or summary['pilot_summary_sha256'] != pilot.completion['summary_sha256']):
            raise ValueError('closed parent or pilot source changed')
        for sid, sha in summary['material_sha256'].items():
            if (digest((base / (sid + '-material.json.gz')).read_bytes()) != sha
                    or digest(parent.input('material-' + sid, raw=True)) != sha):
                raise ValueError('staged saved epochs changed')
    finally:
        parent.close()
        pilot.close()
    return summary


def prepare(root, *, qualification, recovery_qualification):
    from lll.ilvis0_control_shards import runtime_environment
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition
    from lll.studies.task_resume import (qualification_sources as recovery_sources,
                                         REQUIRED_TESTS as recovery_tests)

    root = Path(root).resolve()
    base = root / PREPARATION
    if (root / 'data' / STUDY).exists():
        raise ValueError('fresh finite drift study required')
    environment = runtime_environment()
    request, report = checked(root, qualification,
                              sources=qualification_sources(root),
                              environment=environment,
                              required_tests=required_tests(), minimum_tests=5)
    recovery_request, recovery_report = checked(
        root, recovery_qualification,
        sources=recovery_sources(root), environment=environment,
        required_tests=recovery_tests,
        minimum_tests=len(recovery_tests))
    summary = checked_preparation(root)
    files = dict(software_request=request, software_report=report,
                 recovery_request=recovery_request,
                 recovery_report=recovery_report,
                 runtime_environment=encoded(environment))
    inputs = {'preparation': (base / 'summary.json').relative_to(root).as_posix()}
    for key, blob in files.items():
        destination = base / ('qualification-' + key)
        atomic(destination, blob)
        inputs[key] = destination.relative_to(root).as_posix()
    tasks = []
    for index, sid in enumerate(sorted(summary['material_sha256'])):
        inputs['material-' + sid] = (
            base / (sid + '-material.json.gz')).relative_to(root).as_posix()
        tasks.append(dict(identity=sid, index=index, shard=0,
                          input_key='material-' + sid,
                          payload=dict(segment_id=sid),
                          limits=dict(native_calls=0, packet_visits=0,
                                      bound_calls=0, bound_steps=0)))
    definition = dict(id=STUDY, scope=SCOPE,
                      adapter='analysis/lll/prediction_drift_study.py',
                      sources=qualification_sources(root), inputs=inputs,
                      tasks=tasks, workers=1, threads=1, maximum_wall_s=600)
    atomic(base / 'definition.json', encoded(definition))
    manifest = Definition.from_dict(definition, root).prepare(root)
    return dict(path='data/' + STUDY,
                allocation=manifest['allocation'], limits=manifest['limits'])


def evaluate(task, context):
    """One recording; preserve all four settings per physical model."""
    if context.manifest.get('scope') != SCOPE or task not in context.manifest['tasks']:
        raise ValueError('unchanged drift task required')
    summary = json.loads(context.input_path('preparation').read_bytes())
    if summary['recipe'] != recipe():
        raise ValueError('unchanged drift recipe required')
    sid = task['identity']
    blob = context.input_path('material-' + sid).read_bytes()
    if digest(blob) != summary['material_sha256'][sid]:
        raise ValueError('unchanged saved pilot epochs required')
    material = json.loads(gzip.decompress(blob))
    if material['segment_id'] != sid:
        raise ValueError('saved recording identity differs')
    settings=[]
    for selection in summary['selected_settings']:
        if selection['segment_id'] != sid:
            continue
        identity = selection['chosen_identity']
        if identity is None:
            settings.append(dict(**selection, correction=None))
            continue
        result = score_drift(material['selected_epochs'][identity])
        require_baseline(result, summary['baseline_reference'][identity])
        settings.append(dict(**selection, correction=result))
    if len(settings) != 12:
        raise ValueError('all twelve settings per recording required')
    context.save('drift-comparison.json', settings)
    return dict(passed=True, segment_id=sid,
                corrected_settings=sum(row['correction'] is not None
                                       for row in settings),
                numerical_abstentions=sum(row['correction'] is None
                                          for row in settings),
                scientific_decision='abstain', model_fits=0,
                original_imu_reads=0, protected_esa_reads=0)
