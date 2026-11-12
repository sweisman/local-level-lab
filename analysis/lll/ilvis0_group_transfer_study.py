# SPDX-License-Identifier: AGPL-3.0-or-later
"""Finite four-group transfer grid using the established rolling evaluator.

Preparation, source-bound qualification and launch remain separate gates.
"""


def recipe():
    return dict(version='ilvis0-four-group-transfer-v1',
                model='sphere_rotating', clock='header_elapsed', profile=False,
                starts=2, cuts=('inner', 'outer'), maximum_evaluations=200,
                stopping='near_zero', maximum_interval_s=.0075,
                gyro_offset_dph=1., training_weight='h1_v3_tau60',
                independent_neu_m=[.3, .3, .7],
                workers=1, threads=1, maximum_wall_s=43200.,
                scientific_decision='abstain', coverage_calibrated=False)


def sources(root):
    from lll.ilvis0_rolling_origin_study import sources as established_sources
    from lll.studies.dependencies import source_closure
    shared = established_sources(root)
    added = source_closure(root, [
        'analysis/lll/ilvis0_group_transfer_study.py',
        'analysis/lll/ilvis0_group_transfer_selection.py',
        'analysis/lll/prediction_transfer_reference.py',
        'analysis/tests/test_ilvis0_group_transfer_study.py',
        'analysis/tests/test_prediction_transfer_reference.py',
        'docs/prediction-group-transfer/OBSERVED_PLAN.md'])
    return sorted(set(shared) | set(added))


def prepare(root, *, qualification):
    """Verify software before decoding four preselected originals into sealed cuts."""
    import csv
    import gzip
    import io
    import json
    from pathlib import Path

    from lll.ilvis0_control_shards import runtime_environment
    from lll.ilvis0_group_transfer_selection import build_layouts
    from lll.ilvis0_rolling_origin import split_origins
    from lll.ilvis0_rolling_origin_study import (recipe as established_recipe,
                                                sources as established_sources)
    from lll.prediction_transfer_reference import from_saved_csv
    from lll.studies.artifacts import ArchiveStore, atomic, digest, encoded, safe_path
    from lll.studies.closed import ClosedStudy
    from lll.studies.qualification import checked
    from lll.studies.runtime import Definition

    root = Path(root).resolve()
    required = [
        'test_fixed_grid_and_charges_have_four_groups_sixteen_starts',
        'test_missing_or_duplicate_provenance_group_fails_closed',
        'test_grid_ignores_scientific_outcome_metadata',
        'test_adapter_reuses_established_evaluator',
        'test_missing_source_qualification_blocks_preparation_before_original_reads',
        'test_reused_prediction_source_matches_sealed_three_recording_study',
        'test_reference_uses_three_previously_scored_first_cuts',
        'test_outer_scores_cannot_change_earlier_reference',
        'test_changed_binding_and_missing_inner_result_fail_closed',
        'test_reboot_resume_skips_sealed_and_preserves_charges',
        'test_source_input_environment_mutation_blocks',
        'test_long_generated_both_cuts_meet_original_accuracy_screen[inner]',
        'test_long_generated_both_cuts_meet_original_accuracy_screen[outer]',
        'test_generated_rolling_origin_forecast_has_sealed_scoring_boundary[header_elapsed-False-inner]',
        'test_generated_rolling_origin_forecast_has_sealed_scoring_boundary[header_elapsed-False-outer]',
    ]
    request, report = checked(
        root, qualification, sources=sources(root),
        environment=runtime_environment(), required_tests=required,
        minimum_tests=len(required))
    prior = ClosedStudy(root, 'data/ilvis0-rolling-origin-development-v1')
    try:
        if (prior.completion['state'] not in ('complete', 'terminal') or
                prior.completion['manifest_sha256'] !=
                'dc7fded1b06b068f112e9915114e60b19dbd1ddd2022e84f3b173f19e35b2373' or
                len(prior.tasks) != 48 or len(prior.rows) != 48 or
                any(prior.manifest['sources'][name] != digest((root / name).read_bytes())
                    for name in established_sources(root))):
            raise ValueError('unchanged sealed rolling-origin evaluator required')
    finally:
        prior.close()

    split_name = 'docs/prediction-group-transfer/split-receipt.json'
    split_raw = safe_path(root, split_name).read_bytes()
    if digest(split_raw) != '5c3d62be8e9609ff5f4fba992e021dcca9ef33c6f9d04bce270b75b0d5bf0edb':
        raise ValueError('selected four-group receiver split changed')
    saved_split = json.loads(split_raw)
    if build_layouts(root) != saved_split:
        raise ValueError('saved four-group metadata selection changed')
    reference_name = 'docs/prediction-rolling-origin/result.csv'
    reference_raw = safe_path(root, reference_name).read_bytes()
    reference = from_saved_csv(
        reference_raw,
        expected_sha256='651ae7c87d28d4d5e2d4b9493d3f5a990fc550adc1972c30d970e3bc32ac4117')

    names = {
        'population': 'data/ilvis0-highspeed-segments-v2-20261008/selection.json.gz',
        'context': 'data/ilvis0-followup-20261007/summary.json',
        'selection': 'docs/prediction-group-transfer/selection.csv',
    }
    store = ArchiveStore(root)
    try:
        raw = {key: store.read(name) for key, name in names.items()}
    finally:
        store.close()
    if any(saved_split['input_sha256'][name] != digest(raw[key])
           for key, name in names.items()):
        raise ValueError('selected source metadata changed')
    population = json.loads(gzip.decompress(raw['population']))
    selected = {row['segment']['segment_id']: row for row in population['selected']}
    contexts = {row['task_id']: row for row in json.loads(raw['context'])['results']}
    selection = list(csv.DictReader(io.StringIO(raw['selection'].decode())))
    layouts = saved_split['layouts']
    if (len(selection) != 4 or
            [row['segment_id'] for row in selection] !=
            [row['segment_id'] for row in layouts]):
        raise ValueError('four-group selection order changed')

    from lll.ilvis0_segments import extract_segment
    from lll.ilvis0_prediction import split as numerical_split

    identity = 'ilvis0-four-group-transfer-v1'
    base = root/'data'/(identity+'-inputs')
    if base.exists() or (root/'data'/identity).exists():
        raise ValueError('fresh finite study identity required')
    base.mkdir(parents=True)
    material = {
        'recipe': encoded(established_recipe()),
        'transfer-recipe': encoded(recipe()),
        'transfer-reference': encoded(reference),
        'qualification-request': request,
        'qualification-report': report,
        'selection-receipt': split_raw,
    }
    task_layouts = []
    for row, saved in zip(selection, layouts):
        segment = row['segment_id']
        source = selected[segment]
        context = contexts[source['task']]
        original = Path(source['source_path'])
        relative = original.relative_to(root)
        if relative.parts[:2] != ('data', 'ilvis0-ready'):
            raise ValueError('documented retained original required')
        values, times, gps, provenance = extract_segment(
            safe_path(root, relative.as_posix()), context, source['segment'])
        cut = saved['training_epochs']
        split = numerical_split(times)
        if (provenance['source_sha256'] != row['source_sha256'] or
                split['training_epochs'] != cut or
                split['prediction_epochs'] != saved['prediction_epochs']):
            raise ValueError('decoded measurement differs from selected split')
        layout = dict(saved, native_packets=len(values),
                      first_interval_start_utc_s=provenance['first_interval_start_utc_s'])
        task_layouts.append(layout)
        measurements = dict(segment_id=segment, layout=layout,
                            values=values.tolist(), times=times.tolist(),
                            training_gps=gps[:cut].tolist())
        scoring = dict(segment_id=segment,
                       prediction_gps=gps[cut:].tolist())
        separated = split_origins(measurements, scoring)
        material[segment+'-common'] = gzip.compress(encoded(separated['common']), mtime=0)
        for origin in ('inner', 'outer'):
            material[segment+'-'+origin+'-training'] = encoded(separated[origin]['training'])
            material[segment+'-'+origin+'-scoring'] = encoded(separated[origin]['scoring'])
        material[segment+'-provenance'] = encoded(provenance)
    material['layouts'] = encoded(task_layouts)
    inputs = {}
    for index, (key, raw) in enumerate(material.items()):
        path = base/f'input-{index:03d}'
        atomic(path, raw)
        inputs[key] = path.relative_to(root).as_posix()
    definition = dict(id=identity,
                      scope='four preselected retrospective NASA groups; descriptive forecast-error transfer only',
                      adapter='analysis/lll/ilvis0_group_transfer_study.py',
                      sources=sources(root), inputs=inputs, tasks=tasks(task_layouts),
                      workers=recipe()['workers'], threads=recipe()['threads'],
                      maximum_wall_s=recipe()['maximum_wall_s'])
    atomic(base/'definition.json', encoded(definition))
    return Definition.from_dict(definition, root).prepare(root)


def tasks(layouts):
    if (not isinstance(layouts, list) or len(layouts) != 4 or
            len({row['segment_id'] for row in layouts}) != 4 or
            len({row['group_id'] for row in layouts}) != 4):
        raise ValueError('four distinct selected segments and provenance groups required')
    result = []
    for row in layouts:
        segment = row['segment_id']
        count = row['receiver_epochs']
        packets = row['native_packets']
        outer = row['training_epochs']
        if (not isinstance(segment, str) or not segment or
                not isinstance(row['group_id'], str) or not row['group_id'] or
                type(count) is not int or count < 9 or
                type(outer) is not int or outer != 2*count//3 or
                type(packets) is not int or packets < 1):
            raise ValueError('exact receiver split and packet count required')
        inner = count//3
        horizon = min(outer-inner, count-outer)
        for origin, cut in (('inner', inner), ('outer', outer)):
            for start in range(recipe()['starts']):
                result.append(dict(
                    identity=f'{segment}-{origin}-0-header_elapsed-{start}',
                    input_key=segment+'-common',
                    payload=dict(segment_id=segment, origin=origin,
                                 profile=False, clock='header_elapsed', start=start),
                    limits=dict(native_calls=201,
                                packet_visits=packets*(200*cut+cut+horizon),
                                bound_calls=0, bound_steps=0)))
    return result


def evaluate(task, context):
    from lll.ilvis0_rolling_origin_study import evaluate as established_evaluate
    return established_evaluate(task, context)
