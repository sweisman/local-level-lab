# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bind two added receiver tracks to their original signed inertial packets."""

import argparse
from contextlib import closing
import csv
import gzip
import json
from pathlib import Path

from . import ilvis0_gps_reconstruction_extension as gps, ilvis0_matched_observed_inputs as shared
from .ilvis0_gps_force_comparison import position_tracks
from .ilvis0_matched_observed_layout import BASELINE
from .ilvis0_prediction_layout import prediction_layout
from .studies.artifacts import digest, encoded, safe_path
from .studies.closed import ClosedStudy


ID = 'ilvis0-matched-extension-inputs-v1'
PLAN = shared.FOLDER+'MATCHED_EXTENSION_INPUTS_PLAN.md'
REQUEST = shared.FOLDER+'matched-extension-inputs-qualification.json'
TEST_REPORT = shared.FOLDER+'matched-extension-inputs-tests.xml'
RECEIPT = shared.FOLDER+'matched-extension-inputs-receipt.json'
SCOPE = 'align two additional NASA original recordings with three receiver tracks'
MAX_COMPRESSED = 10_000_000
GPS_RECEIPT = shared.FOLDER+'gps-reconstruction-extension-receipt.json'
REFERENCE_HASHES = {
    GPS_RECEIPT: 'aeb0fb4a43bb80362e5081a66ad3ad5d5dfd175d906ad159a6cb5a1f57286b23',
    BASELINE: '7f41d5c4ea5bb8b76c5daf069631bfdf7cd3531ad0e7491147686267c87ac51e',
    shared.CONTEXT: 'd488530b392584f2300817ff9bb52003f140f64a90e4270b1e49d92a75daf89c',
    shared.POPULATION: '934dea342a64b716533732d7ab0e961d23709cf37499faf7cee8e4c386778809',
}
ARMS = ((8, 585), (21, 538))
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=1)
TESTS = ('test_extension_join_keeps_original_training_cut_and_excludes_extra_epoch',
         'test_extension_join_refuses_missing_or_ambiguous_original_epochs',
         'test_extension_original_path_resolves_absolute_and_relative_corpus_names',
         'test_clock_checks_use_a_distinct_prefix_for_each_period',
         'test_short_elapsed_clock_or_changed_original_counts_fail_preflight')


def exact_join(original, tags, *, cut, gps_minus_utc_s):
    onboard = [round(fix['time_s']*1000) for fix in original]
    offset = round(gps_minus_utc_s*1000)
    converted = [(tag-offset) % shared.WEEK_MS for tag in tags]
    if (not 0 < cut < len(onboard) or sorted(set(onboard)) != onboard
            or sorted(set(converted)) != converted or not set(onboard) <= set(converted)):
        raise ValueError('every original epoch needs a unique exact receiver match')
    return dict(receiver_position_pilot_epochs=len(converted), exact_common_receiver_epochs=len(onboard),
                exact_common_training_epochs=cut, exact_common_prediction_epochs=len(onboard)-cut)


def original_path(root, name):
    path = Path(name)
    relative = (path.relative_to(root) if path.is_absolute() else path).as_posix()
    if (not relative.startswith('data/ilvis0-ready/')
            or not 0 < safe_path(root, relative).stat().st_size <= MAX_COMPRESSED):
        raise ValueError('the chosen archived original is missing or exceeds its size allowance')
    return relative


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, shared.TEST,
        'analysis/tests/test_ilvis0_matched_extension_inputs.py'))


def request(root):
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=shared.runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the existing input preparation allowance')
    environment, dependencies = shared.runtime_environment(), sources(root)
    binding, tests = checked(root, REQUEST, sources=dependencies, environment=environment,
                             required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, gps.RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    inputs = dict(plan=PLAN, gps_receipt=GPS_RECEIPT, gps_selection=gps.selection.OUTPUT)
    tasks = []
    staged = dict(qualification=binding, qualification_tests=tests,
        recovery=recovery, recovery_tests=recovery_tests, recovery_policy=encoded(gps.RECOVERY_POLICY))
    with closing(ClosedStudy(root, 'data/'+gps.ID)) as study:
        references = {path: study.store.read(path) for path in REFERENCE_HASHES}
        if any(digest(raw) != REFERENCE_HASHES[path] for path, raw in references.items()):
            raise ValueError('source or receiver reconstruction evidence changed')
        receipt = json.loads(references[GPS_RECEIPT])
        selection = study.input('selection', raw=True)
        if (study.completion != {key: receipt[key] for key in study.completion}
                or digest(selection) != gps.SELECTION_SHA or (root/gps.selection.OUTPUT).read_bytes() != selection
                or not study.summary['passed'] or receipt['imu_fit_starts'] != 0):
            raise ValueError('the exact completed two-group GPS reconstruction is required')
        selection = json.loads(selection)
        staged['receiver_completion'] = encoded(study.completion)
        tracks = position_tracks(study, selection)
        baseline = {r['segment_id']: r for r in csv.DictReader(references[BASELINE].decode().splitlines())}
        population = json.loads(gzip.decompress(references[shared.POPULATION]))
        originals = {row['segment']['segment_id']: row for row in population['selected']}
        records = {r['task_id']: r for r in json.loads(references[shared.CONTEXT])['results']}
        for pick, (imu, epochs) in zip(selection['selected'], ARMS, strict=True):
            identity = pick['segment_id']
            source = originals[identity]
            context = records[source['task']]
            geometry = prediction_layout(dict(baseline[identity], group_id=pick['group_id']), source, context)
            offset = context['timing']['gps_minus_utc_s']
            saved = tracks[pick['identity']]
            if (geometry['imu_type'] != imu or geometry['receiver_epochs'] != epochs
                    or geometry['source_sha256'] != pick['source_sha256'] or pick['identity'] != source['task']
                    or not 0 < context['inspection']['source_bytes'] <= shared.MAX_SOURCE_BYTES):
                raise ValueError('the chosen archived source or recording limit differs')
            geometry.update(exact_join(source['segment']['receiver_fixes'], sorted(saved),
                                      cut=geometry['training_epochs'], gps_minus_utc_s=offset),
                            gps_minus_utc_s=offset, source_task=source['task'])
            original = 'original-'+identity
            inputs[original] = original_path(root, source['source_path'])
            task_input = 'layout-'+identity
            staged[task_input] = encoded(dict(geometry=geometry, context=context,
                source=dict(task=source['task'], segment=source['segment']), saved=saved,
                time_offset_s=shared.matched_limits(1.)['time_offset']))
            tasks.append(dict(identity=identity, input_key=task_input, original_key=original, limits=LIMITS))
    for key, raw in staged.items():
        path = f'data/{ID}-inputs/{key}.json'
        shared._write_equal(root/path, raw)
        inputs[key] = path
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        sources=dependencies, inputs=inputs, tasks=tasks, workers=2, threads=1, maximum_wall_s=300.)
    shared._write_equal(root/f'data/{ID}-inputs/definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    frozen = json.loads(context.input_path().read_bytes())
    geometry = frozen['geometry']
    original = context.input_path(task['original_key'])
    if (context.manifest['scope'] != SCOPE or task['limits'] != LIMITS or task['identity'] != geometry['segment_id']
            or original.stat().st_size > MAX_COMPRESSED):
        raise ValueError('the unchanged recorded-input decode allowance is required')
    context.charge(bound_calls=1, bound_steps=1)
    saved = {int(tag): value for tag, value in frozen['saved'].items()}
    files, clocks, provenance = shared.prepared_artifacts(original, geometry, frozen['source'],
        frozen['context'], saved, frozen['time_offset_s'])
    for name, raw in files.items():
        context.save_bytes(name, raw)
    return dict(passed=True, source_sha256=provenance['source_sha256'], imu_type=geometry['imu_type'],
        source_packets=provenance['native_packets'], training_epochs=geometry['training_epochs'],
        scoring_epochs=geometry['prediction_epochs'], clocks=clocks, imu_fit_starts=0,
        original_decodes=1, scientific_decision='abstain')


def report(root):
    names = ('packets.npy.gz', 'queries.json', 'training.json', 'scoring.json', 'packet-provenance.json')
    results = []
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        for identity in study.rows:
            envelope = study.envelope(identity)
            row = envelope['result']
            if row['passed']:
                if envelope['charged'] != LIMITS:
                    raise ValueError('one charged original decode required')
                for name in names:
                    study.artifact(identity, name, raw=True)
                query, training, scoring = (study.artifact(identity, f'{name}.json')
                                            for name in ('queries', 'training', 'scoring'))
                train_times, later_times = training['query_times_s'], scoring['query_times_s']
                if (row['training_epochs'] != len(train_times) or row['scoring_epochs'] != len(later_times)
                        or query['query_times_s'] != train_times+later_times
                        or train_times[-1] >= later_times[0] or 'coordinates' in query):
                    raise ValueError('recorded inputs do not preserve the isolated forecast split')
            results.append(dict(segment_id=identity, **row))
        receipt = dict(study.completion, recordings=results, charged=study.summary['charged'],
                       imu_fit_starts=0, scientific_decision='abstain')
    shared._write_equal(root/RECEIPT, encoded(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    result = {'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
