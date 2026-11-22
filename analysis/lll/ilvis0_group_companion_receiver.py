# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score sealed later forecasts on exactly matched epochs from two receivers."""

import argparse
from contextlib import closing
import csv
import gzip
import io
import json
from pathlib import Path

import numpy as np

from .ilvis0_companion_forecast import _receiver_coordinates, reference_choices
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_receiver_overlap import WEEK_MS, _time_index
from .ilvis0_receiver_window_pairs_study import IDENTITY, PARENT
from .ilvis0_remaining_prediction_layouts import CONTEXT, POPULATION
from .ilvis0_remaining_prediction_report import STUDY, verify_closed
from .ilvis0_rolling_origin_report import select_primary
from .studies.artifacts import ArchiveStore, digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


FOLDER = 'docs/prediction-group-transfer/'
PLAN = FOLDER+'COMPANION_RECEIVER_PLAN.md'
FREEZE = FOLDER+'companion-receiver-freeze.json'
RESULT = FOLDER+'companion-receiver-receipt.json'
PARENT_REPORT = FOLDER+'remaining-verified-report.json'


def _matched(source, table, leap):
    adjusted = {(tag-round(1000*leap)) % WEEK_MS: tag for tag in table}
    keys = [round(1000*t) % WEEK_MS for t in source]
    if len(adjusted) != len(table) or len(set(keys)) != len(keys):
        raise ValueError('ambiguous week-relative receiver tags')
    return [(i, adjusted[key]) for i, key in enumerate(keys) if key in adjusted]


def _metric(observed):
    radius = 6378137.+observed[:, 2]
    return np.column_stack((radius, radius*np.cos(observed[:, 0]), np.ones(len(observed))))


def _rms(delta):
    axes = np.sqrt(np.mean(delta**2, axis=0))
    return dict(horizontal_m=float(np.hypot(*axes[:2])), height_m=float(axes[2]))


def _score(forecast_delta, training_difference, later_difference):
    offset, references = reference_choices(training_difference, later_difference)
    return dict(training_offset_neu_m=offset.tolist(),
        receiver_relative_rms=_rms(references['companion_training_offset']),
        errors={name: _rms(forecast_delta-reference) for name, reference in references.items()})


def _coordinate_array(fixes):
    return np.array([[r['latitude_rad'], r['longitude_rad'], r['height_m']] for r in fixes])


def _evaluate_group(forecasts, row, source, context, companion):
    segment = row['segment_id']
    fixes = source['segment']['receiver_fixes']
    times = np.array([r['time_s'] for r in fixes])
    cut = 2*len(times)//3
    horizon_epochs = min(cut-len(times)//3, len(times)-cut)
    end = cut+horizon_epochs
    leap = context['timing']['gps_minus_utc_s']
    earlier = _matched(times[:cut], companion, leap)
    later = _matched(times[cut:end], companion, leap)
    result = dict(training_epochs=cut, later_epochs=horizon_epochs,
                  training_matched=len(earlier), later_matched=len(later))
    identity = row['outer_identity']
    if identity is None:
        return dict(result, status='no_passing_forecast')
    if min(len(earlier), len(later)) < 2:
        return dict(result, status='insufficient_shared_epochs')

    train = forecasts.input(segment+'-outer-training')
    scoring = forecasts.input(segment+'-outer-scoring')
    provenance = forecasts.input(segment+'-provenance')
    path = forecasts.artifact(identity, 'forecast.json')
    observed = _coordinate_array(fixes)
    expected_times = times-provenance['first_interval_start_utc_s']
    if (scoring['segment_id'] != segment or train['segment_id'] != segment
            or provenance['source_sha256'] != context['inspection']['source_sha256']
            or not np.array_equal(observed[cut:end], scoring['prediction_gps'])
            or not np.array_equal(observed[:cut], train['training_gps'])
            or not np.array_equal(expected_times[:end], path['times'])
            or not path['continuous_propagation_without_gps_reset']
            or path['prediction_receiver_positions_used'] or path['training_epochs'] != cut
            or path['prediction_epochs'] != horizon_epochs):
        raise ValueError('sealed forecast and original epoch support differ')

    def deltas(matches, offset=0):
        ids, tags = zip(*matches, strict=True)
        indices = np.array(ids)+offset
        ref = observed[indices]
        positions = _receiver_coordinates(companion, tags)
        difference = positions-ref
        difference[:, 1] = (difference[:, 1]+np.pi) % (2*np.pi)-np.pi
        return indices, difference*_metric(ref)

    _, training_difference = deltas(earlier)
    indices, later_difference = deltas(later, cut)
    forecast_delta = (np.asarray(path['coordinates'])[indices]-observed[indices])*_metric(observed[indices])
    horizon = times[indices]-times[cut-1]
    return dict(result, status='scored_shared_epochs',
        first_shared_forecast_s=float(horizon[0]), last_shared_forecast_s=float(horizon[-1]),
        full_forecast_s=float(times[end-1]-times[cut-1]),
        **_score(forecast_delta, training_difference, later_difference))


def run(root, action):
    report_raw = (root/PARENT_REPORT).read_bytes()
    parent = json.loads(report_raw)
    own = Path(__file__).relative_to(root).as_posix()
    with closing(ArchiveStore(root)) as store:
        forecasts = ClosedStudy(root, STUDY, store=store)
        verify_closed(forecasts)
        earlier = ClosedStudy(root, PARENT, store=store)
        pairs = ClosedStudy(root, 'data/'+IDENTITY, store=store)
        if (len(parent['rows']) != 20 or len(pairs.tasks) != 11
                or earlier.completion['state'] != 'complete' or pairs.completion['state'] != 'complete'
                or forecasts.completion['summary_sha256'] != parent['summary_sha256']
                or forecasts.completion['manifest_sha256'] != parent['manifest_sha256']
                or set(earlier.tasks) != set(pairs.tasks)):
            raise ValueError('unchanged archived receiver and forecast populations required')
        population, context = (store.read(name) for name in (POPULATION, CONTEXT))
        layout = forecasts.input('selection-receipt')
        source_hashes = {POPULATION: digest(population), CONTEXT: digest(context)}
        if source_hashes != layout['input_sha256']:
            raise ValueError('original selection or timing context changed')
        config = encoded(dict(sources={name: digest((root/name).read_bytes())
                                       for name in source_closure(root, (own, PLAN))},
            inputs={**source_hashes, PARENT_REPORT: digest(report_raw)},
            parents=[s.completion for s in (forecasts, earlier, pairs)],
            groups=20, source_pairs=11, maximum_reference_scores=60, threads=1, fit_starts=0,
            environment=runtime_environment()))
        if action == 'freeze':
            _write_equal(root/FREEZE, config)
            return dict(freeze_sha256=digest(config))
        if (root/FREEZE).read_bytes() != config:
            raise ValueError('changed study freeze')

        sources = {r['segment']['segment_id']: r for r in json.loads(gzip.decompress(population))['selected']}
        contexts = {r['task_id']: r for r in json.loads(context)['results']}
        by_source = {}
        for key, prior in earlier.tasks.items():
            pair = pairs.tasks[key]
            if not pairs.envelope(key)['result']['passed']:
                raise ValueError('failed receiver pair')
            for side, other in (('left', 'right'), ('right', 'left')):
                sha = prior[side+'_source_sha256']
                if sha in by_source or prior[side+'_task'] != pair[side+'_task']:
                    raise ValueError('ambiguous receiver identity')
                by_source[sha] = (key, pair[other+'_key'])
        report_rows = {row['segment_id']: row for row in parent['rows']}
        rows = []
        for choice in parent['selection']:
            segment = choice['segment_id']
            row = report_rows[segment]
            candidates = []
            for start in (0, 1):
                identity = f'{segment}-outer-0-header_elapsed-{start}'
                fit = forecasts.envelope(identity)['result']
                candidates.append(dict(start=start, identity=identity, passed=fit['passed'],
                                       training_cost=fit.get('training_cost')))
            best = select_primary(candidates)
            if row['outer_identity'] != (best['identity'] if best else None):
                raise ValueError('saved forecast choice differs from sealed starts')
            source = sources[segment]
            context = contexts[source['task']]
            sha = context['inspection']['source_sha256']
            if choice['source_sha256'] != sha:
                raise ValueError('forecast selection differs from source')
            record = dict(segment_id=segment, group_id=choice['group_id'], forecast=row['outer_identity'])
            if sha in by_source:
                key, table = by_source[sha]
                raw = pairs.input(table, raw=True)
                companion = _time_index(csv.DictReader(io.StringIO(gzip.decompress(raw).decode())))
                record.update(pair_id=key, **_evaluate_group(forecasts, row, source, context, companion))
            else:
                record['status'] = 'no_verified_receiver_pair'
            rows.append(record)
    result = encoded(dict(freeze_sha256=digest(config), rows=rows, fit_starts=0, original_reads=0,
        absolute_receiver_accuracy_established=False, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    return dict(groups=len(rows), scored=sum(r['status']=='scored_shared_epochs' for r in rows),
                receipt_sha256=digest(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
