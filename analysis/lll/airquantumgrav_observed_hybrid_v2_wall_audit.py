# SPDX-License-Identifier: AGPL-3.0-or-later
"""Read-only account of the sealed revised-tangent wall-cap outcome."""
import hashlib
from pathlib import Path

from lll.airquantumgrav_observed_hybrid_v2_report import build as base_report
from lll.studies.artifacts import atomic, encoded
from lll.studies.closed import ClosedStudy


STUDY = 'data/esa-observed-hybrid-v2-three-pair-development'
WIDE = ('wide-fit.json', 'wide-forecast.json', 'wide-scores.json',
        'wide-input-binding.json')


def build(root='.'):
    root = Path(root).resolve()
    base = base_report(root)
    if (base['tasks'] != 3 or base['returned'] != 3 or
            base['passing_pairs'] != 0 or base['native_calls'] != 349 or
            base['substitution_qualified'] is not False):
        raise ValueError('exact closed three-pair wall-cap outcome required')
    study = ClosedStudy(root, STUDY)
    try:
        if (study.completion['state'] != 'terminal' or
                study.summary['charged']['native_calls'] != 349 or
                set(study.rows) != set(study.tasks)):
            raise ValueError('terminal task coverage and charges changed')
        rows = []
        for identity in sorted(study.tasks):
            envelope = study.envelope(identity)
            result = envelope['result']
            names = set(envelope['artifacts'])
            prefix = 'artifacts/' + identity + '/'
            if (envelope['status'] != 'complete' or result.get('passed') is not False or
                    result.get('error_type') != 'BudgetStopped' or
                    result.get('reason') != 'original cooperative deadline exhausted' or
                    any(prefix + name not in names for name in WIDE) or
                    any(prefix + name in names for name in
                        ('hybrid-fit.json', 'hybrid-forecast.json', 'comparison.json'))):
                raise ValueError('sealed cap failure or partial-fit evidence differs')
            fit = study.artifact(identity, 'wide-fit.json')
            for name in WIDE[1:]:
                study.artifact(identity, name, raw=True)
            evaluations = fit.get('evaluations')
            if (type(evaluations) is not int or not 0 < evaluations <= 200 or
                    type(fit.get('converged')) is not bool or
                    type(fit.get('stopping_rule_verified')) is not bool):
                raise ValueError('complete wide numerical stopping record required')
            rows.append(dict(identity=identity,
                             charged_native_calls=envelope['charged']['native_calls'],
                             wide_evaluations=evaluations,
                             wide_numerical_passed=(fit['converged'] and
                                                    fit['stopping_rule_verified']),
                             wide_fit_and_forecast_saved=True,
                             revised_fit_and_forecast_saved=False,
                             paired_comparison_complete=False,
                             reason=result['reason']))
        if sum(row['charged_native_calls'] for row in rows) != 349:
            raise ValueError('per-task charges differ from closed total')
        if sum(row['wide_numerical_passed'] for row in rows) != 2:
            raise ValueError('saved wide numerical disposition changed')
        source = root/'analysis/lll/airquantumgrav_observed_hybrid_v2_wall_audit.py'
        return dict(verified=True, study=STUDY,
                    manifest_sha256=study.completion['manifest_sha256'],
                    summary_sha256=study.completion['summary_sha256'],
                    auditor_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    sealed_budget_failures=3, paired_comparisons_passed=0,
                    wide_numerical_passing_fits=2,
                    charged_native_calls=349, unfinished_tasks=0,
                    continuation_of_unfinished_tasks_applicable=False,
                    substitution_qualified=False,
                    scientific_decision='abstain', rows=rows)
    finally:
        study.close()


def render(report):
    lines = ['# Three-pair method check: wall-cap audit', '',
             '**The revised method is not qualified.** All three paired tasks',
             'reached the frozen four-hour wall cap before a paired comparison',
             'was saved. The run charged 349 native calls and sealed every task',
             'as a budget failure. No task remains unfinished, so the prepared',
             'unfinished-task recovery route does not apply.', '',
             'Two saved wide fits passed their numerical stopping checks; one did not.',
             'That partial result cannot qualify the revised method.', '',
             '| Development case | Charged calls | Wide stopping check | Revised fit and forecast |',
             '|---|---:|---|---|']
    for row in report['rows']:
        lines.append(f"| {row['identity']} | {row['charged_native_calls']} | "
                     f"{'pass' if row['wide_numerical_passed'] else 'fail'} "
                     f"({row['wide_evaluations']} evaluations) | Not completed |")
    lines += ['', 'The saved wide-method artifacts are partial task evidence.',
              'They do not make any paired result pass. The established wide',
              'method remains the qualified implementation for this development',
              'analysis. This method check makes no Earth-model decision.', '',
              '[Verified paired-result table](README.md) · '
              '[Frozen plan](../../mixed-tangent-hybrid/V2_PAIRED_PLAN.md)']
    return '\n'.join(lines) + '\n'


def publish(root='.'):
    root = Path(root).resolve()
    report = build(root)
    target = root/'docs/esa-observed-hybrid/three-pair-v2'
    atomic(target/'WALL_CAP.md', render(report).encode())
    atomic(target/'verified-wall-cap.json', encoded(report))
    return report


if __name__ == '__main__':
    report = publish()
    print(f"{report['sealed_budget_failures']}/3 sealed wall-cap failures; "
          f"{report['charged_native_calls']} native calls")
