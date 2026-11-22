# SPDX-License-Identifier: AGPL-3.0-or-later
"""Verify and summarize the closed fresh ESA solver comparison."""

import argparse
from contextlib import ExitStack, closing
import json
from pathlib import Path

from .esa_dispatch_pairs import BASE, ID, MATERIAL, METHODS, SCOPE, assess_group, tasks
from .studies.artifacts import digest, encoded


RESULT = BASE+'observed-dispatch-fresh-result.json'
PREFIX = 'data/'+ID


def summarize(declared, terminal, *, times, materials):
    identities = {case['identity'] for case in declared}
    if len(declared) != 16 or len(identities) != 16 or set(terminal) != identities:
        raise ValueError('all 16 terminal pairs are required')
    pairs, grouped = [], {}
    for case in declared:
        identity = case['identity']
        item = terminal[identity]
        outcome = item['result']
        spec = case['payload']
        group = (spec['model'], spec['profile'], spec['policy_id'])
        grouped.setdefault(group, {})[spec['start']] = dict(outcome, forecasts=item['forecasts'])
        pairs.append(dict(identity=identity, **spec, passed=outcome['passed'],
                          reason=outcome.get('reason', outcome.get('comparison', {}).get('reason')),
                          fits=outcome.get('fits', {}), source=item['source'], result_sha256=item['result_sha256']))
    if len(grouped) != 8 or any(set(starts) != {0, 1} for starts in grouped.values()):
        raise ValueError('eight fixed two-start comparisons required')
    groups = [dict(model=model, profile=profile, policy_id=policy,
                   **assess_group(starts, times=times, materials=materials))
              for (model, profile, policy), starts in grouped.items()]
    return dict(terminal_pairs=len(pairs), passing_pairs=sum(row['passed'] for row in pairs),
                equivalent_groups=sum(row['equivalent'] for row in groups),
                equivalent_on_window=all(row['equivalent'] for row in groups),
                pairs=pairs, groups=groups, forecast_positions_decoded=0,
                protected_reads=0, scientific_decision='abstain')


def closed_report(root, *, expected_manifest_sha256):
    from .ilvis0_control_shards import verify_completion
    from .studies.closed import ClosedStudy
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    original = root/PREFIX
    if not (original/'completion.json').is_file():
        raise ValueError('closed paired study required before reporting')
    verify_completion(original)
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, PREFIX)))
        if (parent.completion['manifest_sha256'] != expected_manifest_sha256
                or parent.manifest['scope'] != SCOPE
                or parent.manifest['adapter'] != 'analysis/lll/esa_dispatch_pairs.py'):
            raise ValueError('exact frozen paired comparison required')
        binding = parent.input('preparation')
        prepared = binding['result']
        declared = tasks(native_packets=prepared['native_packets'],
                         training_prefix_packets=prepared['training_prefix_packets'])
        frozen = [{key: value for key, value in task.items() if key not in ('index', 'shard')}
                  for task in parent.manifest['tasks']]
        if (declared != frozen
                or binding['files'] != {key: parent.manifest['inputs'][key]['sha256'] for key in MATERIAL}):
            raise ValueError('paired task and input bindings differ')
        times = parent.input('queries')['times_s']
        studies = [parent]
        recovery_sha256 = None
        if len(parent.rows) != len(declared) or any(
                parent.envelope(identity)['status'] != 'complete' for identity in parent.rows):
            recovery = root/(PREFIX+'-recovery')
            completion = recovery/'completion.json'
            if not completion.is_file() or resume_campaign(root, recovery, launch=False)['state'] != 'all_tasks_finished':
                raise ValueError('verified recovery closure required for unfinished pairs')
            recovery_sha256 = digest(completion.read_bytes())
            studies.extend(stack.enter_context(closing(ClosedStudy(
                root, stage.relative_to(root).as_posix(), store=parent.store)))
                for stage in _stage_paths(recovery))

        terminal = {}
        for study in studies:
            for identity in study.rows:
                envelope = study.envelope(identity)
                if envelope['status'] == 'interrupted':
                    continue
                if envelope['status'] != 'complete' or identity in terminal:
                    raise ValueError('one sealed terminal result required per pair')
                outcome = envelope['result']
                forecasts = {}
                if outcome['passed']:
                    if (outcome['forecast_positions_decoded'] != 0 or outcome['protected_reads'] != 0
                            or outcome['comparison'] != study.artifact(identity, 'comparison.json')):
                        raise ValueError('inconsistent or out-of-scope paired result')
                    forecasts = {method: study.artifact(identity, method+'-forecast.json') for method in METHODS}
                terminal[identity] = dict(result=outcome, forecasts=forecasts, source=study.prefix,
                                          result_sha256=envelope['result_sha256'])
        summary = summarize(declared, terminal, times=times, materials=binding['files'])
        closures = {study.prefix: study.completion for study in studies}
    return dict(summary, closures=closures, recovery_completion_sha256=recovery_sha256)


if __name__ == '__main__':
    from .ilvis0_matched_observed_inputs import _write_equal

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest-sha256', required=True)
    args = parser.parse_args()
    root = Path.cwd()
    result = closed_report(root, expected_manifest_sha256=args.manifest_sha256)
    _write_equal(root/RESULT, encoded(result))
    print(json.dumps({key: result[key] for key in
                      ('terminal_pairs', 'passing_pairs', 'equivalent_groups', 'equivalent_on_window')}, sort_keys=True))
