# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test a receiver-common Doppler correction on the fixed Nuuk comparison."""

import argparse
from contextlib import closing
import json
import math
from pathlib import Path
from statistics import median

from . import esa_nuuk_carrier_screen as audit
from . import esa_nuuk_near_stations as near
from .esa_carrier_phase_support import DUAL_DIFFERENCE_LIMIT_M, L1_WAVELENGTH, L2_WAVELENGTH
from .esa_qaq_ground_score import reference_residual
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import encoded
from .studies.closed import ClosedStudy


ID = 'esa-nuuk-clock-aware-v1'
SCOPE = 'Hold out each satellite from the permanent Nuuk Doppler clock estimate'
PLAN = near.BASE + 'ESA_NUUK_CLOCK_AWARE_PLAN.md'
RESULT = near.BASE + 'esa-nuuk-clock-aware-result.json'
AUDIT_SHA = 'fbccc3b591e945dcc32f4cab6c6c2d3ef6cf818b57720ebfd64d96bd60972552'
PEERS = 5
STEPS = 64 + 32**2
TASK = dict(identity='clock-aware-compare', input_key='ground', payload={}, limits=dict(
    native_calls=0, packet_visits=0, bound_calls=1+near.COUNT+3, bound_steps=1+(STEPS+3)*near.COUNT))


def clock_aware_residual(first, last, candidates, continued, model):
    """Change only the Doppler comparison, retaining both original phase increments."""
    gaps = {}
    for prn in set(candidates) & continued:
        a, b = first['satellites'][prn], last['satellites'][prn]
        _, gap = audit.inspect_satellite(a, b)
        if gap is None:
            continue
        l1 = L1_WAVELENGTH*(b['l1'][0]-a['l1'][0])
        l2 = L2_WAVELENGTH*(b['l2']['2W'][0]-a['l2']['2W'][0])
        if abs(l1-l2) <= DUAL_DIFFERENCE_LIMIT_M:
            gaps[prn] = gap
    ends = dict(last['satellites'])
    if len(gaps) > PEERS:
        for prn in gaps:
            offset = median(gap for satellite, gap in gaps.items() if satellite != prn)
            ends[prn] = dict(ends[prn], doppler=ends[prn]['doppler']-2*offset)
    return reference_residual(first, dict(last, satellites=ends), candidates, continued, model)


def prepare(root):
    from .esa_calibration_conditioned_margin import RECOVERY
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('preserve the original finite clock-aware check')
    near._verified(root, audit.RESULT, AUDIT_SHA)
    baseline = json.loads(near._verified(root, near.RESULT, audit.PARENT_SHA))
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+near.ID)) as parent:
        if (parent.completion != baseline['completion']
                or parent.envelope(near.TASK['identity'])['charged'] != near.TASK['limits']):
            raise ValueError('preserve the original finite comparison and source evidence')
        inputs = {name: parent.input(name, raw=True) for name in (
            'intake', 'ranges', 'score', 'museum', 'qaqortoq', 'ground', 'navigation', 'orbit', 'clock', 'recovery_policy')}
    files = dict(plan=PLAN, baseline=near.RESULT, diagnostic=audit.RESULT)
    for name, raw in dict(inputs, recovery=recovery, recovery_tests=tests).items():
        path = f'data/{ID}-inputs/{name}'
        _write_equal(root/path, raw)
        files[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, (adapter, PLAN, 'analysis/tests/test_esa_nuuk_clock_aware.py'))
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=files, sources=sources, tasks=[TASK],
                      workers=1, threads=1, maximum_wall_s=60)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def compare_support(original, alternative):
    from .shared_motion_carrier import centre

    old, new = [{r['start_gps_s']: r for r in rows} for rows in (original, alternative)]
    added = [new[time] for time in sorted(new.keys() - old.keys())]
    differences = []
    for time in old.keys() & new.keys():
        def values(row):
            return dict(zip(row['satellites'], row['permanent_m'], strict=True))

        first, last = values(old[time]), values(new[time])
        common = sorted(first.keys() & last.keys())
        if common:
            delta = centre([first[p]-last[p] for p in common])
            differences.extend(abs(delta))
    max_difference = max(map(float, differences), default=None)
    if max_difference is None or max_difference > 1e-12:
        raise ValueError('the same original phase ranges must reproduce on common satellites')
    new_pairs = len(near.flatten(added, 'museum_m'))
    return dict(old_intervals=len(old), additional_intervals=len(added), lost_intervals=len(old.keys()-new.keys()),
                shared_ranges=len(differences), maximum_shared_range_change_m=max_difference,
                new_intervals_ranges=new_pairs, new_intervals_difference_rms_m=(
                    near._difference(near.flatten(added, 'museum_m'), near.flatten(added, 'permanent_m'))
                    if new_pairs else None))


def evaluate(task, context):
    if (context.manifest['scope'] != SCOPE
            or {key: value for key, value in task.items() if key not in ('index', 'shard')} != TASK):
        raise ValueError('the fixed clock-aware comparison is required')
    baseline = json.loads(context.input_path('baseline').read_bytes())
    permanent, museum, qaqortoq, gap = near.compare_frozen_score(context, ground_residual=clock_aware_residual,
                                                                interval_steps=STEPS)
    result = near.summarize_comparison(context, permanent, museum, qaqortoq, gap)
    support = near.matched_rows(museum=museum['intervals'], permanent=permanent['intervals'])
    result['support_check'] = compare_support(baseline['evidence']['near'], support)
    result['minimum_doppler_peers'] = PEERS
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        envelope = study.envelope(TASK['identity'])
        if envelope['charged'] != TASK['limits'] or not envelope['result']['passed']:
            raise ValueError('complete finite clock-aware result required')
        summary = dict(envelope['result'], completion=study.completion, charged=envelope['charged'],
                       inputs=study.manifest['inputs'])
        evidence = study.artifact(TASK['identity'], 'shared-range-evidence.json')
    _write_equal(root/RESULT, encoded(dict(summary, evidence=evidence)))
    return {k: v for k, v in summary.items() if k != 'inputs'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'report'))
    print(json.dumps({'prepare': prepare, 'report': report}[parser.parse_args().action](Path.cwd()), sort_keys=True))
