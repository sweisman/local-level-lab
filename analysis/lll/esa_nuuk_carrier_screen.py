# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit the frozen permanent Nuuk ground-carrier screen without changing it."""

import argparse
from collections import Counter
from contextlib import closing
import gzip
import json
import math
from pathlib import Path
from statistics import median

from . import esa_nuuk_near_stations as near
from .esa_carrier_phase_support import DUAL_DIFFERENCE_LIMIT_M, L1_DOPPLER_LIMIT_CYCLES, L1_WAVELENGTH, L2_WAVELENGTH
from .esa_qaq_ground_score import reference_residual
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-nuuk-carrier-screen-v1'
SCOPE = 'Diagnostic of the unchanged permanent Nuuk phase-continuity screen'
PLAN = near.BASE + 'ESA_NUUK_CARRIER_SCREEN_PLAN.md'
RESULT = near.BASE + 'esa-nuuk-carrier-screen-result.json'
PARENT_SHA = '49ce115480ab13a1cd95405f2b4a3f93c0d87f5dcf5cd67c05bb90d94c59fa7e'
TASK = dict(identity='nuuk-carrier-screen', input_key='ground', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+near.COUNT, bound_steps=1+32*near.COUNT))


def inspect_satellite(first, last):
    endpoints = (first, last)
    if any(row['code_m'] is None or not 1e6 < row['code_m'] < 6e7 for row in endpoints):
        return 'missing_or_invalid_code', None
    if any(row['l1'] is None or row['doppler'] is None or '2W' not in row['l2'] for row in endpoints):
        return 'missing_phase_or_doppler', None
    if any(row['l1'][1] or row['l2']['2W'][1] for row in endpoints):
        return 'loss_of_lock', None
    cycles = last['l1'][0]-first['l1'][0]
    doppler_gap = cycles+(first['doppler']+last['doppler'])/2.
    if abs(doppler_gap) > L1_DOPPLER_LIMIT_CYCLES:
        return 'l1_doppler', doppler_gap
    d1 = L1_WAVELENGTH*cycles
    d2 = L2_WAVELENGTH*(last['l2']['2W'][0]-first['l2']['2W'][0])
    if abs(d1-d2) > DUAL_DIFFERENCE_LIMIT_M:
        return 'dual_phase', doppler_gap
    return 'passes', doppler_gap


def doppler_pattern(values):
    if len(values) < 5:
        return None
    middle = median(values)
    return dict(median_cycles=middle,
                centered_rms_cycles=math.sqrt(math.fsum((x-middle)**2 for x in values)/len(values)),
                numeric=len(values))


def prepare(root):
    from .esa_calibration_conditioned_margin import RECOVERY
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    raw = near._verified(root, near.RESULT, PARENT_SHA)
    with closing(ClosedStudy(root, 'data/'+near.ID)) as parent:
        if (parent.completion != json.loads(raw)['completion']
                or parent.envelope(near.TASK['identity'])['charged'] != near.TASK['limits']):
            raise ValueError('the original complete nearby-station comparison is required')
        frozen = {key: parent.input(key, raw=True) for key in ('ground', 'intake', 'ranges', 'recovery_policy')}
    inputs = dict(plan=PLAN, parent=near.RESULT)
    for key, data in dict(frozen, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{key}'
        _write_equal(root/path, data)
        inputs[key] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_nuuk_carrier_screen.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=[TASK], workers=1, threads=1, maximum_wall_s=30)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the frozen station screen audit is required')
    context.charge(bound_calls=1, bound_steps=1)
    receipt, ranges, parent = [json.loads(context.input_path(key).read_bytes()) for key in ('intake', 'ranges', 'parent')]
    ground, _ = near.decode_ground(gzip.decompress(context.input_path('ground').read_bytes()))
    arcs = {r['time_s']: {int(sv[1:]) for sv in r['continued']} for r in receipt['rows']}
    retained = {r['start_gps_s']: set(r['satellites']) for r in parent['evidence']['near']}
    counts = {'retained': Counter(), 'excluded': Counter()}
    details = []
    for index, time in enumerate(range(near.FIRST, near.LAST)):
        context.charge(bound_calls=1, bound_steps=32)
        halves = ranges['rows'][2*index:2*index+2]
        if [r['seconds'] for r in halves] != [time+.5, time+1]:
            raise ValueError('wrong fixed aircraft half-second support')
        prns = set(halves[0]['common_satellites']) & set(halves[1]['common_satellites'])
        first, last = ground[time], ground[time+1]
        accepted, reasons, gaps = set(), Counter(), []
        for prn in sorted(prns):
            if prn not in arcs[time+1]:
                reasons['continuity_or_required_signal'] += 1
                continue
            status, gap = inspect_satellite(first['satellites'][prn], last['satellites'][prn])
            reasons[status] += 1
            if gap is not None:
                gaps.append(gap)
            if status == 'passes':
                accepted.add(prn)
        original = reference_residual(first, last, prns, arcs[time+1],
                                      lambda a, b, sats, codes: dict.fromkeys(sats, 0.))
        if accepted != set(original) or not retained.get(time, set()) <= accepted:
            raise ValueError('the original carrier acceptance did not reproduce')
        state = 'retained' if time in retained else 'excluded'
        counts[state].update(reasons)
        details.append(dict(time_gps_s=time, state=state, pregeometry_passes=len(accepted),
                            reasons=dict(reasons), doppler=doppler_pattern(gaps)))
    excluded = [row for row in details if row['state'] == 'excluded']
    pattern = [row['doppler'] for row in excluded if row['doppler'] is not None]
    context.save('interval-screen.json', details)
    return dict(passed=True, scientific_decision='abstain', thresholds_unchanged=True, new_fits=0,
                protected_reads=0, intervals=len(details), excluded=len(excluded),
                excluded_before_geometry=sum(row['pregeometry_passes'] < 5 for row in excluded),
                excluded_median_beyond_doppler_limit=sum(abs(row['median_cycles']) > L1_DOPPLER_LIMIT_CYCLES
                                                         for row in pattern),
                excluded_doppler_profiles=len(pattern), counts={key: dict(value) for key, value in counts.items()})


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('the completed finite station screen audit is required')
        summary = dict(envelope['result'], completion=study.completion, charged=envelope['charged'], parent_sha256=PARENT_SHA)
        rows = study.artifact(TASK['identity'], 'interval-screen.json')
    _write_equal(root/RESULT, encoded(dict(summary, rows=rows)))
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
