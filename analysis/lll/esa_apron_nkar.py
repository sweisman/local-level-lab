# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare the archived parked-aircraft receiver to nearby Nuuk Museum."""

import argparse
from contextlib import closing
import json
from pathlib import Path

from . import esa_apron_carrier as apron
from .studies.artifacts import digest, encoded


ID = 'esa-apron-nkar-v1'
SCOPE = 'ESA 187 parked aircraft and Nuuk Museum common carrier comparisons'
FOLDER = apron.FOLDER
PLAN = FOLDER+'ESA_APRON_NKAR_PLAN.md'
RESULT = FOLDER+'esa-apron-nkar-result.json'
STATION = FOLDER+'esa-nkar-ground-score-result.json'
APRON_SHA = 'a9c72b08c56f5dbbd701cfeff4768dc81b82557908c7a993d5bd079ef9825be8'
STATION_SHA = 'ab8fcb08bbf97d43538e0020649fce3f810bd4d488b1c52dadbc93ae5690aa75'
CONVERTER_SHA = '450dc590b29ca346de3c95b061aac7d1fd22e7e6a67c13932fd3246df4f6c3fd'
SECONDS = tuple(range(int(apron.FIRST), int(apron.LAST)+1))
TASK = dict(identity='apron-ground-common-phase', input_key='station', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=apron.PAIRS+len(SECONDS),
                        bound_steps=1+66*apron.PAIRS+64*(len(SECONDS)-1)))


def matched_residuals(air, ground, *, minimum=5):
    from .shared_motion_carrier import centre

    satellites = sorted(air.keys() & ground.keys())
    if len(satellites) < minimum:
        return None
    left = centre([air[prn] for prn in satellites])
    right = centre([ground[prn] for prn in satellites])
    return dict(satellites=satellites, aircraft_m=left.tolist(), ground_m=right.tolist())


def pooled_statistics(rows):
    import numpy as np

    if not rows:
        raise ValueError('no matched one-second ranges')
    air, ground = (np.concatenate([row[name] for row in rows]) for name in ('aircraft_m', 'ground_m'))
    magnitude = np.linalg.norm(air)*np.linalg.norm(ground)
    return dict(matched_intervals=len(rows), matched_ranges=len(air),
                aircraft_rms_m=float(np.linalg.norm(air)/np.sqrt(len(air))),
                ground_rms_m=float(np.linalg.norm(ground)/np.sqrt(len(air))),
                difference_rms_m=float(np.linalg.norm(air-ground)/np.sqrt(len(air))),
                correlation=float((air@ground)/magnitude) if magnitude else None)


def prepare(root, original, converter):
    from .esa_nkar_score import station_geometry
    from .fixed_reference_rinex2 import observation_epochs, read_header
    from .ilvis0_matched_observed_inputs import _write_equal
    from .rinex_archive_decode import decode_archive
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite apron reference comparison')
    saved, prior_station = ((root/name).read_bytes() for name in (apron.RESULT, STATION))
    if digest(saved) != APRON_SHA or digest(prior_station) != STATION_SHA:
        raise ValueError('the exact aircraft and station result receipts are required')
    station = json.loads(prior_station)
    previous = station['ground_provenance']
    if (original.name != 'nkar1870.23d.Z' or original.stat().st_size != previous['original']['bytes']
            or digest(original.read_bytes()) != previous['original']['sha256']
            or digest(converter.read_bytes()) != CONVERTER_SHA):
        raise ValueError('the verified station day and GSI decoder are required')
    with decode_archive(original, converter) as (stream, provenance):
        if any(provenance[key] != previous[key] for key in ('original', 'compact', 'expanded')):
            raise ValueError('the previously verified expanded observation bytes must reproduce')
        layout = read_header(stream)
        if encoded(layout) != encoded(station['station_layout']):
            raise ValueError('the unchanged one-second station layout is required')
        rows = []
        for i, row in enumerate(observation_epochs(stream, layout, retain_measurements=True), 1):
            if i > 40_000 or row['week'] != apron.source.WEEK:
                raise ValueError('station intake outside the fixed epoch and week allowance')
            if row['seconds'] > SECONDS[-1]:
                break
            if row['seconds'] >= SECONDS[0]:
                rows.append(row)
    if [row['seconds'] for row in rows] != list(SECONDS):
        raise ValueError('the exact nineteen station epochs are required')
    if not layout.get('receiver_clock_applied') and any(row['receiver_offset_s'] for row in rows):
        raise ValueError('independent station clock correction would need qualification')
    antenna = station_geometry(layout).tolist()
    if antenna != station['antenna_ecef_m']:
        raise ValueError('the original station antenna position is required')
    inputs = dict(plan=PLAN, apron=apron.RESULT, station_receipt=STATION)
    output = f'data/{ID}-inputs/station.json'
    _write_equal(root/output, encoded(dict(epochs=rows, antenna_ecef_m=antenna, decoding=provenance)))
    inputs['station'] = output
    with closing(ClosedStudy(root, 'data/'+apron.ID)) as study:
        if (study.completion != json.loads(saved)['completion']
                or study.envelope(apron.TASK['identity'])['charged'] != apron.TASK['limits']):
            raise ValueError('completed corrected apron check required')
        for key in ('prefix', 'tie', 'ground', 'navigation', 'orbit', 'clock'):
            path = f'data/{ID}-inputs/{key}'
            _write_equal(root/path, study.input(key, raw=True))
            inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_apron_nkar.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import math
    import numpy as np

    from .esa_nkar_score import final_range_model, reference_pair

    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen parked-aircraft comparison is required')
    context.charge(bound_calls=1, bound_steps=1)

    def raw(key):
        return context.input_path(key).read_bytes()

    prior, station = (json.loads(raw(key)) for key in ('apron', 'station'))
    epochs, clock_offsets, nominal, _, products = apron.load_apron(raw)
    pairs, _ = apron.calculate_residuals(epochs, clock_offsets, final_range_model(*products, nominal),
                                        lambda: context.charge(bound_calls=1, bound_steps=66))
    reproduced = apron.rms_steps(pairs)
    if any(reproduced[key]['ranges'] != prior['nominal'][key]['ranges']
           or not math.isclose(reproduced[key]['rms_m'], prior['nominal'][key]['rms_m'],
                               rel_tol=0, abs_tol=1e-12) for key in reproduced):
        raise ValueError('the fixed aircraft residuals must reproduce before matching')
    model = final_range_model(*products, np.asarray(station['antenna_ecef_m']))
    rows, unmatched = [], []
    ground_epochs = station['epochs']
    for air, first, last in zip(apron.one_second_ranges(pairs), ground_epochs[:-1], ground_epochs[1:], strict=True):
        context.charge(bound_calls=1, bound_steps=64)
        ground = reference_pair(first, last, sorted(air), model)
        pair = matched_residuals(air, ground)
        if pair is None:
            unmatched.append(first['seconds'])
        else:
            rows.append(dict(gps_s=first['seconds'], **pair))
    context.save('apron-ground-ranges.json', rows)
    return dict(passed=True, scientific_decision='abstain', aircraft_error_cap_established=False,
                first_gps_s=SECONDS[0], last_gps_s=SECONDS[-1], unmatched_starts_gps_s=unmatched,
                station_provenance=station['decoding'], original_downloads=0, new_fits=0, protected_reads=0,
                **pooled_statistics(rows))


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.closed import ClosedStudy

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the verified complete parked-aircraft comparison is required')
        result = dict(envelope['result'], completion=study.completion, inputs=study.manifest['inputs'],
                      charged=envelope['charged'], rows=study.artifact(TASK['identity'], 'apron-ground-ranges.json'))
    _write_equal(root/RESULT, encoded(result))
    return {key: value for key, value in result.items() if key not in ('rows', 'inputs')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    parser.add_argument('--original', type=Path)
    parser.add_argument('--converter', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare' and (args.original is None or args.converter is None):
        parser.error('prepare requires --original and --converter')
    result = prepare(Path.cwd(), args.original, args.converter) if args.action == 'prepare' else report(Path.cwd())
    print(json.dumps(result, sort_keys=True))
