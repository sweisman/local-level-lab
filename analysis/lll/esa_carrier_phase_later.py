# SPDX-License-Identifier: AGPL-3.0-or-later
"""Propagate the opened ESA aircraft path from continuous dual GPS carrier phases."""

from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from .esa_carrier_phase_support import L1_WAVELENGTH, MINIMUM_SATELLITES, pair_satellites, phase_epochs
from .esa_carrier_phase_support import RESULT as SUPPORT
from .esa_final_orbit_score import ORIGINAL_COMPARISON, ORIGINAL_SHA, _load
from .esa_rinex_code import read_navigation
from .esa_rinex_code_study import _INPUTS, _NAV, _OBS
from .esa_rinex_code_comparison import FOLDER, PARENT, PARENT_SHA, coordinates
from .esa_shape_receiver_margin import PRIOR_RESULT, PRIOR_SHA, WITNESS, WITNESS_MANIFEST
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-carrier-phase-later-v1'
SCOPE = 'ESA 187 later-only dual-band carrier-phase displacement'
PLAN = FOLDER + 'ESA_CARRIER_PHASE_LATER_PLAN.md'
RESULT = FOLDER + 'esa-carrier-phase-later-result.json'
SUPPORT_SHA = '5e42231fed6399e8810a3d2eedd914a3f467d71daece7989c1465652556c4319'
START, END = 799, 1039
CUT, LATER = 400, 120
TASK = dict(identity='dual-carrier-240-pairs', input_key='rinex', payload=dict(pairs=END - START),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=END - START,
                        bound_steps=16 * (END - START)))


def recover_metre_change(anchor, first, last, clock_a, clock_b, trop_a, trop_b, measured):
    import numpy as np
    from .gnss_carrier_phase import recover_displacement

    zeros = np.zeros(len(measured))
    return recover_displacement(anchor, first, last, clock_a, clock_b, zeros, zeros,
                                trop_a, trop_b, zeros, measured / L1_WAVELENGTH, sign=1)


def phase_step_geometry(first, second, ephemerides, expected):
    import numpy as np
    from .gnss_carrier_phase import shared_ephemerides
    from .gnss_position import satellite_state

    paired, _ = pair_satellites(first, second)
    if list(paired) != expected:
        raise ValueError('the frozen phase continuity check did not reproduce')
    model = shared_ephemerides(ephemerides, *[
        dict(gps_week=row['week'], gps_week_seconds=row['seconds']) for row in (first, second)])
    prns = sorted(paired.keys() & model.keys())
    ends = []
    for endpoint, row in enumerate((first, second)):
        states = [satellite_state(model[prn], row['week'], row['seconds'],
                  paired[prn]['broadcast_input_code_m'][endpoint]) for prn in prns]
        ends.append((np.array([s[0] for s in states]), np.array([s[1] for s in states])))
    if len(prns) < MINIMUM_SATELLITES:
        raise ValueError('too few phase pairs with common healthy ephemerides')
    measured = np.array([paired[prn]['ionosphere_free_displacement_m'] for prn in prns])
    return prns, ends, measured


def step(first, second, anchor, ephemerides, ionosphere, expected, *, atmosphere=None):
    import numpy as np
    from .gnss_carrier_phase import _atmosphere

    atmosphere = _atmosphere if atmosphere is None else atmosphere
    prns, ends, measured = phase_step_geometry(first, second, ephemerides, expected)
    (first_pos, first_clock), (last_pos, last_clock) = ends
    mask_a, _, trop_a = atmosphere(anchor, first_pos, first['seconds'], ionosphere)
    mask_b, _, trop_b = atmosphere(anchor, last_pos, second['seconds'], ionosphere)
    mask = mask_a & mask_b

    def solve(last_trop):
        return recover_metre_change(anchor, first_pos[mask], last_pos[mask], first_clock[mask],
            last_clock[mask], trop_a[mask], last_trop[mask], measured[mask])

    preliminary = solve(trop_b)
    if preliminary['status'] != 'converged':
        raise ValueError(preliminary['reason'])
    endpoint = anchor + np.asarray(preliminary['displacement_ecef_m'])
    supported, _, corrected_trop = atmosphere(endpoint, last_pos, second['seconds'], ionosphere)
    if not np.all(supported[mask]):
        raise ValueError('corrected end position changes the fixed elevation mask')
    answer = solve(corrected_trop)
    if answer['status'] != 'converged':
        raise ValueError(answer['reason'])
    return answer | dict(satellites=[prn for prn, use in zip(prns, mask, strict=True) if use],
                         atmosphere_update_m=float(np.linalg.norm(
                             np.asarray(answer['displacement_ecef_m']) - preliminary['displacement_ecef_m'])))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('existing carrier replay freeze must be preserved')
    continuity = _load(root, SUPPORT, SUPPORT_SHA)['result']
    if any(len(row['accepted_prns']) < MINIMUM_SATELLITES for row in continuity['per_pair'][START:END]):
        raise ValueError('later support is incomplete')
    previous = _load(root, ORIGINAL_COMPARISON, ORIGINAL_SHA)['result']
    if previous['matched_code_indices'][CUT - 1:] != list(range(START, END + 1, 2)):
        raise ValueError('exact earlier anchor and 120 later assignments required')
    with closing(ClosedStudy(root, PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_SHA:
            raise ValueError('exact opened parent required')
        earlier = json.loads(gzip.decompress(parent.input('training', raw=True)))[CUT - 1]
    if abs(earlier['time_s'] - continuity['per_pair'][START]['first_gps_seconds']) > .001:
        raise ValueError('anchor time mismatch')
    anchor = 'data/' + ID + '-inputs/anchor.json'
    atomic(root / anchor, encoded(earlier))
    sources = source_closure(root, [Path(__file__).relative_to(root).as_posix(), PLAN,
                                   'analysis/tests/test_esa_carrier_phase_later.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        tasks=[TASK], inputs=dict(rinex=_OBS, navigation=_NAV, anchor=anchor, continuity=SUPPORT),
        sources=sources, workers=1, threads=1, maximum_wall_s=180.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(encoded(manifest['limits']).decode(), end='')


def evaluate(declared, context):
    import numpy as np
    from . import gnss_position as gps

    if context.manifest['scope'] != SCOPE or declared['payload'] != TASK['payload']:
        raise ValueError('unexpected carrier displacement task')
    rinex = gzip.decompress(context.input_path('rinex').read_bytes())
    nav = context.input_path('navigation').read_bytes()
    flags = context.input_path('continuity').read_bytes()
    if digest(rinex) != _INPUTS[_OBS] or digest(nav) != _INPUTS[_NAV] or digest(flags) != SUPPORT_SHA:
        raise ValueError('exact sealed receiver inputs required')
    epochs = list(phase_epochs(rinex))
    navigation, ionosphere = read_navigation(gzip.decompress(nav).decode('ascii'))
    support = json.loads(flags)['result']['per_pair']
    original = json.loads(context.input_path('anchor').read_bytes())
    anchor = np.asarray(gps.ecef(*coordinates([original])[0]))
    positions = []
    failure = None
    for index in range(START, END):
        context.charge(bound_calls=1, bound_steps=16)
        try:
            answer = step(epochs[index], epochs[index + 1], anchor, navigation,
                          ionosphere, support[index]['accepted_prns'])
        except ValueError as error:
            failure = dict(index=index, reason=str(error))
            break
        anchor += answer['displacement_ecef_m']
        positions.append(dict(index=index + 1, seconds=epochs[index + 1]['seconds'],
                              position=list(gps.geodetic(anchor)), **answer))
    context.save_bytes('carrier-path.json', encoded(dict(positions=positions, failure=failure)))
    return dict(passed=len(positions) == END - START, completed_pairs=len(positions), failure=failure,
                scientific_decision='abstain')


def report(root):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .esa_changing_drift_transfer import _chart
    from .esa_fit_adjusted_forecast_report import position_errors_neu
    from .innovations_snapshot import restore

    prior = _load(root, PRIOR_RESULT, PRIOR_SHA)
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, 'data/' + ID, store=store)) as run:
            if not run.summary['passed'] or run.summary['charged']['bound_calls'] != END - START:
                raise ValueError('the continuous carrier replay did not qualify')
            path = run.artifact(TASK['identity'], 'carrier-path.json')['positions']
            manifest_sha = run.completion['manifest_sha256']
            bound_anchor = run.input('anchor')
        with closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if parent.completion['manifest_sha256'] != PARENT_SHA:
                raise ValueError('original opened receiver parent required')
            original = json.loads(gzip.decompress(parent.input('training', raw=True)))[:CUT + LATER]
        with closing(ClosedStudy(root, 'data/' + WITNESS, store=store)) as witness:
            if witness.completion['manifest_sha256'] != WITNESS_MANIFEST:
                raise ValueError('original shape-score direction required')
            shape, snapshot = witness.input('shape-direction'), witness.input('later-operator', raw=True)
    selected = path[1::2]
    if (len(path) != END - START or len(selected) != LATER or original[CUT - 1] != bound_anchor
            or any(abs(row['seconds'] - observed['time_s']) > .001
                   for row, observed in zip(selected, original[CUT:], strict=True))):
        raise ValueError('original matched times and single earlier anchor required')
    reconstructed = [row['position'] for row in selected]
    reference = coordinates(original)
    errors = position_errors_neu(reconstructed, reference[CUT:]).tolist()
    chart_difference = _chart(reconstructed, np.asarray(reference[0])) - _chart(
        reference[CUT:], np.asarray(reference[0]))
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    changed = np.vstack((np.zeros((CUT, 3)), chart_difference))
    score_effect = float(np.asarray(shape['direction']) @ operator.whiten(changed.ravel())[3 * CUT:])
    result = dict(
        study_manifest_sha256=manifest_sha, pairs=len(path), later_reports=len(selected),
        minimum_satellites=min(len(row['satellites']) for row in path),
        maximum_condition=max(row['condition'] for row in path),
        maximum_atmosphere_update_m=max(row['atmosphere_update_m'] for row in path),
        relative_motion_metrics=error_metrics(errors), signed_receiver_differences_m=errors,
        original_signed_midpoint=prior['scores']['original']['signed_midpoint'], score_effect=score_effect,
        carrier_signed_midpoint=prior['scores']['original']['signed_midpoint'] + score_effect,
        new_inertial_fits=0, new_forecast_propagations=0, protected_reads=0, scientific_decision='abstain',
    )
    raw = encoded(result)
    output = root / RESULT
    if not output.exists():
        atomic(output, raw)
    if output.read_bytes() != raw:
        raise ValueError('saved carrier replay report differs')
    print(encoded({k: v for k, v in result.items() if k != 'signed_receiver_differences_m'}
                  | dict(result_sha256=digest(raw))).decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_carrier_phase_later {prepare,report}')
