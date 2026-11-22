# SPDX-License-Identifier: AGPL-3.0-or-later
"""Release sealed steady-course forecasts and compare them with the matched turns."""

import argparse
from contextlib import ExitStack, closing
import json
import math
from pathlib import Path

from . import esa_straight_control_forecast as study
from .esa_repeat_turn_release import receiver_positions, terminal_starts
from .esa_repeat_turn_scoring import VERSION as SCORE_VERSION, score_sealed
from .esa_straight_control_windows import CLOCK_RESULT, RESULT as SELECTION, SELECTION_SHA
from .studies.artifacts import atomic, digest, encoded


PREFIX = 'data/'+study.ID
VERSION = 'esa-steady-course-forecast-release-v1'


def primary_starts(outcomes):
    if set(outcomes) != {task['identity'] for task in study.tasks()}:
        raise ValueError('all 16 terminal control starts are required')
    selections = []
    for index in study.WINDOWS:
        for law in study.reference.LAWS:
            group = dict(first_index=index, law=law)
            candidates = [(f'{index}-{law}-{start}', outcomes[f'{index}-{law}-{start}'])
                          for start in (0, 1)]
            converged = [(identity, result) for identity, result in candidates if result['converged']]
            if not converged:
                selections.append(dict(group, identity=None, state='no_converged_start'))
                continue
            if any(not math.isfinite(result['cost']) or result['cost'] < 0 for _, result in converged):
                raise ValueError('converged control starts must retain finite training costs')
            identity, chosen = min(converged, key=lambda pair: pair[1]['cost'])
            sha = chosen.get('forecast_sha256')
            selections.append(dict(group, identity=identity, state='sealed' if sha else 'primary_forecast_missing',
                                   training_cost=chosen['cost'], forecast_sha256=sha))
    return selections


def closed_stages(root, stack, expected_manifest_sha256):
    from .ilvis0_control_shards import verify_completion
    from .studies.closed import ClosedStudy
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    original = root/PREFIX
    if not (original/'completion.json').is_file():
        raise ValueError('closed control forecasts required before release')
    verify_completion(original)
    parent = stack.enter_context(closing(ClosedStudy(root, PREFIX)))
    tasks = [{key: value for key, value in task.items() if key not in ('index', 'shard')}
             for task in parent.manifest['tasks']]
    if (parent.completion['manifest_sha256'] != expected_manifest_sha256
            or parent.manifest['scope'] != study.SCOPE
            or parent.manifest['adapter'] != 'analysis/lll/esa_straight_control_forecast.py'
            or tasks != study.tasks()):
        raise ValueError('exact frozen control forecast execution required')
    if len(parent.rows) == len(tasks) and all(
            parent.envelope(identity)['status'] == 'complete' for identity in parent.rows):
        return [parent], None
    directory = root/(PREFIX+'-recovery')
    completion = directory/'completion.json'
    if not completion.is_file() or resume_campaign(root, directory, launch=False)['state'] != 'all_tasks_finished':
        raise ValueError('verified recovery closure required for unfinished control starts')
    stages = [stack.enter_context(closing(ClosedStudy(root, path.relative_to(root).as_posix(), store=parent.store)))
              for path in _stage_paths(directory)]
    return [parent, *stages], digest(completion.read_bytes())


def release(root, *, expected_manifest_sha256):
    cut = study.reference.TRAIN
    with ExitStack() as stack:
        studies, recovery_hash = closed_stages(root, stack, expected_manifest_sha256)
        clock_raw = (root/CLOCK_RESULT).read_bytes()
        bundle = studies[0].input('bundle')
        if digest(clock_raw) != study.CLOCK_SHA or bundle['clock_sha256'] != study.CLOCK_SHA:
            raise ValueError('unchanged control clock and package binding required')
        clock = json.loads(clock_raw)
        clocks = {w['window']['first_index']: w for w in clock['windows']}
        windows = {w['window']['first_index']: w for w in bundle['windows']}
        if tuple(windows) != study.WINDOWS:
            raise ValueError('unchanged control windows required')
        for index, window in windows.items():
            bound = clocks[index]
            if (window['window'] != bound['window'] or window['scoring_clock_sha256'] != bound['scoring_clock_sha256']
                    or window['training_receiver_sha256'] != bound['training_sha256']
                    or window['query_times_s'] != [time-window['raw_first_s'] for time in bound['query_times_s']]):
                raise ValueError('control forecast and checked clock disagree')
        outcomes, owners = terminal_starts(studies)
        selections = primary_starts(outcomes)
        forecasts = {}
        for case in selections:
            if case['state'] != 'sealed':
                continue
            identity = case['identity']
            window = windows[case['first_index']]
            raw = owners[identity].artifact(identity, 'sealed-receiver-forecast.json', raw=True)
            seal = json.loads(raw)
            if (digest(raw) != case['forecast_sha256'] or seal['policy'] != SCORE_VERSION
                    or seal['law'] != case['law'] or seal['training_sha256'] != window['training_receiver_sha256']
                    or seal['previous_time'] != window['query_times_s'][cut-1]
                    or seal['times_s'] != window['query_times_s'][cut:]):
                raise ValueError('primary control forecast does not match its seal and clock')
            forecasts[identity] = raw
        receipt = dict(version=VERSION, manifest_sha256=expected_manifest_sha256,
                       recovery_sha256=recovery_hash, control_clock_sha256=study.CLOCK_SHA,
                       receiver_metadata=clock['metadata_sha256'],
                       closures={s.prefix: digest(encoded(s.completion)) for s in studies},
                       outcomes=outcomes, primary=selections, scientific_decision='abstain')
    return receipt, forecasts, windows


def matched_gains(matches, forecasts):
    def gains(identity):
        if identity not in forecasts:
            return None
        scores = forecasts[identity]['scores']
        nll = {name: entry['negative_log_score'] for name, entry in scores.items()}
        return dict(without_steady=nll['native']-nll['turn'], with_steady=nll['steady']-nll['both'])

    result = []
    for turn, control in matches:
        tg, cg = gains(turn), gains(control)
        difference = {name: tg[name]-cg[name] for name in tg} if tg is not None and cg is not None else None
        result.append(dict(turn=turn, control=control, turn_gain=tg, control_gain=cg, extra_turn_gain=difference))
    return result


def transplant_exposure(control_raw, turn_raw):
    """Align a recorded turn exposure to the unchanged control query grid."""
    control, turn = map(json.loads, (control_raw, turn_raw))
    horizon = study.reference.LATER
    if (control['policy'] != SCORE_VERSION or turn['policy'] != SCORE_VERSION
            or control['law'] != turn['law'] or control['law'] not in study.reference.LAWS
            or any(len(case['times_s']) != horizon or len(case['angular_exposure']) != horizon
                   or any(type(x) not in (int, float) or not math.isfinite(x) or x < 0.
                          for x in case['angular_exposure'])
                   for case in (control, turn))):
        raise ValueError('exact matched exposure grids and error descriptions required')
    return encoded(dict(control, angular_exposure=turn['angular_exposure']))


def timing_controls(root, matches, forecasts, turns):
    from .studies.closed import ClosedStudy

    selected = {row['identity']: row for row in turns.values()}
    prepared = {}
    if not forecasts:
        return prepared
    with closing(ClosedStudy(root, study.ARCHIVE)) as archive:
        if (archive.completion['manifest_sha256'] != study.REFERENCE_SHA
                or archive.completion['state'] != 'complete' or archive.summary['completed'] != 16):
            raise ValueError('exact archived turn forecasts required')
        for turn, control in matches:
            if control not in forecasts:
                continue
            donor = archive.artifact(turn, 'sealed-receiver-forecast.json', raw=True)
            donor_sha = digest(donor)
            if donor_sha != selected[turn]['forecast_sha256']:
                raise ValueError('matched archived turn forecast seal differs')
            variant = transplant_exposure(forecasts[control], donor)
            prepared[control] = (variant, dict(turn=turn, turn_forecast_sha256=donor_sha,
                                               reassigned_forecast_sha256=digest(variant)))
    if set(prepared) != set(forecasts):
        raise ValueError('all available controls require a matched timing comparison')
    return prepared


def score(root, *, expected_manifest_sha256, saved_release):
    from .esa_repeat_turn_scale_diagnostic import verified_scores

    receipt, forecasts, windows = release(root, expected_manifest_sha256=expected_manifest_sha256)
    if saved_release != encoded(receipt):
        raise ValueError('exact saved release required before decoding later receiver positions')
    raw = (root/SELECTION).read_bytes()
    if digest(raw) != SELECTION_SHA:
        raise ValueError('unchanged turn-to-control pairing required')
    _, turns, turn_scores = verified_scores(root)
    selected = [case for case in receipt['primary'] if case['state'] == 'sealed']
    controls = {(case['first_index'], case['law']): case['identity'] for case in receipt['primary']}
    matches = [(turns[row['turn_first_index'], law]['identity'], controls[row['control']['first_index'], law])
               for row in json.loads(raw)['contrasts'] for law in study.reference.LAWS]
    timing = timing_controls(root, matches, forecasts, turns)
    targets = {case['first_index']: windows[case['first_index']] for case in selected}
    observed = receiver_positions(root, targets, expected_metadata=receipt['receiver_metadata']) if targets else {}
    scores, timing_scores = {}, {}
    for case in selected:
        identity = case['identity']
        times, actual = observed[case['first_index']]
        scores[identity] = score_sealed(forecasts[identity], expected_sha256=case['forecast_sha256'],
                                       times=times, actual=actual)
        variant, binding = timing[identity]
        reassigned = score_sealed(variant, expected_sha256=binding['reassigned_forecast_sha256'],
                                times=times, actual=actual)['scores']
        original = scores[identity]['scores']
        if any(original[name] != reassigned[name] for name in ('native', 'steady')):
            raise ValueError('reassigned turn exposure changed a covariance without a turn term')
        timing_scores[identity] = dict(binding, scores=reassigned, gain_from_reassigning_exposure={
            name: original[name]['negative_log_score']-reassigned[name]['negative_log_score']
            for name in ('turn', 'both')})
    return dict(release_sha256=digest(saved_release), scores=scores,
                matched_gains=matched_gains(matches, {**turn_scores, **scores}),
                reassigned_turn_exposure=timing_scores,
                control_angular_exposure={index: window['angular_exposure_counts']['scoring']
                                          for index, window in windows.items()},
                protected_reads=0, scientific_decision='abstain')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('release', 'score'))
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    root = Path.cwd()
    sources = study.qualification(root, verify=True)
    runtime = root/PREFIX
    manifest = (runtime/'manifest.json').read_bytes()
    if digest(manifest) != args.manifest_sha256:
        raise ValueError('exact control forecast manifest required')
    frozen = json.loads(manifest)['sources']
    if any(digest((root/name).read_bytes()) != frozen.get(name) for name in (*sources, study.REQUEST, study.REPORT)):
        raise ValueError('release sources differ from the forecast freeze')
    receipt_path = runtime/'receiver-release.json'
    if args.action == 'release':
        result, _, _ = release(root, expected_manifest_sha256=args.manifest_sha256)
        path = receipt_path
    else:
        result = score(root, expected_manifest_sha256=args.manifest_sha256, saved_release=receipt_path.read_bytes())
        path = runtime/'receiver-scores.json'
    raw = encoded(result)
    if path.is_file():
        if raw != path.read_bytes():
            raise ValueError('saved control result differs from regenerated receipt')
    else:
        atomic(path, raw)
    print(json.dumps(dict(path=path.relative_to(root).as_posix(), sha256=digest(raw)), sort_keys=True))


if __name__ == '__main__':
    main()
