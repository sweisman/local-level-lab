# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconstruct the entire opened ESA 400/120 path with one earlier anchor."""

from contextlib import closing
import gzip
import json
from pathlib import Path
import sys

from .esa_carrier_clock_step import metadata, normalized_epochs, RESULT as CLOCK_STEP
from .esa_carrier_phase_later import (
    CUT, LATER, ORIGINAL_COMPARISON, ORIGINAL_SHA, PARENT, PARENT_SHA, SUPPORT, SUPPORT_SHA, _load, step,
)
from .esa_carrier_phase_support import MINIMUM_SATELLITES, phase_epochs
from .esa_rinex_code import read_navigation
from .esa_rinex_code_study import _INPUTS, _NAV, _OBS
from .esa_rinex_code_comparison import FOLDER, coordinates
from .esa_shape_receiver_margin import PRIOR_RESULT, PRIOR_SHA, WITNESS, WITNESS_MANIFEST
from .studies.artifacts import ArchiveStore, atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-carrier-phase-continuous-v1'
SCOPE = 'ESA 187 400/120 carrier-phase displacement with checked clock step'
PLAN = FOLDER + 'ESA_CARRIER_PHASE_CONTINUOUS_PLAN.md'
RESULT = FOLDER + 'esa-carrier-phase-continuous-result.json'
CLOCK_STEP_SHA = 'f853e0210101494123bdc8da6029878dd5ffc11b0d5813f19308ac4d7c3e0c83'
START, END = 1, 1039
COUNT = END - START
TASK = dict(identity='continuous-1038-pairs', input_key='rinex', payload=dict(pairs=COUNT),
            limits=dict(native_calls=0, packet_visits=0, bound_calls=COUNT, bound_steps=16 * COUNT))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root / 'data' / ID).exists():
        raise ValueError('existing continuous carrier freeze must be preserved')
    continuity = _load(root, SUPPORT, SUPPORT_SHA)['result']['per_pair']
    clock = _load(root, CLOCK_STEP, CLOCK_STEP_SHA)['result']
    gaps = [i for i in range(START, END) if len(continuity[i]['accepted_prns']) < MINIMUM_SATELLITES]
    if (not clock['passed'] or gaps != [clock['pair_index']]
            or len(clock['supported_prns']) < MINIMUM_SATELLITES):
        raise ValueError('the exact checked clock step must close the only gap')
    matches = _load(root, ORIGINAL_COMPARISON, ORIGINAL_SHA)['result']['matched_code_indices']
    if matches != list(range(START, END + 1, 2)):
        raise ValueError('exact saved 520 report assignments required')
    with closing(ClosedStudy(root, PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_SHA:
            raise ValueError('exact opened parent required')
        first = json.loads(gzip.decompress(parent.input('training', raw=True)))[0]
    if abs(first['time_s'] - continuity[START]['first_gps_seconds']) > .001:
        raise ValueError('first receiver anchor differs from the saved match')
    anchor = 'data/' + ID + '-inputs/anchor.json'
    atomic(root / anchor, encoded(first))
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, tasks=[TASK],
        inputs=dict(rinex=_OBS, navigation=_NAV, anchor=anchor, continuity=SUPPORT, clock=CLOCK_STEP),
        sources=source_closure(root, [adapter, PLAN]), workers=1, threads=1, maximum_wall_s=180.)
    manifest = Definition.from_dict(definition, root).prepare(root)
    print(encoded(manifest['limits']).decode(), end='')


def evaluate(declared, context):
    import numpy as np
    from . import gnss_position as gps

    if context.manifest['scope'] != SCOPE or declared['payload'] != TASK['payload']:
        raise ValueError('unexpected continuous carrier task')
    rinex = gzip.decompress(context.input_path('rinex').read_bytes())
    navigation, flags, clock = (context.input_path(key).read_bytes()
                                for key in ('navigation', 'continuity', 'clock'))
    if [digest(raw) for raw in (rinex, navigation, flags, clock)] != [
            _INPUTS[_OBS], _INPUTS[_NAV], SUPPORT_SHA, CLOCK_STEP_SHA]:
        raise ValueError('exact original carrier observations and clock result required')
    support = json.loads(flags)['result']['per_pair']
    correction = json.loads(clock)['result']
    break_index = correction['pair_index']
    if any(correction[key] != value for key, value in metadata(rinex, break_index).items()):
        raise ValueError('the original receiver clock step did not reproduce')
    epochs = list(phase_epochs(rinex))
    ephemerides, ionosphere = read_navigation(gzip.decompress(navigation).decode('ascii'))
    first = json.loads(context.input_path('anchor').read_bytes())
    initial = coordinates([first])[0]
    anchor = np.asarray(gps.ecef(*initial))
    positions = [dict(index=START, seconds=epochs[START]['seconds'], position=initial)]
    failure = None
    for i in range(START, END):
        context.charge(bound_calls=1, bound_steps=16)
        a, b = epochs[i:i + 2]
        expected = support[i]['accepted_prns']
        if i == break_index:
            a, b = normalized_epochs(a, b, correction['integer_clock_step_s'],
                                      correction['corrected_elapsed_s'])
            expected = correction['supported_prns']
        try:
            answer = step(a, b, anchor, ephemerides, ionosphere, expected)
        except ValueError as error:
            failure = dict(index=i, reason=str(error))
            break
        anchor += answer['displacement_ecef_m']
        positions.append(dict(index=i + 1, seconds=b['seconds'], position=list(gps.geodetic(anchor)), **answer))
    context.save_bytes('carrier-path.json', encoded(dict(positions=positions, failure=failure)))
    return dict(passed=len(positions) == COUNT + 1, completed_pairs=len(positions) - 1,
                failure=failure, scientific_decision='abstain')


def report(root):
    import numpy as np
    from .airquantumgrav_geographic_report import error_metrics
    from .esa_changing_drift_transfer import _chart
    from .esa_fit_adjusted_forecast_report import position_errors_neu
    from .innovations_snapshot import restore

    baseline = _load(root, PRIOR_RESULT, PRIOR_SHA)['scores']['original']['signed_midpoint']
    with closing(ArchiveStore(root)) as store:
        with closing(ClosedStudy(root, 'data/' + ID, store=store)) as run:
            if not run.summary['passed'] or run.summary['charged']['bound_calls'] != COUNT:
                raise ValueError('the complete continuous carrier replay is required')
            track = run.artifact(TASK['identity'], 'carrier-path.json')['positions']
            manifest_sha = run.completion['manifest_sha256']
            anchor = run.input('anchor')
        with closing(ClosedStudy(root, PARENT, store=store)) as parent:
            if parent.completion['manifest_sha256'] != PARENT_SHA:
                raise ValueError('exact opened parent required')
            observed = json.loads(gzip.decompress(parent.input('training', raw=True)))[:CUT + LATER]
        with closing(ClosedStudy(root, 'data/' + WITNESS, store=store)) as witness:
            if witness.completion['manifest_sha256'] != WITNESS_MANIFEST:
                raise ValueError('exact opened shape-direction witness required')
            shape, snapshot = witness.input('shape-direction'), witness.input('later-operator', raw=True)
    matched = track[::2]
    if (len(matched) != CUT + LATER or observed[0] != anchor or len(track) != COUNT + 1
            or any(abs(row['seconds'] - other['time_s']) > .001
                   for row, other in zip(matched, observed, strict=True))):
        raise ValueError('unchanged position times and one earlier anchor required')
    reconstructed, original = [row['position'] for row in matched], coordinates(observed)
    errors = position_errors_neu(reconstructed, original)
    chart_origin = np.asarray(original[0])
    difference = _chart(reconstructed, chart_origin) - _chart(original, chart_origin)
    operator = restore(snapshot, expected_sha256=shape['factors_sha256'],
                       expected_configuration=shape['configuration'], maximum_bytes=2**26)
    direction = np.r_[np.zeros(3 * CUT), shape['direction']]
    total = float(direction @ operator.whiten(difference.ravel()))
    earlier_only = difference.copy()
    earlier_only[CUT:] = 0
    earlier_effect = float(direction @ operator.whiten(earlier_only.ravel()))
    result = dict(study_manifest_sha256=manifest_sha, pairs=COUNT, matched_reports=len(matched),
        earlier=error_metrics(errors[:CUT].tolist()), later=error_metrics(errors[CUT:].tolist()),
        earlier_score_effect=earlier_effect, later_score_effect=total - earlier_effect,
        original_signed_midpoint=baseline, carrier_signed_midpoint=baseline + total,
        signed_receiver_differences_m=errors.tolist(), minimum_satellites=min(
            len(row['satellites']) for row in track[1:]), new_inertial_fits=0,
        new_forecast_propagations=0, protected_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    output = root / RESULT
    if not output.exists():
        atomic(output, raw)
    if output.read_bytes() != raw:
        raise ValueError('saved continuous carrier report differs')
    print(encoded({k: v for k, v in result.items() if k != 'signed_receiver_differences_m'}
                  | dict(result_sha256=digest(raw))).decode(), end='')


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_carrier_phase_continuous {prepare,report}')
