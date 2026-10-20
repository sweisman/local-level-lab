# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reconcile every sealed reservation; no LP, bound or native execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_control_shards as runner
from lll.ilvis0_support_accounting import check_case

DATA=ROOT/'data/ilvis0-conditioned-prediction-20261020'
PUBLIC=Path(__file__).resolve().parent
STEPS=[(1,3)]*6+[(0,6)]+[(1,3)]*6+[(0,6)]


def audit():
    manifest=runner.verify(DATA);summary=runner.verify_completion(DATA)
    if not summary['passed'] or len(summary['results'])!=48:raise ValueError('complete passing 48-case evidence required')
    cases=[]
    for item in summary['results']:
        record=runner._load(DATA/item['artifact']);identity=record['result']['identity']
        task=next(t for t in manifest['tasks'] if t['identity']==identity)
        cases.append(check_case(DATA,record,steps=STEPS,
            maximum_proposals=task['payload']['maximum_proposals'],
            maximum_supports=task['payload']['maximum_exact_supports']))
    proposals=sum(r['lp_proposals'] for r in cases);supports=sum(r['exact_supports'] for r in cases)
    if proposals!=576 or supports!=2304:raise ValueError('global reservations do not reconcile')
    return dict(passed=True,cases=cases,reservation_events=sum(r['reservation_events'] for r in cases),
        lp_proposals=proposals,maximum_lp_proposals=576,exact_supports=supports,maximum_exact_supports=2304,
        charged_native_calls=summary['charged']['native_calls'],charged_bound_calls=summary['charged']['bound_calls'],
        new_lp_proposals=0,new_native_evaluations=0,new_bound_evaluations=0,
        manifest_sha256=runner._sha(DATA/'manifest.json'),summary_sha256=runner._sha(DATA/'summary.json'),
        audit_scope='sealed reservations and result consistency; execution counts also rely on the frozen instrumented controls',
        scientific_decision='abstain')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true')
    args=parser.parse_args();report=audit()
    if args.write:
        (PUBLIC/'accounting.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
        (PUBLIC/'ACCOUNTING.md').write_text(
            '# Proposal and support accounting\n\n'
            'All 48 cases reconcile with their hashed reservation events: **576/576 LP '
            'proposals and 2,304/2,304 exact support evaluations**. Each case has fourteen '
            'ordered events, charged before execution. No missing, extra or changed '
            'event is accepted. The twelve proposals and 48 supports per case include '
            'fallbacks, the independent acceleration consumer and the final endpoint audit.\n\n'
            'The study charged 48 enclosure calls and zero native prediction calls. '
            'Frozen local instrumentation checks the support-call protocol; this saved-only '
            'audit reconciles its recorded charges without repeating computations. '
            'It does not independently observe every executed arithmetic operation.\n\n'
            '[Prediction results](README.md) · [Frozen limits](PLAN.md).\n')
        names=['accounting.json','ACCOUNTING.md','check_accounting.py']
        sources=['analysis/lll/ilvis0_support_accounting.py','analysis/tests/test_ilvis0_support_accounting.py']
        receipt=dict(artifacts={n:runner._sha(PUBLIC/n) for n in names},
            sources={n:runner._sha(ROOT/n) for n in sources},
            study_manifest_sha256=report['manifest_sha256'],study_summary_sha256=report['summary_sha256'])
        (PUBLIC/'accounting-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'}))


if __name__=='__main__':main()
