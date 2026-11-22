# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct and compare the sealed GLONASS carrier-phase motion path."""

from collections import defaultdict
from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from .esa_carrier_phase_continuous import COUNT, END, START, CLOCK_STEP, CLOCK_STEP_SHA
from .esa_carrier_phase_continuous import RESULT as GPS_RESULT
from .esa_carrier_phase_later import CUT, LATER, PARENT, PARENT_SHA, _load, recover_metre_change
from .esa_final_orbit_score import ORIGINAL_COMPARISON, ORIGINAL_SHA
from .esa_glonass_phase_support import C, MINIMUM_SATELLITES, accepted, observations, RESULT as SUPPORT
from .esa_rinex_code import read_navigation
from .esa_rinex_code_study import _INPUTS, _NAV, _OBS
from .esa_rinex_code_comparison import coordinates
from .esa_rinex_window import FOLDER
from .esa_shape_receiver_margin import PRIOR_RESULT, PRIOR_SHA, WITNESS, WITNESS_MANIFEST
from .glonass_code import navigation, propagate
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-glonass-phase-path-v1'
SCOPE = 'ESA 187 GLONASS-only continuous carrier displacement on the saved 400/120 support'
PLAN = FOLDER + 'ESA_GLONASS_PHASE_PATH_PLAN.md'
RESULT = FOLDER + 'esa-glonass-phase-path-result.json'
SUPPORT_SHA = '407f249d08ad2e6e2cde4173b8c0c9c890cb27aadaba8d6a9b4e3e80194af6ca'
GPS_SHA = '68f6cfad45e74571296d2029ef72a9d0bd32f163db57b61727f835f307f4d090'
TASK = dict(identity='glonass-1038-pairs', input_key='rinex', payload=dict(pairs=COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=COUNT, bound_steps=16 * COUNT))


def _elapsed(ephemeris, week, raw_transmit):
    return (ephemeris.elapsed(week, raw_transmit) - ephemeris.clock_offset) / (1 + ephemeris.relative_frequency)


def common_ephemeris(entries, week, transmit, channel):
    candidates = []
    for entry in entries:
        if entry.unhealthy or entry.channel != channel:
            continue
        distance = max(abs(_elapsed(entry, week, t)) for t in transmit)
        if distance <= 900.:
            candidates.append((distance, entry.week, entry.epoch, entry))
    return min(candidates, key=lambda x: x[:3])[-1] if candidates else None


def displacement(first, second, center, paired, ephemerides, ionosphere, *, atmosphere=None):
    import numpy as np
    from .gnss_carrier_phase import _atmosphere

    atmosphere = _atmosphere if atmosphere is None else atmosphere
    launch, arrival, clocks_a, clocks_b, measured, prns = [], [], [], [], [], []
    week = first['week']
    if week != second['week']:
        raise ValueError('continuous single-week GLONASS inputs required')
    for prn, row in paired.items():
        t = tuple(epoch['seconds'] - code / C for epoch, code in zip(
            (first, second), row['code_endpoints_m'], strict=True))
        record = common_ephemeris(ephemerides[prn], week, t, row['channel'])
        if record is None:
            continue
        da, db = (_elapsed(record, week, a) for a in t)
        launch.append(propagate(record.position, record.velocity, record.acceleration, da))
        arrival.append(propagate(record.position, record.velocity, record.acceleration, db))
        clocks_a.append(record.clock(da))
        clocks_b.append(record.clock(db))
        measured.append(row['range_difference_m'])
        prns.append(prn)
    if len(prns) < MINIMUM_SATELLITES:
        raise ValueError('fewer than five phase pairs with shared healthy GLONASS geometry')
    launch, arrival, clocks_a, clocks_b, measured = map(np.asarray, (launch, arrival, clocks_a, clocks_b, measured))
    mask_a, _, trop_a = atmosphere(center, launch, first['seconds'], ionosphere)
    mask_b, _, trop_b = atmosphere(center, arrival, second['seconds'], ionosphere)
    valid = mask_a & mask_b

    def solve(trop):
        answer = recover_metre_change(center, launch[valid], arrival[valid], clocks_a[valid], clocks_b[valid],
                                     trop_a[valid], trop[valid], measured[valid])
        if answer['status'] != 'converged':
            raise ValueError(answer['reason'])
        return answer

    preliminary = solve(trop_b)
    endpoint = center + np.asarray(preliminary['displacement_ecef_m'])
    mask_end, _, corrected = atmosphere(endpoint, arrival, second['seconds'], ionosphere)
    if not np.all(mask_end[valid]):
        raise ValueError('updated end position leaves the fixed elevation mask')
    return solve(corrected) | dict(satellites=[p for p, keep in zip(prns, valid, strict=True) if keep])


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('existing GLONASS study must be preserved')
    support = _load(root, SUPPORT, SUPPORT_SHA)['result']
    matches = _load(root, ORIGINAL_COMPARISON, ORIGINAL_SHA)['result']['matched_code_indices']
    if (matches != list(range(START, END + 1, 2))
            or any(len(row['accepted']) < MINIMUM_SATELLITES for row in support['per_pair'][START:END])):
        raise ValueError('original 520-report assignments and full GLONASS coverage required')
    with closing(ClosedStudy(root, PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_SHA:
            raise ValueError('exact opened receiver parent required')
        anchor = json.loads(gzip.decompress(parent.input('training', raw=True)))[0]
    anchor_path = 'data/' + ID + '-inputs/anchor.json'
    atomic(root / anchor_path, encoded(anchor))
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, tasks=[TASK],
        inputs=dict(rinex=_OBS, navigation=_NAV, anchor=anchor_path, continuity=SUPPORT, clock=CLOCK_STEP),
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_glonass_phase_path.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(encoded(manifest['limits']).decode(), end='')


def evaluate(declared, context):
    import numpy as np
    from . import gnss_position as gps

    if context.manifest['scope'] != SCOPE or declared['payload'] != TASK['payload']:
        raise ValueError('exact GLONASS-only displacement task required')
    rinex = gzip.decompress(context.input_path('rinex').read_bytes())
    nav, support, clock = [context.input_path(key).read_bytes() for key in ('navigation', 'continuity', 'clock')]
    if [digest(raw) for raw in (rinex, nav, support, clock)] != [
            _INPUTS[_OBS], _INPUTS[_NAV], SUPPORT_SHA, CLOCK_STEP_SHA]:
        raise ValueError('frozen GLONASS observations or support changed')
    flags, clock = (json.loads(raw)['result'] for raw in (support, clock))
    slots, epochs = observations(rinex)
    by_prn = defaultdict(list)
    text = gzip.decompress(nav).decode('ascii')
    _, ions = read_navigation(text)
    for row in navigation(text):
        by_prn[row.prn].append(row)
    anchor = json.loads(context.input_path('anchor').read_bytes())
    if abs(anchor['time_s'] - epochs[START]['seconds']) > .001:
        raise ValueError('earliest matched anchor required')
    initial = coordinates([anchor])[0]
    center = np.asarray(gps.ecef(*initial))
    path = [dict(index=START, seconds=epochs[START]['seconds'], position=initial)]
    failure = None
    for index in range(START, END):
        context.charge(bound_calls=1, bound_steps=16)
        a, b = epochs[index:index + 2]
        try:
            options = {}
            if index == clock['pair_index']:
                options = dict(jump=clock['integer_clock_step_s'], elapsed=clock['corrected_elapsed_s'])
            paired, _ = accepted(a, b, slots, **options)
            if list(paired) != flags['per_pair'][index]['accepted']:
                raise ValueError('frozen carrier signal support changed')
            answer = displacement(a, b, center, paired, by_prn, ions)
        except ValueError as error:
            failure = dict(index=index, reason=str(error))
            break
        center += answer['displacement_ecef_m']
        path.append(dict(index=index + 1, seconds=b['seconds'], position=list(gps.geodetic(center)), **answer))
    context.save_bytes('carrier-path.json', encoded(dict(positions=path, failure=failure)))
    return dict(passed=len(path) == COUNT + 1, completed_pairs=len(path) - 1,
                failure=failure, scientific_decision='abstain')


def report(root):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .esa_changing_drift_transfer import _chart
    from .esa_fit_adjusted_forecast_report import position_errors_neu
    from .innovations_snapshot import restore

    original_score = _load(root, PRIOR_RESULT, PRIOR_SHA)['scores']['original']['signed_midpoint']
    gps = _load(root, GPS_RESULT, GPS_SHA)
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, 'data/' + ID, store=store)) as run:
            if not run.summary['passed'] or run.summary['charged']['bound_calls'] != COUNT:
                raise ValueError('continuous GLONASS run did not qualify')
            path = run.artifact(TASK['identity'], 'carrier-path.json')['positions']
            manifest = run.completion['manifest_sha256']
            anchor = run.input('anchor')
        with closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if parent.completion['manifest_sha256'] != PARENT_SHA:
                raise ValueError('unchanged opened receiver parent required')
            original = json.loads(gzip.decompress(parent.input('training', raw=True)))[:CUT + LATER]
        with closing(ClosedStudy(root, 'data/' + WITNESS, store=store)) as witness:
            if witness.completion['manifest_sha256'] != WITNESS_MANIFEST:
                raise ValueError('unchanged archived score witness required')
            shape = witness.input('shape-direction')
            snapshot = witness.input('later-operator', raw=True)
    matches = path[::2]
    if (original[0] != anchor or len(matches) != CUT + LATER or len(path) != COUNT + 1
            or any(abs(row['seconds'] - raw['time_s']) > .001 for row, raw in zip(matches, original, strict=True))):
        raise ValueError('same receiver anchor and full report support required')
    reference = coordinates(original)
    reconstruction = [row['position'] for row in matches]
    measured = position_errors_neu(reconstruction, reference)
    constellations = measured - np.asarray(gps['signed_receiver_differences_m'])
    anchor_coords = np.asarray(reference[0])
    offset = _chart(reconstruction, anchor_coords) - _chart(reference, anchor_coords)
    op = restore(snapshot, expected_sha256=shape['factors_sha256'],
                  expected_configuration=shape['configuration'], maximum_bytes=2**26)
    change = float(np.asarray(shape['direction']) @ op.whiten(offset.ravel())[3 * CUT:])
    result = dict(study_manifest_sha256=manifest, signed_position_errors_m=measured.tolist(),
        pairs=COUNT, original_score=original_score, gps_carrier_score=gps['carrier_signed_midpoint'],
        glonass_carrier_score=original_score + change,
        minimum_satellites=min(len(row['satellites']) for row in path[1:]),
        maximum_condition=max(row['condition'] for row in path[1:]),
        glonass_minus_export=dict(earlier=error_metrics(measured[:CUT].tolist()), later=error_metrics(measured[CUT:].tolist())),
        glonass_minus_gps=dict(earlier=error_metrics(constellations[:CUT].tolist()),
                               later=error_metrics(constellations[CUT:].tolist())),
        new_inertial_fits=0, new_forecast_propagations=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    output = root / RESULT
    if not output.exists():
        atomic(output, raw)
    if output.read_bytes() != raw:
        raise ValueError('saved GLONASS result differs')
    print(encoded({key: value for key, value in result.items() if key != 'signed_position_errors_m'}
                  | dict(result_sha256=digest(raw))).decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_glonass_phase_path {prepare,report}')
