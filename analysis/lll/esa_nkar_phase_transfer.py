# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compare earlier-only ground phase corrections on common aircraft support."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_nkar_ground_intake as intake
from . import esa_nkar_score_study as nkar
from . import esa_qaq_phase_transfer as qaq
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .rinex_archive_decode import decode_archive
from .studies.artifacts import encoded


ID = 'esa-nkar-phase-transfer-v1'
SCOPE = 'Matched earlier-only ground phase corrections, ESA development record 187'
PLAN = nkar.carrier.FOLDER+'ESA_NKAR_PHASE_TRANSFER_PLAN.md'
REQUEST = nkar.carrier.FOLDER+'esa-nkar-phase-transfer-qualification.json'
XML = nkar.carrier.FOLDER+'esa-nkar-phase-transfer-tests.xml'
RESULT = nkar.carrier.FOLDER+'esa-nkar-phase-transfer-result.json'
ARTIFACT = 'nkar-phase-transfer.json'
PARENTS = {
    'earlier': (qaq, '50508c8bc9a6777b44b27533dee56fd977c7874e4a3f1fc46d247f8a2493d61b'),
    'later-nkar': (nkar, 'ab8fcb08bbf97d43538e0020649fce3f810bd4d488b1c52dadbc93ae5690aa75'),
    'later-qaq': (qaq.qaq, qaq.PARENT_SHA),
}
TASK = dict(identity='nkar-phase-transfer', input_key='ground', payload=dict(training_seconds=qaq.COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+qaq.COUNT+nkar.SECONDS,
                        bound_steps=1+64*qaq.COUNT+nkar.SECONDS))
TESTS = ('test_later_pair_recenters_on_common_satellites', 'test_later_pair_rejects_mismatched_aircraft_values',
         'test_comparison_applies_separate_earlier_gains_to_same_later_rows')


def later_pair(nuuk, qaqortoq):
    import numpy as np

    from .shared_motion_carrier import centre

    time = nuuk['start_gps_s']
    if qaqortoq['start_gps_s'] != time or any(r['stop_gps_s'] != time+1 for r in (nuuk, qaqortoq)):
        raise ValueError('identical one-second comparison intervals required')
    prns = sorted(set(nuuk['satellites']) & set(qaqortoq['satellites']))
    if len(prns) < 5:
        return None

    def select(row, field):
        values = dict(zip(row['satellites'], row[field], strict=True))
        return centre([values[prn] for prn in prns])

    aircraft = select(nuuk, 'air_range_m')
    weights = select(nuuk, 'aggregate_weights')
    if not np.allclose(aircraft, select(qaqortoq, 'air_range_m'), rtol=0., atol=1e-12):
        raise ValueError('saved aircraft observations disagree on common satellites')
    if not np.allclose(weights, select(qaqortoq, 'aggregate_weights'), rtol=0., atol=1e-12):
        raise ValueError('saved score weights disagree on common satellites')
    return dict(start_gps_s=time, satellites=prns, aircraft_m=aircraft.tolist(), weights=weights.tolist(),
                nkar_m=select(nuuk, 'ground_range_m').tolist(), qaq_m=select(qaqortoq, 'ground_range_m').tolist())


def compare_transfer(earlier, later, *, score_gap):
    from math import fsum, isfinite

    import numpy as np

    if not isfinite(score_gap) or score_gap <= 0:
        raise ValueError('positive frozen score gap required')
    result = dict(score_gap=score_gap)
    for station in ('nkar', 'qaq'):
        field = station+'_m'

        def rows(block):
            return [(row['start_gps_s'], row['aircraft_m'], row[field]) for row in block]

        comparison = qaq.transfer(rows(earlier), rows(later))
        shift = -comparison['trained_gain']*fsum(float(np.dot(row['weights'], row[field])) for row in later)
        result[station] = dict(comparison, signed_later_shift=shift, signed_shift_per_gap=shift/score_gap)
    return result


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_nkar_phase_transfer.py', 'test_esa_nkar_score.py', 'test_esa_qaq_phase_transfer.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                   *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=3)
    return sources, environment


def prepare(root, original, converter):
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite matched transfer study')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with ExitStack() as stack:
        parents, evidence = {}, {}
        for label, (module, sha) in PARENTS.items():
            study, result = _parent(root, module.RESULT, sha, module.ID, module.TASK, module.ARTIFACT, stack)
            if study.envelope(module.TASK['identity'])['charged'] != module.TASK['limits']:
                raise ValueError('complete parent comparison coverage required')
            parents[label], evidence[label] = study, result
        values = {key: parents['later-nkar'].input(key, raw=True) for key in ('navigation', 'clock', 'orbit')}
        if any(study.input(key, raw=True) != raw for study in parents.values() for key, raw in values.items()):
            raise ValueError('all comparisons must use the same satellite products')
        previous = evidence['later-nkar']
    with decode_archive(original, converter) as (stream, provenance):
        layout, measurements = intake.ground_window(stream, retain_measurements=True)
    if provenance != previous['ground_provenance'] or encoded(layout) != encoded(previous['station_layout']):
        raise ValueError('the exact station day, decoder and header from the later comparison are required')
    ground = [row for (_, seconds), row in measurements.items() if qaq.FIRST <= seconds <= qaq.LAST]
    if not layout.get('receiver_clock_applied') and any(row['receiver_offset_s'] for row in ground):
        raise ValueError('earlier ground receiver clock offsets require separate timing qualification')
    values.update(ground=encoded(dict(provenance=provenance, layout=layout, epochs=ground,
                                      antenna_ecef_m=previous['antenna_ecef_m'])), recovery=recovery,
                  recovery_tests=tests, recovery_policy=encoded(RECOVER))
    inputs = dict(plan=PLAN, qualification=REQUEST, qualification_tests=XML,
                  **{key: module.RESULT for key, (module, _) in PARENTS.items()})
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=nkar.carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    from .esa_nkar_score import final_range_model, reference_pair
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation
    from .shared_motion_carrier import centre

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen matched transfer task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(read(name)).decode('ascii')

    ground = json.loads(read('ground'))
    station = {row['seconds']: row for row in ground['epochs']}
    nav, atmosphere = read_navigation(product('navigation'))
    model = final_range_model(nav, atmosphere, read_orbit_positions(product('orbit')),
                              _clock_records(product('clock')), ground['antenna_ecef_m'])
    early = {row['start_gps_s']: row for row in json.loads(read('earlier'))['training_rows']}
    earlier = []
    for time in range(qaq.FIRST, qaq.LAST):
        context.charge(bound_calls=1, bound_steps=64)
        if time not in early or time not in station or time+1 not in station:
            continue
        row = early[time]
        delta = reference_pair(station[time], station[time+1], row['satellites'], model)
        prns = sorted(delta)
        if len(prns) < 5:
            continue
        selected = [row['satellites'].index(prn) for prn in prns]
        earlier.append(dict(start_gps_s=time, satellites=prns, nkar_m=centre([delta[prn] for prn in prns]).tolist(),
                            aircraft_m=centre([row['aircraft_m'][i] for i in selected]).tolist(),
                            qaq_m=centre([row['ground_m'][i] for i in selected]).tolist()))
    saved = [json.loads(read(key)) for key in ('later-nkar', 'later-qaq')]
    gap = saved[0]['score_gap']
    if saved[1]['score_gap'] != gap:
        raise ValueError('the same frozen score gap is required')
    near, far = [{r['start_gps_s']: r for r in source['intervals']} for source in saved]
    later = []
    for time in range(*intake.SCORE_WINDOW):
        context.charge(bound_calls=1, bound_steps=1)
        if time in near and time in far and (row := later_pair(near[time], far[time])) is not None:
            later.append(row)
    result = compare_transfer(earlier, later, score_gap=gap)
    result.update(training_rows=earlier, withheld_rows=later, matched_training_intervals=len(earlier),
                  matched_withheld_intervals=len(later), new_fits=0, protected_reads=0, passed=True,
                  scientific_decision='abstain')
    context.save(ARTIFACT, result)
    return result


def report(root):
    from .studies.closed import ClosedStudy

    prefix, identity = 'data/'+ID, TASK['identity']
    with ExitStack() as stack:
        study = stack.enter_context(closing(ClosedStudy(root, prefix)))
        if (root/(prefix+'-recovery')).is_dir():
            from .studies.combined_task_evidence import inspect

            origin = inspect(root, root/(prefix+'-recovery'))['selected'][identity]['origin']
            if origin != prefix:
                study = stack.enter_context(closing(ClosedStudy(root, origin, store=study.store)))
        envelope, result = study.envelope(identity), study.artifact(identity, ARTIFACT)
        if envelope['charged'] != TASK['limits'] or envelope['result'] != result or not result['passed']:
            raise ValueError('sealed and complete matched transfer evidence required')
        _write_equal(root/RESULT, encoded(dict(result, completion=study.completion,
                                               parents={key: sha for key, (_, sha) in PARENTS.items()})))
    return {key: value for key, value in result.items() if not key.endswith('_rows')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'recover', 'report'))
    parser.add_argument('--original', type=Path)
    parser.add_argument('--converter', type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    if args.action == 'prepare':
        if args.original is None or args.converter is None:
            parser.error('prepare requires --original and --converter')
        result = prepare(root, args.original, args.converter)
    elif args.action == 'request':
        result = qualification(root, False)
    elif args.action == 'recover':
        result = nkar.carrier.recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))
