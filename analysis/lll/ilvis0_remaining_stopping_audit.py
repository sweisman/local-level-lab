# SPDX-License-Identifier: AGPL-3.0-or-later
"""Saved-only numerical stopping audit of the twenty-group forecast transfer."""

from collections import Counter
import hashlib
from pathlib import Path
from statistics import median

STUDY='data/ilvis0-remaining-prediction-transfer-20261118'
MANIFEST_SHA256='3cc9a72f3c3f3fa10c3f867fe31443fecfb7ee320dcb3567692d0af678c2863e'
FROZEN_STOPPING_SOURCE='analysis/lll/ilvis0_solver_refinement.py'
FROZEN_STOPPING_SHA256='442dd52979f4db0973a29c7553ab5b0f02ba90e847dbea2f7db99735ade1db0f'
FROZEN_RELATIVE_COST_TOLERANCE=1e-8


def classify(fit):
    probe=fit.get('stability_probe')
    count=fit.get('evaluations')
    limit=fit.get('maximum_evaluations')
    gradient=fit.get('exact_projected_gradient_relative')
    tolerance=fit.get('stationarity_tolerance')
    if (not isinstance(probe,dict) or not isinstance(probe.get('reason'),str)
            or type(count) is not int or type(limit) is not int
            or not 0<=count<=limit or not isinstance(gradient,(int,float))
            or not isinstance(tolerance,(int,float)) or tolerance<=0
            or not isinstance(fit.get('active_bounds'),list)
            or type(fit.get('converged')) is not bool):
        raise ValueError('complete saved numerical stopping record required')
    if fit['converged'] != (probe.get('passed') is True and gradient<=tolerance):
        raise ValueError('saved pass flag differs from frozen stopping rule')
    failed=[]
    if gradient>tolerance:
        failed.append('stationarity')
    if probe['reason']=='fresh_position_probe_not_stable':
        checks=(
            ('cost',probe.get('actual_cost_change'),FROZEN_RELATIVE_COST_TOLERANCE),
            ('fresh_stationarity',probe.get('fresh_stationarity'),tolerance),
            ('position_rms',max(probe.get('position_rms_neu_m',[]),default=None),
             probe.get('position_rms_tolerance_m')),
            ('position_maximum',max(probe.get('position_max_abs_neu_m',[]),default=None),
             probe.get('position_max_tolerance_m')))
        if any(value is None or limit is None for _,value,limit in checks):
            raise ValueError('complete fresh position probe required')
        failed.extend(name for name,value,limit in checks if value>limit)
        if not failed:
            raise ValueError('nonpassing fresh probe must fail a frozen check')
    return dict(passed=fit['converged'],probe_reason=probe['reason'],
                evaluations=count,maximum_evaluations=limit,
                allowance_exhausted=count>=limit,
                stationarity_passed=gradient<=tolerance,
                failed_components=failed,
                active_bound_count=len(fit['active_bounds']),
                actual_cost_change=probe.get('actual_cost_change'),
                fresh_stationarity=probe.get('fresh_stationarity'),
                position_rms_neu_m=probe.get('position_rms_neu_m'),
                position_max_abs_neu_m=probe.get('position_max_abs_neu_m'))


def summarize(fits):
    rows=[classify(fit) for fit in fits]
    if not rows:
        raise ValueError('saved stopping records required')
    return dict(version='ilvis0-remaining-stopping-audit-v1',
                starts=len(rows),passing=sum(r['passed'] for r in rows),
                nonpassing=sum(not r['passed'] for r in rows),
                allowance_exhausted=sum(r['allowance_exhausted'] for r in rows),
                stationarity_failed=sum(not r['stationarity_passed'] for r in rows),
                at_least_one_bound=sum(r['active_bound_count']>0 for r in rows),
                maximum_evaluations_used=max(r['evaluations'] for r in rows),
                median_evaluations_used=median(r['evaluations'] for r in rows),
                reasons=dict(sorted(Counter(r['probe_reason'] for r in rows).items())),
                failed_component_counts=dict(sorted(Counter(
                    name for row in rows for name in row['failed_components']).items())),
                rows=rows,refits=0,original_reads=0,
                failed_fits_reclassified=False,scientific_decision='abstain')


def build(root='.'):
    from .studies.closed import ClosedStudy
    root=Path(root).resolve()
    study=ClosedStudy(root,STUDY)
    try:
        if (study.completion['manifest_sha256']!=MANIFEST_SHA256
                or study.completion['state'] not in ('complete','terminal')
                or len(study.tasks)!=80 or len(study.rows)!=80
                or study.manifest['sources'].get(FROZEN_STOPPING_SOURCE)!=
                FROZEN_STOPPING_SHA256 or hashlib.sha256(
                    (root/FROZEN_STOPPING_SOURCE).read_bytes()).hexdigest()!=
                FROZEN_STOPPING_SHA256):
            raise ValueError('exact closed eighty-fit study required')
        identities=list(study.tasks)
        fits=[study.artifact(identity,'fit.json') for identity in identities]
        report=summarize(fits)
        if report['starts']!=80 or report['passing']!=30:
            raise ValueError('saved fit total differs from sealed study')
        for identity,fit,row,detail in zip(identities,fits,
                                           (study.rows[i] for i in identities),
                                           report['rows']):
            if row['passed']!=detail['passed']:
                raise ValueError('saved stopping status differs from sealed task')
            detail['identity']=identity
            detail['origin']=study.tasks[identity]['payload']['origin']
        report.update(study=STUDY,manifest_sha256=MANIFEST_SHA256,
                      completion_summary_sha256=study.completion['summary_sha256'],
                      source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        return report
    finally:
        study.close()


def render(report):
    lines=['# Saved stopping audit for the twenty-group forecast extension','',
           f"All {report['starts']} planned fits are included: "
           f"{report['passing']} passed and {report['nonpassing']} did not.",
           f"No fit used its full 200-evaluation allowance; the maximum was "
           f"{report['maximum_evaluations_used']}. "
           f"{report['stationarity_failed']} failed the final stationarity check. "
           f"All {report['at_least_one_bound']} fits had at least one calibration "
           'parameter at a permitted bound.','',
           '| Fresh stopping probe | Fits |','|---|---:|']
    lines += [f'| `{reason}` | {count} |'
              for reason,count in report['reasons'].items()]
    lines += ['', 'Failed checks within the nonpassing starts can overlap:', '',
              '| Frozen check | Fits |', '|---|---:|']
    lines += [f'| {name.replace("_", " ")} | {count} |'
              for name,count in report['failed_component_counts'].items()]
    lines += ['',
        'This is a saved-data numerical diagnosis. It does not turn a failed fit',
        'into a pass or show that the fitted physical model is adequate. The',
        'nearby starts can have similar costs even when both fail their frozen',
        'stopping checks. A new solver qualification would need separate',
        'known-answer controls and a new finite observed study.', '',
        '[All starts and scores](remaining-fit-audit.csv) · '
        '[Complete stopping fields](remaining-stopping-audit.json) · '
        '[Forecast transfer result](REMAINING_GROUPS_PREDICTION_RESULT.md)']
    return '\n'.join(lines)+'\n'


def publish(root='.'):
    from .studies.artifacts import atomic,encoded
    root=Path(root).resolve()
    report=build(root)
    base=root/'docs/prediction-group-transfer'
    atomic(base/'remaining-stopping-audit.json',encoded(report))
    atomic(base/'REMAINING_GROUPS_STOPPING_AUDIT.md',render(report).encode())
    return report


if __name__=='__main__':
    report=publish()
    print({key:report[key] for key in ('starts','passing','nonpassing',
                                      'stationarity_failed','allowance_exhausted')})
