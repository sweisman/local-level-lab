# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chronological transfer of same-flight GPS receiver contrast covariance."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from .esa_forecast_receiver_transfer import BASE, PPP_AUDIT, PPP_SHA, RECOVER, RECOVERY, WALL_S
from .esa_parallel_gnss_reported_precision import WINDOWS
from .esa_raw_phase_ppp_closure import corrected_position
from .esa_receiver_contrast_study import LAWS
from .ilvis0_matched_observed_inputs import _write_equal
from .receiver_contrast_covariance import contrast_covariances, gaussian_loss, split_bands
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


STUDIES = {stage: f'esa-ppp-covariance-chronology-{stage}-v1' for stage in ('train', 'score')}
SCOPE = 'ESA 187 receiver covariance chronological transfer'
PLAN = BASE+'ESA_PPP_COVARIANCE_CHRONOLOGY_PLAN.md'
RESULT = BASE+'esa-ppp-covariance-chronology-result.json'
REQUEST = BASE+'esa-ppp-covariance-chronology-qualification.json'
REPORT = BASE+'esa-ppp-covariance-chronology-tests.xml'
MATERIAL = 'data/esa-ppp-covariance-chronology-inputs'
WINDOWS_SHA = '711846ee666d4fbe88d68697673902120e9f18bdae4eb8cb314724abd6ca556f'
TEST = 'analysis/tests/test_esa_ppp_covariance_chronology.py'
TESTS = (
    'test_chronology_uses_original_ids_and_never_rebalances_missing_windows',
    'test_one_missing_receiver_epoch_makes_the_whole_fixed_window_unavailable',
    'test_later_offsets_use_donor_mean_and_scores_derive_quadratic',
)
BANDS = ('constant', 'slow', 'middle', 'fast')
BATCH_SIZES = {'train': 97, 'later-1': 25, 'later-2': 25, 'later-3': 24, 'later-4': 24}
RECEIVERS = ('air1', 'mosaic03', 'pwrpak7')
WIDTH = 120


def partition(identities):
    if len(identities) != sum(BATCH_SIZES.values()) or identities != sorted(set(identities)):
        raise ValueError('195 unique ordered window identities required')
    cursor, batches = 0, {}
    for name, count in BATCH_SIZES.items():
        batches[name] = identities[cursor:cursor+count]
        cursor += count
    return batches


def receiver_window(identity, by_receiver):
    import numpy as np

    first = identity*WIDTH
    times = range(first, first+WIDTH)
    matched = {name: sum(time in by_receiver[name] for time in times) for name in RECEIVERS}
    window = dict(identity=identity, matched=matched, complete=all(n == WIDTH for n in matched.values()))
    if not window['complete']:
        return dict(window, reason='incomplete common integer-second grid')
    values = []
    for time in times:
        reference, rotation = by_receiver['air1'][time]
        contrasts = [rotation@(np.asarray(by_receiver[name][time])-reference) for name in RECEIVERS[1:]]
        values.append(np.concatenate(contrasts).tolist())
    return dict(window, contrasts=values)


def materialize(root, windows, previous):
    from .airquantumgrav_receiver import records
    from .esa_full_parallel_gnss import AIR1, BASE as SOURCE_DIRECTORY, _sha
    from .esa_full_parallel_gnss_v2 import EXPECTED_ROLLOVERS
    from .esa_parallel_gnss import match_times
    from .esa_ppp_acquisition import TARGETS, verify_complete
    from .esa_receiver_sequence_wrap import records_with_sequence_wrap
    from .esa_rinex_window import WEEK
    from .gnss_position import local_rotation

    if (previous['protected_group_reads'] or windows['protected_group_reads']
            or windows['window_width_s'] != WIDTH or windows['reference_sha256'] != previous['reference_sha256']):
        raise ValueError('the original opened flight inventory is required')
    chosen = [{row['window_id'] for row in source['windows'] if row['fast_window']}
              for source in windows['sources']]
    if len(chosen) != 2:
        raise ValueError('the original two alternate receiver inventories are required')
    batches = partition(sorted(chosen[0] & chosen[1]))
    targets = [dict(time_s=time) for identities in batches.values() for index in identities
               for time in range(index*WIDTH, (index+1)*WIDTH)]
    tolerance = previous['match_tolerance_s']
    base = root/SOURCE_DIRECTORY

    def aligned(records, *, reference=False):
        matched = match_times(targets, records, tolerance_s=tolerance)
        result = {}
        for index, row in matched:
            if row['gps_week'] != WEEK:
                raise ValueError('exact original GPS week required')
            time = targets[index]['time_s']
            position = corrected_position(row, time, tolerance=tolerance)
            if reference:
                angles = map(math.radians, (row['latitude_deg'], row['longitude_deg']))
                result[time] = position, local_rotation(*angles)
            else:
                result[time] = position
        return result

    primary = base/AIR1
    if previous['reference_file'] != AIR1 or _sha(primary) != previous['reference_sha256']:
        raise ValueError('the original reference receiver file is required')
    with primary.open() as stream:
        aligned_sources = {'air1': aligned(records(stream), reference=True)}
    for name, size in TARGETS.items():
        raw_receipt = (base/(name+'.receipt.json')).read_bytes()
        saved = next(row for row in previous['sources'] if row['filename'] == name)
        file_sha = verify_complete(base/name, size, json.loads(raw_receipt))
        if file_sha != saved['source_sha256'] or digest(raw_receipt) != saved['receipt_sha256']:
            raise ValueError('exact audited receiver source required')
        audit = {}
        with (base/name).open() as stream:
            parsed = records_with_sequence_wrap(stream, expected_rollovers=EXPECTED_ROLLOVERS[name], audit=audit)
            aligned_sources[name.split('_')[1]] = aligned(parsed)
            for _ in parsed:
                pass
        if audit != saved['sequence_audit']:
            raise ValueError('the original sequence audit differs')
    return {name: [receiver_window(identity, aligned_sources) for identity in ids] for name, ids in batches.items()}


def fit_laws(cases, *, reserve):
    import numpy as np

    if len(cases) < 7:
        raise ValueError('at least seven complete donor windows are required')
    result = []
    for index, samples in enumerate(zip(*cases, strict=True)):
        reserve()
        rows = np.concatenate(samples)
        mean = rows.mean(axis=0) if index == 0 else np.zeros(6)
        centered = rows-mean
        estimated = contrast_covariances(centered.T@centered/len(centered))
        result.append(dict(mean=mean.tolist(), coefficients=len(rows),
                           raw_eigenvalues=estimated['raw_eigenvalues'].tolist(),
                           laws={law: estimated[law].tolist() for law in LAWS}))
    return result


def score_laws(cases, fits, *, reserve):
    import numpy as np

    bands = []
    for index, fit in enumerate(fits):
        scores = {}
        for law in LAWS:
            reserve()
            covariance = fit['laws'][law]
            normalization = 6.*math.log(2.*math.pi)+np.linalg.slogdet(covariance)[1]
            values = []
            for case in cases:
                rows = case[index]-fit['mean']
                loss = gaussian_loss(rows, covariance)
                values.append(dict(negative_log_score=loss, coefficients=len(rows),
                                   quadratic=2.*loss-len(rows)*normalization))
            scores[law] = values
        bands.append(scores)
    return bands


def task_for(batch):
    count = BATCH_SIZES[batch]
    limits = (dict(bound_calls=count+4, bound_steps=4*count+12) if batch == 'train'
              else dict(bound_calls=count+12, bound_steps=16*count))
    return dict(identity=batch, input_key=batch, payload=dict(batch=batch),
                limits=dict(native_calls=0, packet_visits=0, **limits))


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    env = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=env, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=env, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources, env


def closed_stage(root, stage, stack):
    """Resolve exact completed tasks from the original or its technical recovery."""
    prefix = 'data/'+STUDIES[stage]
    original = stack.enter_context(closing(ClosedStudy(root, prefix)))
    continuation = root/(prefix+'-recovery')
    sources = {prefix: original}
    if continuation.is_dir():
        from .studies.combined_task_evidence import inspect

        selected = {identity: row['origin'] for identity, row in inspect(root, continuation)['selected'].items()}
    else:
        selected = {identity: prefix for identity in original.rows
                    if original.envelope(identity)['status'] == 'complete'}
    expected = {'train'} if stage == 'train' else set(BATCH_SIZES)-{'train'}
    if set(selected) != expected:
        raise ValueError('the complete verified stage is required')
    for origin in sorted(set(selected.values())-sources.keys()):
        sources[origin] = stack.enter_context(closing(ClosedStudy(root, origin, store=original.store)))
    tasks = {identity: sources[origin] for identity, origin in selected.items()}
    closures = {name: study.completion for name, study in sources.items()}
    return original, tasks, closures


def inputs_for_stage(root, stage, sources, environment):
    from .studies.qualification import checked
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    for path, expected in ((WINDOWS, WINDOWS_SHA), (PPP_AUDIT, PPP_SHA)):
        if digest((root/path).read_bytes()) != expected:
            raise ValueError('the original receiver audit and fast-window list are required')
    staged = dict(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER))
    selection_path = root/MATERIAL/'selection'
    source_hashes = {name: digest((root/name).read_bytes()) for name in sources}
    if stage == 'train':
        if not selection_path.is_file():
            cases = materialize(root, json.loads((root/WINDOWS).read_bytes()), json.loads((root/PPP_AUDIT).read_bytes()))
            hashes = {}
            for name, rows in cases.items():
                payload = encoded(rows)
                _write_equal(root/MATERIAL/name, payload)
                hashes[name] = digest(payload)
            selection = dict(hashes=hashes, source_hashes=source_hashes, batches={
                name: [{key: value for key, value in row.items() if key != 'contrasts'} for row in rows]
                for name, rows in cases.items()})
            _write_equal(selection_path, encoded(selection))
        chosen = ['train']
    else:
        with ExitStack() as stack:
            parent, tasks, closures = closed_stage(root, 'train', stack)
            receipt = tasks['train'].envelope('train')
            if (receipt['status'] != 'complete' or not receipt['result']['passed']
                    or parent.input('selection', raw=True) != selection_path.read_bytes()
                    or parent.manifest['environment'] != environment
                    or any(sha != parent.manifest['sources'][name] for name, sha in source_hashes.items())):
                raise ValueError('sealed training output and unchanged sources are required')
            fits = tasks['train'].artifact('train', 'receiver-donors.json', raw=True)
            staged.update(model=fits, training_completion=encoded(closures))
        chosen = [name for name in BATCH_SIZES if name != 'train']
    selection = json.loads(selection_path.read_bytes())
    if selection['source_hashes'] != source_hashes:
        raise ValueError('prepared material was generated by different sources')
    for name in chosen:
        path = root/MATERIAL/name
        if digest(path.read_bytes()) != selection['hashes'][name]:
            raise ValueError('receiver material differs from the frozen selection')
    inputs = dict(plan=PLAN, ppp_audit=PPP_AUDIT, prior=WINDOWS, selection=f'{MATERIAL}/selection',
                  qualification=REQUEST, qualification_tests=REPORT)
    inputs.update({name: f'{MATERIAL}/{name}' for name in chosen})
    for name, raw in staged.items():
        path = f'{MATERIAL}/{stage}-{name}'
        _write_equal(root/path, raw)
        inputs[name] = path
    return inputs, [task_for(name) for name in chosen]


def prepare(root, stage):
    from .studies.runtime import Definition

    if (root/'data'/STUDIES[stage]/'manifest.json').is_file():
        raise ValueError('retain the existing frozen allowance')
    sources, environment = qualification(root, check=True)
    inputs, tasks = inputs_for_stage(root, stage, sources, environment)
    definition = dict(id=STUDIES[stage], scope=f'{SCOPE}: {stage}', adapter=Path(__file__).relative_to(root).as_posix(),
                      inputs=inputs, sources=sources, tasks=tasks, workers=1 if stage == 'train' else 2,
                      threads=1, maximum_wall_s=WALL_S)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    batch = task['payload']['batch']
    stage = 'train' if batch == 'train' else 'score'
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != f'{SCOPE}: {stage}' or declared != task_for(batch):
        raise ValueError('exact declared stage and batch required')
    raw = context.input_path(batch).read_bytes()
    selected = json.loads(context.input_path('selection').read_bytes())
    rows = json.loads(raw)
    if (len(rows) != BATCH_SIZES[batch] or digest(raw) != selected['hashes'][batch]
            or selected['batches'][batch] != [{key: value for key, value in item.items() if key != 'contrasts'}
                                              for item in rows]):
        raise ValueError('unchanged fixed chronological inventory required')
    ids, cases = [], []
    for item in rows:
        context.charge(bound_calls=1, bound_steps=4)
        if not item['complete']:
            continue
        start = item['identity']*WIDTH
        bands, dc = split_bands(item['contrasts'], range(start, start+WIDTH))
        ids.append(item['identity'])
        cases.append([dc[None, :], *bands])
    if stage == 'train':
        def reserve():
            context.charge(bound_calls=1, bound_steps=3)

        context.save('receiver-donors.json', dict(identities=ids, fits=fit_laws(cases, reserve=reserve)))
    else:
        model = json.loads(context.input_path('model').read_bytes())
        if set(ids) & set(model['identities']) or len(model['fits']) != len(BANDS):
            raise ValueError('training overlap or incomplete saved covariance')

        def reserve():
            context.charge(bound_calls=1, bound_steps=BATCH_SIZES[batch])

        scores = score_laws(cases, model['fits'], reserve=reserve)
        context.save('receiver-later.json', dict(identities=ids, scores=dict(zip(BANDS, scores, strict=True))))
    return dict(passed=True, batch=batch, scheduled=len(rows), scored=len(ids), scientific_decision='abstain',
                new_fits=0, protected_reads=0)


def recover(root, stage):
    from .studies.task_resume import close_original, prepare_campaign, resume_campaign

    prefix = 'data/'+STUDIES[stage]
    continuation = root/(prefix+'-recovery')
    if not continuation.is_dir():
        if not (root/prefix/'completion.json').is_file():
            close_original(root, prefix, qualification_request=RECOVERY)
        with closing(ClosedStudy(root, prefix)) as original:
            if original.input('recovery_policy') != RECOVER:
                raise ValueError('unchanged recovery allowance required')
            if all(identity in original.rows and original.envelope(identity)['status'] == 'complete'
                   for identity in original.tasks):
                return dict(state='original_tasks_finished', pending=0)
        prepare_campaign(root, prefix, continuation, qualification_request=RECOVERY, **RECOVER)
    return resume_campaign(root, continuation)


def summarize(scores):
    single = {}
    for band, by_law in scores.items():
        single[band] = {}
        for law, rows in by_law.items():
            count = sum(row['coefficients'] for row in rows)
            q = math.fsum(row['quadratic'] for row in rows)
            single[band][law] = dict(negative_log_score=math.fsum(row['negative_log_score'] for row in rows),
                                    coefficients=count, mean_squared_standardized=q/(6*count) if count else None)
    return single


def report(root):
    with ExitStack() as stack:
        _, trained, train_closures = closed_stage(root, 'train', stack)
        scores, scored, score_closures = closed_stage(root, 'score', stack)
        if scores.input('training_completion') != train_closures:
            raise ValueError('the later scores must use the sealed donor settings')
        train = trained['train']
        donor = train.artifact('train', 'receiver-donors.json')
        if (train.envelope('train')['charged'] != task_for('train')['limits']
                or encoded(donor) != scores.input('model', raw=True)):
            raise ValueError('exact original donor settings and allowance required')
        selection = scores.input('selection')
        later = {}
        for batch, study in scored.items():
            row = study.artifact(batch, 'receiver-later.json')
            if (study.envelope(batch)['charged'] != task_for(batch)['limits']
                    or row['identities'] != [x['identity'] for x in selection['batches'][batch] if x['complete']]):
                raise ValueError('later coverage differs from the frozen selection')
            later[batch] = dict(identities=row['identities'], bands=summarize(row['scores']))
        totals = {scope: {law: math.fsum(bands['bands'][band][law]['negative_log_score']
                         for bands in later.values() for band in included) for law in LAWS}
                  for scope, included in (('all', BANDS), ('changing', BANDS[1:]))}
        result = dict(donors=donor['identities'], later=later, totals=totals, selection=selection,
                      closures={'train': train_closures, 'score': score_closures})
    _write_equal(root/RESULT, encoded(result))
    return dict(donors=len(result['donors']), retained={key: len(row['identities'])
                for key, row in later.items()}, totals=totals)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare-train', 'prepare-score', 'recover-train', 'recover-score', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    if action == 'request':
        output = qualification(root, check=False)
    elif action == 'report':
        output = report(root)
    else:
        command, stage = action.split('-')
        output = {'prepare': prepare, 'recover': recover}[command](root, stage)
    print(json.dumps(output, sort_keys=True))
