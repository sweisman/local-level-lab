# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the fixed ESA shape score under two observed regional atmospheres."""

from collections import defaultdict
from contextlib import closing
from functools import partial
import gzip
import json
import math
from pathlib import Path
import sys

from . import esa_carrier_phase_continuous as gps_path
from . import esa_glonass_phase_path as glonass_path
from .esa_carrier_clock_step import metadata, normalized_epochs
from .esa_glonass_phase_support import accepted, observations
from .esa_rinex_code import read_navigation
from .esa_rinex_code_comparison import coordinates
from .esa_rinex_code_study import _INPUTS, _NAV, _OBS
from .esa_sounding_delay import CUT, COUNT, FOLDER, SETTINGS, SOURCES_SHA
from .glonass_code import navigation
from .gnss_sounding import read_sounding, vapour_at_dewpoint, zenith_delay
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-sounding-carrier-v1'
SCOPE = 'ESA 187 frozen carrier trajectories with two observed regional atmospheres'
PLAN = FOLDER + '/ESA_SOUNDING_CARRIER_PLAN.md'
RESULT = FOLDER + '/esa-sounding-carrier-result.json'
REFERENCES = {
    'gps': (gps_path.ID, gps_path.TASK['identity'], '93fcfc884ffe80067ae434f2d6a9abdb272337c732847a2541d620b768781d43'),
    'glonass': (glonass_path.ID, glonass_path.TASK['identity'], '33c0dcbff856a13df142e2c2d90fc3d4fcd473843cb3b1a0ff23a6b253619440'),
}
PAIRS = gps_path.COUNT
TASKS = [dict(identity=f'{system}-{station}', input_key='rinex', payload=dict(system=system, station=station),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=PAIRS, bound_steps=16 * PAIRS))
         for system in REFERENCES for station in SETTINGS]


def sounding_slant_delay(profile):
    def delay(latitude, height, elevation):
        pressure, temperature, dewpoint = profile.weather_at(height)
        zenith = zenith_delay(latitude, height, pressure, temperature, vapour_at_dewpoint(dewpoint))
        return zenith / math.sin(elevation)
    return delay


def _reference(root, system, store):
    prefix, identity, sha = REFERENCES[system]
    with closing(ClosedStudy(root, 'data/' + prefix, store=store)) as study:
        if (study.completion['manifest_sha256'] != sha or study.summary['passed'] != 1
                or study.summary['charged']['bound_calls'] != PAIRS):
            raise ValueError('complete original carrier reference required')
        anchor = study.input('anchor')
        path = study.artifact(identity, 'carrier-path.json')['positions']
    if len(path) != PAIRS + 1:
        raise ValueError('incomplete reference path')
    return anchor, path


def _sources(raw):
    if digest(raw) != SOURCES_SHA:
        raise ValueError('exact saved sounding catalog required')
    return json.loads(raw)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('existing atmosphere replay must be preserved')
    catalog = FOLDER + '/esa-sounding-sources.json'
    sources = _sources((root / catalog).read_bytes())
    inputs = dict(rinex=_OBS, navigation=_NAV, catalog=catalog, gps_support=gps_path.SUPPORT,
                  glonass_support=glonass_path.SUPPORT, clock=gps_path.CLOCK_STEP)
    for station, source in sources.items():
        path = FOLDER + '/' + source['excerpt']
        if digest((root / path).read_bytes()) != source['excerpt_sha256']:
            raise ValueError('saved sounding excerpt changed')
        inputs[station] = path
    anchors = []
    with closing(ArchiveStore(root)) as store:
        for system in REFERENCES:
            anchor, path = _reference(root, system, store)
            anchors.append(anchor)
            name = f'data/{ID}-inputs/{system}-satellites.json'
            atomic(root / name, encoded([row['satellites'] for row in path[1:]]))
            inputs[f'{system}_satellites'] = name
    if anchors[0] != anchors[1]:
        raise ValueError('carrier references use different starting positions')
    name = f'data/{ID}-inputs/anchor.json'
    atomic(root / name, encoded(anchors[0]))
    inputs['anchor'] = name
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, tasks=TASKS,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_sounding_carrier.py']),
        workers=1, threads=1, maximum_wall_s=180.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def _gps_stepper(rinex, support, clock, gps_nav, ions, atmosphere):
    if any(clock[key] != value for key, value in metadata(rinex, clock['pair_index']).items()):
        raise ValueError('clock step does not reproduce')
    epochs = list(gps_path.phase_epochs(rinex))

    def advance(index, center):
        a, b = epochs[index:index + 2]
        expected = support[index]['accepted_prns']
        if index == clock['pair_index']:
            a, b = normalized_epochs(a, b, clock['integer_clock_step_s'], clock['corrected_elapsed_s'])
            expected = clock['supported_prns']
        return gps_path.step(a, b, center, gps_nav, ions, expected, atmosphere=atmosphere)
    return epochs, advance


def _glonass_stepper(rinex, support, clock, nav_text, ions, atmosphere):
    slots, epochs = observations(rinex)
    ephemerides = defaultdict(list)
    for row in navigation(nav_text):
        ephemerides[row.prn].append(row)

    def advance(index, center):
        a, b = epochs[index:index + 2]
        options = {}
        if index == clock['pair_index']:
            options = dict(jump=clock['integer_clock_step_s'], elapsed=clock['corrected_elapsed_s'])
        paired, _ = accepted(a, b, slots, **options)
        if list(paired) != support[index]['accepted']:
            raise ValueError('frozen GLONASS support differs')
        return glonass_path.displacement(a, b, center, paired, ephemerides, ions, atmosphere=atmosphere)
    return epochs, advance


def evaluate(declared, context):
    import numpy as np
    from . import gnss_position as gps
    from .gnss_carrier_phase import _atmosphere

    payload = declared['payload']
    if context.manifest['scope'] != SCOPE or payload not in [task['payload'] for task in TASKS]:
        raise ValueError('exact frozen weather replay task required')
    system, station = payload['system'], payload['station']
    catalog = _sources(context.input_path('catalog').read_bytes())
    excerpt = context.input_path(station).read_bytes()
    if digest(excerpt) != catalog[station]['excerpt_sha256']:
        raise ValueError('frozen sounding excerpt changed')
    profile = read_sounding(excerpt.decode('ascii'), SETTINGS[station])
    atmosphere = partial(_atmosphere, neutral_delay=sounding_slant_delay(profile))
    rinex = gzip.decompress(context.input_path('rinex').read_bytes())
    nav, flags, clock = (context.input_path(key).read_bytes()
                         for key in ('navigation', f'{system}_support', 'clock'))
    expected_support_hash = gps_path.SUPPORT_SHA if system == 'gps' else glonass_path.SUPPORT_SHA
    if [digest(raw) for raw in (rinex, nav, flags, clock)] != [
            _INPUTS[_OBS], _INPUTS[_NAV], expected_support_hash, gps_path.CLOCK_STEP_SHA]:
        raise ValueError('original GNSS replay inputs required')
    support, clock_step = (json.loads(raw)['result'] for raw in (flags, clock))
    nav_text = gzip.decompress(nav).decode('ascii')
    gps_nav, ions = read_navigation(nav_text)
    if system == 'gps':
        epochs, advance = _gps_stepper(rinex, support['per_pair'], clock_step, gps_nav, ions, atmosphere)
    else:
        epochs, advance = _glonass_stepper(rinex, support['per_pair'], clock_step, nav_text, ions, atmosphere)
    anchor = json.loads(context.input_path('anchor').read_bytes())
    satellites = json.loads(context.input_path(f'{system}_satellites').read_bytes())
    start, end = gps_path.START, gps_path.END
    if len(satellites) != PAIRS or abs(anchor['time_s'] - epochs[start]['seconds']) > .001:
        raise ValueError('frozen support does not match the shared anchor')
    initial = coordinates([anchor])[0]
    center = np.asarray(gps.ecef(*initial))
    path = [dict(seconds=epochs[start]['seconds'], position=initial)]
    failure = None
    for index, expected_satellites in zip(range(start, end), satellites, strict=True):
        context.charge(bound_calls=1, bound_steps=16)
        try:
            answer = advance(index, center)
            if answer['satellites'] != expected_satellites:
                raise ValueError('weather replay changed the frozen satellites')
        except ValueError as error:
            failure = dict(index=index, reason=str(error))
            break
        center += answer['displacement_ecef_m']
        path.append(dict(seconds=epochs[index + 1]['seconds'], position=list(gps.geodetic(center)),
                         range_difference_rms_m=answer['range_difference_rms_m']))
    context.save_bytes('carrier-path.json', encoded(dict(positions=path, failure=failure)))
    return dict(passed=failure is None and len(path) == PAIRS + 1, completed_pairs=len(path) - 1,
                failure=failure, scientific_decision='abstain')


def _saved_path(replay, identity):
    """Retain the runner disposition while checking a saved diagnostic path."""
    receipt = replay.rows.get(identity)
    if receipt is None:
        return dict(runner_passed=False, path_complete=False, reason='no sealed task'), None
    envelope = replay.envelope(identity)
    result = envelope['result']
    reason = result.get('reason')
    schema_rejected = (result.get('error_type') == 'ValueError'
                       and reason == 'one explicit software result and continued scientific abstention required')
    status = dict(runner_passed=result['passed'], path_complete=False, reason=reason)
    if not (result['passed'] or schema_rejected):
        return status, None
    artifact = replay.artifact(identity, 'carrier-path.json')
    path = artifact['positions']
    if (receipt['charged']['bound_calls'] != PAIRS or receipt['charged']['bound_steps'] != 16 * PAIRS
            or artifact['failure'] is not None or len(path) != PAIRS + 1
            or any(not math.isfinite(row['range_difference_rms_m']) or row['range_difference_rms_m'] < 0
                   for row in path[1:])):
        raise ValueError('diagnostic path and recorded charges do not agree')
    return status | dict(path_complete=True, pairs=PAIRS), path


def report(root):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .esa_changing_drift_transfer import _chart
    from .esa_fit_adjusted_forecast_report import position_errors_neu
    from .esa_shape_receiver_margin import PRIOR_RESULT, PRIOR_SHA, WITNESS, WITNESS_MANIFEST
    from .innovations_snapshot import restore

    original_score = gps_path._load(root, PRIOR_RESULT, PRIOR_SHA)['scores']['original']['signed_midpoint']
    with closing(ArchiveStore(root)) as store:
        references = {system: _reference(root, system, store) for system in REFERENCES}
        with closing(ClosedStudy(root, gps_path.PARENT, store=store)) as parent:
            if parent.completion['manifest_sha256'] != gps_path.PARENT_SHA:
                raise ValueError('exact opened receiver parent required')
            original = json.loads(gzip.decompress(parent.input('training', raw=True)))[:COUNT]
        with closing(ClosedStudy(root, 'data/' + WITNESS, store=store)) as witness:
            if witness.completion['manifest_sha256'] != WITNESS_MANIFEST:
                raise ValueError('exact score witness required')
            shape, snapshot = witness.input('shape-direction'), witness.input('later-operator', raw=True)
        with closing(ClosedStudy(root, 'data/' + ID, store=store)) as replay:
            manifest = replay.completion['manifest_sha256']
            outcomes = {task['identity']: _saved_path(replay, task['identity']) for task in TASKS}
            attempted = replay.summary['charged']['bound_calls']
            worker_passed = replay.summary['passed']
    positions = coordinates(original)
    origin = np.asarray(positions[0])
    original_chart = _chart(positions, origin)
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)

    def score(trajectory):
        shift = _chart(trajectory, origin) - original_chart
        return original_score + float(np.asarray(shape['direction']) @ operator.whiten(shift.ravel())[3 * CUT:])

    def match(path):
        sampled = path[::2]
        if (len(path) != PAIRS + 1 or len(sampled) != COUNT
                or any(not math.isfinite(a['seconds']) or abs(a['seconds'] - b['time_s']) > .001
                       for a, b in zip(sampled, original, strict=True))):
            raise ValueError('position paths do not share the exact matched report times')
        track = np.asarray([row['position'] for row in sampled])
        if track.shape != (COUNT, 3) or not np.isfinite(track).all():
            raise ValueError('invalid positions in the saved path')
        return track.tolist()

    baseline = {}
    for system, (anchor, path) in references.items():
        if anchor != original[0]:
            raise ValueError('carrier reference anchor differs from first matched report')
        baseline[system] = match(path)
    nominal = {system: score(trajectory) for system, trajectory in baseline.items()}
    rows = {}
    for task in TASKS:
        identity = task['identity']
        status, path = outcomes[identity]
        if path is None:
            rows[identity] = status
            continue
        system = task['payload']['system']
        trajectory = match(path)
        errors = position_errors_neu(trajectory, baseline[system]).tolist()
        signed_score = score(trajectory)
        rows[identity] = status | dict(
            earlier_difference=error_metrics(errors[:CUT]), later_difference=error_metrics(errors[CUT:]),
            signed_score=signed_score, score_change=signed_score - nominal[system])
    result = dict(study_manifest_sha256=manifest, runner_passed=worker_passed,
        attempted_pairs=attempted, original_score=original_score,
        nominal_scores=nominal, alternatives=rows, new_fits=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    output = root / RESULT
    if not output.exists():
        atomic(output, raw)
    if output.read_bytes() != raw:
        raise ValueError('saved atmospheric replay report differs')
    print(raw.decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_sounding_carrier {prepare,report}')
