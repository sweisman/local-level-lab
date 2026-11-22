# SPDX-License-Identifier: AGPL-3.0-or-later
"""Count distinct charges for full proposals repeated at the same saved point."""

from contextlib import closing
import json
from pathlib import Path
import sys

from .ilvis0_matched_unstarted_recovery import ARCHIVE, MANIFEST, SUMMARY
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


SOURCE = 'analysis/lll/ilvis0_solver_trust_v2.py'
RESULT = 'docs/ilvis0-measurement-contribution/matched-repeated-trial-audit.json'


def repeat_rows(fit):
    first = None
    repeated = []
    traced = {row['evaluation'] for row in fit['evaluation_trace'] if not row['fresh']}
    for row in fit['step_history']:
        if row['accepted']:
            first = None
        elif row.get('method') == 'full_bounded':
            key = tuple(row[field] for field in ('cost', 'predicted_reduction', 'actual_reduction',
                                                 'normalized_step', 'agreement_ratio'))
            if first is None:
                first = (key, row['evaluation'])
            elif first[0] != key:
                raise ValueError('full proposal changed with no accepted step')
            elif row['evaluation'] != first[1] and row['evaluation'] in traced:
                repeated.append(dict(first=first[1], repeat=row['evaluation']))
    if len({row['repeat'] for row in repeated}) != len(repeated):
        raise ValueError('multiple repeat rows claim one evaluation charge')
    return repeated


def build(root):
    with closing(ClosedStudy(root, ARCHIVE)) as study:
        if (study.completion['manifest_sha256'], study.completion['summary_sha256']) != (MANIFEST, SUMMARY):
            raise ValueError('exact closed preflight required')
        source_sha = study.manifest['sources'][SOURCE]
        study.read('source-freeze/'+SOURCE, source_sha, raw=True)
        results = []
        for identity in study.rows:
            fit = study.artifact(identity, 'fit.json')
            row = study.rows[identity]
            charges = row['charged']['native_calls']
            if (fit['evaluations'] + int(row['passed']) != charges
                    or len(fit['evaluation_trace']) != fit['evaluations']):
                raise ValueError('solver trace differs from sealed charges: '+identity)
            results.append(dict(identity=identity, evaluations=fit['evaluations'],
                converged=fit['converged'], fresh_probe=fit['stability_probe'],
                repeated_full_rejections=repeat_rows(fit)))
    return dict(preflight_manifest_sha256=MANIFEST, preflight_summary_sha256=SUMMARY,
                historical_solver_source_sha256=source_sha, rows=results, scientific_decision='abstain')


def main():
    if sys.argv[1:] not in (['write'], ['check']):
        raise SystemExit('usage: python -m lll.ilvis0_repeated_trial_audit {write,check}')
    root = Path.cwd()
    raw = encoded(build(root))
    path = root/RESULT
    if sys.argv[1:] == ['write'] and not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved repeat audit differs')
    print(json.dumps(dict(result=RESULT, sha256=digest(raw)), sort_keys=True))


if __name__ == '__main__':
    main()
