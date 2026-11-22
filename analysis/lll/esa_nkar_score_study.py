# SPDX-License-Identifier: AGPL-3.0-or-later
"""Frozen one-second ground score for the open ESA development recording."""
import argparse
from contextlib import ExitStack, closing
import gzip
import json
from pathlib import Path

from . import esa_carrier_score_bound as bound
from . import esa_nkar_ground_intake as intake
from . import esa_nuuk_orbit_clock as orbit
from . import esa_shared_motion_carrier as carrier
from .esa_calibration_conditioned_margin import RECOVER, RECOVERY, _parent
from .ilvis0_matched_observed_inputs import _write_equal
from .rinex_archive_decode import decode_archive
from .studies.artifacts import encoded


ID = 'esa-nkar-ground-score-v1'
SCOPE = 'Actual one-second ground phase on the frozen ESA 187 carrier score'
PLAN = carrier.FOLDER+'ESA_NKAR_GROUND_SCORE_PLAN.md'
REQUEST = carrier.FOLDER+'esa-nkar-ground-score-qualification.json'
XML = carrier.FOLDER+'esa-nkar-ground-score-tests.xml'
RESULT = carrier.FOLDER+'esa-nkar-ground-score-result.json'
ARTIFACT = 'nkar-ground-score.json'
BOUND_SHA = '12c0f807d4e710cf05fc3dc521ad9e05f2ba69df8e53f95bcf47dd541b6295bb'
SECONDS = intake.SCORE_WINDOW[1]-intake.SCORE_WINDOW[0]
TASK = dict(identity='nkar-ground-score', input_key='ground', payload=dict(seconds=SECONDS),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=1+SECONDS, bound_steps=1+64*SECONDS))


def qualification(root, verify):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    tests = ('test_esa_nkar_score.py', 'test_fixed_reference_rinex2.py', 'test_carrier_score_cadence.py')
    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN,
                                    *(f'analysis/tests/{test}' for test in tests)))
    environment = runtime_environment()
    if not verify:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=XML)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=(
        'test_legacy_phase_values_keep_original_signal_labels_and_flags',
        'test_reference_pair_preserves_signed_range_and_rejects_changed_signal',
        'test_actual_coverage_projection_preserves_gaps_and_clock_invariance',
        'test_final_station_range_includes_clock_and_delay_with_expected_sign'), minimum_tests=11)
    return sources, environment


def prepare(root, original, converter):
    from .esa_nkar_score import station_geometry
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').is_file():
        raise ValueError('retain the original finite ground score study')
    if original.name != 'nkar1870.23d.Z':
        raise ValueError('use the original archived NKAR station day')
    sources, environment = qualification(root, True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=environment,
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with decode_archive(original, converter) as (stream, provenance):
        layout, measurements = intake.ground_window(stream, retain_measurements=True)
    first, last = intake.SCORE_WINDOW
    ground = [row for (_, seconds), row in measurements.items() if first <= seconds <= last]
    if not any(b['seconds']-a['seconds'] == 1 and not (a['flag'] or b['flag'])
               for a, b in zip(ground, ground[1:])):
        raise ValueError('no adjacent normal NKAR observations in the frozen two-minute window')
    if not layout.get('receiver_clock_applied') and any(row['receiver_offset_s'] for row in ground):
        raise ValueError('recorded ground receiver clock offsets require a separate timing qualification')
    antenna = station_geometry(layout).tolist()
    with ExitStack() as stack:
        phases, phase_result = _parent(root, orbit.RESULT, bound.PRODUCT_SHA, orbit.ID, orbit.TASK, orbit.ARTIFACT, stack)
        score, score_result = _parent(root, bound.RESULT, BOUND_SHA, bound.ID, bound.TASK, bound.ARTIFACT, stack)
        if (phases.envelope(orbit.TASK['identity'])['charged'] != orbit.TASK['limits']
                or score.envelope(bound.TASK['identity'])['charged'] != bound.TASK['limits']
                or len(phase_result['rows']) != 2*SECONDS or score_result['endpoint_gps_s'] != [first, last]):
            raise ValueError('the complete aircraft score and carrier context must reproduce')
        values = {key: phases.input(key, raw=True) for key in ('navigation', 'orbit', 'clock')}
    values.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVER),
                  ground=encoded(dict(source=intake.SOURCE, provenance=provenance, layout=layout,
                                      antenna_ecef_m=antenna, epochs=ground)))
    inputs = dict(plan=PLAN, ranges=orbit.RESULT, score=bound.RESULT, qualification=REQUEST, qualification_tests=XML)
    for key, value in values.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    return Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
                                     inputs=inputs, sources=sources, tasks=[TASK], workers=1, threads=1,
                                     maximum_wall_s=carrier.WALL_S), root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .esa_nkar_score import compare_score, final_range_model, reference_pair
    from .esa_precise_gps_support import read_orbit_positions
    from .esa_relative_clock_replay import _clock_records
    from .esa_rinex_code import read_navigation

    if context.manifest['scope'] != SCOPE or {k: v for k, v in task.items() if k not in ('index', 'shard')} != TASK:
        raise ValueError('the frozen actual ground score task is required')
    context.charge(bound_calls=1, bound_steps=1)

    def read(name):
        return context.input_path(name).read_bytes()

    def product(name):
        return gzip.decompress(read(name)).decode('ascii')

    ground, ranges, score = [json.loads(read(name)) for name in ('ground', 'ranges', 'score')]
    navigation, atmosphere = read_navigation(product('navigation'))
    model = final_range_model(navigation, atmosphere, read_orbit_positions(product('orbit')),
                              _clock_records(product('clock')), np.asarray(ground['antenna_ecef_m']))
    station = {row['seconds']: row for row in ground['epochs']}
    result = compare_score(ranges['rows'], score['bound']['dual_weights'], score['endpoint_gps_s'][0],
                           station, lambda a, b, prns: reference_pair(a, b, prns, model),
                           before_interval=lambda: context.charge(bound_calls=1, bound_steps=64))
    result.update(score_gap=score['score_gap'], ground_epochs=len(station), ground_provenance=ground['provenance'],
                  station_layout=ground['layout'], antenna_ecef_m=ground['antenna_ecef_m'],
                  exact_tracking_codes_established=False, aircraft_accuracy_established=False,
                  new_fits=0, protected_reads=0, passed=True, scientific_decision='abstain')
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
            raise ValueError('sealed and complete ground score evidence required')
        _write_equal(root/RESULT, encoded(dict(result, bound_sha256=BOUND_SHA, orbit_sha256=bound.PRODUCT_SHA,
                                               completion=study.completion)))
    return {key: result[key] for key in ('ground_epochs', 'matched_intervals', 'planned_intervals',
                                         'observable_norm_fraction', 'air_minus_ground_score_equivalent', 'score_gap')}


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
        result = carrier.recover_signature(root, study_id=ID, task=TASK)
    else:
        result = report(root)
    print(json.dumps(result, sort_keys=True))
