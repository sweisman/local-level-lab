# SPDX-License-Identifier: AGPL-3.0-or-later
"""Audit value-only proposal work from sealed ESA solver traces."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .esa_direction_holdout_forecast import frozen_input
from .esa_dispatch_pair_report import BASE, METHODS, PREFIX
from .esa_dispatch_pair_report import RESULT as PARENT_RESULT
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-dispatch-trial-work-v1'
SCOPE = 'count distinct trial evaluations and avoidable derivatives from 32 saved ESA fits'
PLAN = BASE+'OBSERVED_TRIAL_WORK_PLAN.md'
RESULT = BASE+'observed-trial-work-result.json'
PARENT_MANIFEST = '9e4f8af256bab5270a216b5d83c97b614a69a1ede6270ec10574fa7caa3c4d1f'
PARENT_SHA = '781bb1eae88ee8761bcfa800baf82c21cb470d3836f39e19b7ddb06674429d41'
FIT_COUNT = 32
TASK = dict(identity='count-saved-trial-work', input_key='comparison', payload={},
            limits=dict(native_calls=0, packet_visits=0, bound_calls=FIT_COUNT, bound_steps=FIT_COUNT))
COUNTS = ('tangent_calls', 'value_only_calls', 'avoided_tangent_calls', 'planned_tangent_calls')


def trial_work(fit):
    """Separate proposed trials from initial, accepted and fresh checks."""
    count = fit['evaluations']
    trace = fit['evaluation_trace']
    if (type(count) is not int or count < 1 or len(trace) != count
            or any(type(row['evaluation']) is not int or row['evaluation'] != index
                   or type(row['fresh']) is not bool for index, row in enumerate(trace, 1))):
        raise ValueError('complete ordered unique fit evaluation trace required')

    trial, accepted = set(), set()
    for row in fit['step_history']:
        index = row['evaluation']
        if (type(index) is not int or not 2 <= index <= count
                or trace[index-1]['fresh'] or type(row['accepted']) is not bool):
            raise ValueError('trial must refer to a saved noninitial nonfresh evaluation')
        trial.add(index)
        if row['accepted']:
            accepted.add(index)
    avoided = len(trial-accepted)
    return dict(tangent_calls=count, value_only_calls=len(trial), avoided_tangent_calls=avoided,
                planned_tangent_calls=count-avoided, break_even_ratio=avoided/len(trial) if trial else None)


def method_summary(pairs):
    summary = {}
    for method in METHODS:
        rows = [pair['work'][method] for pair in pairs]
        counts = {key: sum(row[key] for row in rows) for key in COUNTS}
        baseline = counts['tangent_calls']
        avoided = counts['avoided_tangent_calls']
        proposals = counts['value_only_calls']
        summary[method] = dict(counts, fits=len(rows), fits_with_savings=sum(row['avoided_tangent_calls'] > 0 for row in rows),
                               avoided_fraction=avoided/baseline,
                               break_even_ratio=avoided/proposals if proposals else None)
    return summary


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists() or digest((root/PARENT_RESULT).read_bytes()) != PARENT_SHA:
        raise ValueError('new audit and unchanged published paired result required')
    with closing(ClosedStudy(root, PREFIX)) as parent:
        if (parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']
                or len(parent.rows)*len(METHODS) != FIT_COUNT):
            raise ValueError('all sealed fits from the exact parent comparison are required')

    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs={'comparison': PARENT_RESULT},
        tasks=[TASK], sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_dispatch_trial_work.py']),
        workers=1, threads=1, maximum_wall_s=120.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    declared = {name: value for name, value in task.items() if name not in ('index', 'shard')}
    if declared != TASK or context.manifest['scope'] != SCOPE:
        raise ValueError('exact finite solver history audit required')
    source = frozen_input(context, 'comparison', PARENT_SHA)
    pairs = []
    with closing(ClosedStudy(context.root.parents[1], PREFIX)) as parent:
        if (source['closures'] != {PREFIX: parent.completion}
                or parent.completion['manifest_sha256'] != PARENT_MANIFEST
                or source['forecast_positions_decoded'] != 0 or source['protected_reads'] != 0
                or len(source['pairs'])*len(METHODS) != FIT_COUNT
                or {row['identity'] for row in source['pairs']} != set(parent.rows)):
            raise ValueError('sealed source and published fit identities differ')
        for row in source['pairs']:
            identity = row['identity']
            envelope = parent.envelope(identity)
            if (row['source'] != PREFIX or not row['passed'] or envelope['status'] != 'complete'
                    or row['result_sha256'] != envelope['result_sha256']
                    or row['fits'] != envelope['result']['fits']):
                raise ValueError('fit result binding differs from the paired report')
            work = {}
            for method in METHODS:
                context.charge(bound_calls=1, bound_steps=1)
                fit = parent.artifact(identity, method+'-fit.json')
                baseline = row['fits'][method]
                if (fit['evaluations'] != baseline['evaluations'] or fit['model'] != row['model']
                        or fit['converged'] != baseline['converged']
                        or fit['residual_sum_squares'] != baseline['training_cost']):
                    raise ValueError('fit trace differs from the bound numerical result')
                work[method] = trial_work(fit)
            if sum(values['tangent_calls']+1 for values in work.values()) != envelope['charged']['native_calls']:
                raise ValueError('paired native charges differ from recorded evaluations and forecasts')
            pairs.append(dict(identity=identity, paired_result_sha256=row['result_sha256'], work=work))

    summary = method_summary(pairs)
    context.save_bytes('trial-work.json', encoded(dict(pairs=pairs, methods=summary,
        parent_manifest_sha256=PARENT_MANIFEST, comparison_sha256=PARENT_SHA,
        new_fits=0, original_reads=0, protected_reads=0, scientific_decision='abstain')))
    return dict(passed=True, fits=FIT_COUNT, scientific_decision='abstain')


def report(root):
    identity = TASK['identity']
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.rows[identity]['charged'] != TASK['limits']:
            raise ValueError('complete audit and exact read allowance required')
        result = study.artifact(identity, 'trial-work.json')
        pairs = result['pairs']
        if (len(pairs)*len(METHODS) != FIT_COUNT or len({row['identity'] for row in pairs}) != len(pairs)
                or result['methods'] != method_summary(pairs)):
            raise ValueError('all fit traces and verified aggregate accounting required')
        result.update(manifest_sha256=study.completion['manifest_sha256'], charged=TASK['limits'])
    raw = encoded(result)
    target = root/RESULT
    if not target.exists():
        atomic(target, raw)
    if target.read_bytes() != raw:
        raise ValueError('saved audit receipt differs from the sealed evidence')
    return dict(sha256=digest(raw), methods=result['methods'])


if __name__ == '__main__':
    operation = {'prepare': prepare, 'report': report}[sys.argv[1]]
    print(json.dumps(operation(Path.cwd()), sort_keys=True))
