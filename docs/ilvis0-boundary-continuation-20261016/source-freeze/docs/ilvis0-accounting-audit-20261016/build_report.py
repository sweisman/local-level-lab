# SPDX-License-Identifier: AGPL-3.0-or-later
"""One saved-only audit; render-only never recalculates accounting."""
import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUTPUT=ROOT/'data'/HERE.name
PARENT=ROOT/'data/ilvis0-boundary-diagnostic-20261016'
sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_interrupted_accounting as audit


def write(path,value):
    from lll.ilvis0_receipt_journal import durable_write,encoded
    durable_write(path,encoded(value),replace=True)


def render(summary):
    for name in ('manifest.json','summary.json','completion.json'):shutil.copyfile(OUTPUT/name,HERE/name)
    text='# Accounting audit of the partial timing diagnostic\n\n'
    text+='**Eight saved checks verify intact: both controls, four passing endpoints and two unresolved endpoints.** '
    text+='A ninth identity was interrupted; twelve never started. No original journal or saved result was changed.\n\n'
    text+='The journal contains 162 valid call charges and an incomplete 163rd entry. All nine started identities '
    text+='keep their complete allowance reserved. A separate continuation may use only the twelve unstarted '
    text+='identities, at 26 calls each (312 maximum); the original combined ceiling remains 546.\n\n'
    text+='| Endpoint | Diagnostic passed | Outcome |\n|---|---|---|\n'
    for r in summary['saved_results'].values():text+=f"| `{r['source_identity']}` | {r['passed']} | {r['reason']} |\n"
    text+='\nThe two unresolved endpoints respectively lack supported side geometry and fail right-side stationarity. '
    text+='Passing local checks cannot replace complete model/case and repeat comparisons. Findings remain 47 globe / zero flat / six unresolved.\n\n'
    text+='Fault injection reproduces the incomplete-append failure mode. The trigger for the observed truncation '
    text+='is not recoverable from the saved traceback; the original exception was masked by another accounting read. '
    text+='A new receipt ledger is software-qualified separately, leaving the stopped study unchanged.\n'
    (HERE/'README.md').write_text(text)
    write(HERE/'evidence-receipt.json',dict(artifacts={n:audit.sha(HERE/n) for n in ('manifest.json','summary.json','completion.json','README.md')},
        observed_starts=0,native_predictions=0,original_journals_unchanged=True))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--render-only',action='store_true');args=parser.parse_args()
    OUTPUT.mkdir(exist_ok=True)
    with (OUTPUT/'worker.lock').open('a+') as own,(PARENT/'worker.lock').open('a+') as parent:
        fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(parent,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (OUTPUT/'completion.json').exists():
            c=json.loads((OUTPUT/'completion.json').read_text())
            if c['manifest_sha256']!=audit.sha(OUTPUT/'manifest.json') or c['summary_sha256']!=audit.sha(OUTPUT/'summary.json'):raise ValueError('completed audit mismatch')
            render(json.loads((OUTPUT/'summary.json').read_text()));return
        if args.render_only or (OUTPUT/'start.json').exists():raise ValueError('charged audit cannot restart')
        sources={str(p):audit.sha(p) for p in (Path(__file__),Path(audit.__file__),ROOT/'analysis/lll/ilvis0_receipt_journal.py')}
        inputs={str(HERE/'PLAN.md'):audit.sha(HERE/'PLAN.md')}
        failure=json.loads((PARENT/'failure.json').read_text())
        for name in (*failure['artifacts'],'failure.json'):inputs[str(PARENT/name)]=audit.sha(PARENT/name)
        write(OUTPUT/'manifest.json',dict(sources=sources,inputs=inputs,maximum_batches=1,observed_starts=0,native_predictions=0))
        write(OUTPUT/'start.json',dict(manifest_sha256=audit.sha(OUTPUT/'manifest.json')))
        summary=audit.inspect(PARENT)
        for name,h in summary['saved_artifacts'].items():inputs[str(PARENT/name)]=h
        write(OUTPUT/'summary.json',summary)
        write(OUTPUT/'completion.json',dict(state='complete',manifest_sha256=audit.sha(OUTPUT/'manifest.json'),summary_sha256=audit.sha(OUTPUT/'summary.json')))
        render(summary);print(json.dumps({k:summary[k] for k in ('charged_starts','verified_saved_results','maximum_remaining_native_evaluations','controls_passed')}))


if __name__=='__main__':main()
