# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate generated-only diagnosis of inherited native roundoff."""
import argparse
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll.compute_budget import environment
if __name__=='__main__' and any(os.environ.get(k)!=v for k,v in environment(threads=4).items()):
    raise SystemExit('use run_numerical.py with four threads')

import ilvis0_streaming_worker as base
from lll import ilvis0_stream_precision as controls

NAME='ilvis0-streaming-precision-20261019';DATA=ROOT/'data'/NAME;PUBLIC=ROOT/'docs/ilvis0-streaming-precision'
TASKS=controls.tasks()
LIMITS=dict(base.LIMITS,maximum_identities=6,maximum_native_evaluations=4500,
    maximum_packet_visits=4000000,maximum_wall_s=300)
SOURCE_NAMES=base.SOURCE_NAMES+['analysis/lll/ilvis0_stream_precision.py',
    'analysis/tests/ilvis0_stream_precision_worker.py','analysis/tests/test_ilvis0_stream_precision.py',
    'analysis/tests/test_ilvis0_stream_precision_worker.py','docs/ilvis0-streaming-precision/PLAN.md']


def configure():
    base.NAME=NAME;base.DATA=DATA;base.PUBLIC=PUBLIC;base.TASKS=TASKS;base.LIMITS=LIMITS
    base.SOURCE_NAMES=SOURCE_NAMES;base.controls=controls;base.publish=publish


def publish():
    manifest=base.verify();summary=base.load(DATA/'summary.json');PUBLIC.mkdir(parents=True,exist_ok=True)
    names=['manifest.json','authorization.json','start.json','summary.json','completion.json']
    names += [r['artifact'] for r in summary['results']]
    names += ['source-freeze/'+n for n in manifest['sources']]
    names += ['starts/'+t['identity']+'.json' for t in manifest['tasks'][:summary['charged']['identities']]]
    names += [f'charges/call-{i:05d}.json' for i in range(1,summary['charged']['native_calls']+1)]
    for name in names:
        target=PUBLIC/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    shutil.copyfile(DATA/'source-freeze/docs/ilvis0-streaming-precision/PLAN.md',PUBLIC/'PLAN.md')
    rows=[base.load(DATA/r['artifact']) for r in summary['results']]
    lines=['# Long-record streaming and native arithmetic','',
        f"{sum(r['passed'] for r in summary['results'])}/{len(manifest['tasks'])} controls pass; state: {summary['state']}.",'',
        'The reference controls compare the unchanged whole-array kernels with chunked predictions. '
        'Exact-pose errors remain separate from agreement between the calculations.','',
        '| Case | Mode | Packets | Streaming − reference / exact target | Streaming exact-pose error | Reference exact-pose error |','|---|---|---:|---:|---:|---:|']
    for row in rows:
        if 'maximum_position_difference_m' in row:
            lines.append(f"| {row['kind']} | {'27-column tangent' if row['input']['tangent'] else 'Value'} | {row['packet_count']:,} | "
                f"{row['maximum_position_difference_m']:.8g} m | {row['maximum_exact_pose_error_m']:.8g} m | {row['reference_exact_pose_error_m']:.8g} m |")
    lines+=['','The exact-pose controls use zero angular increments and exactly representable periods/gravity. '
        'The reference cases retain the earlier nominal-300-Hz specified-field input. The first study’s '
        'absolute-pose failure is preserved and is not relabeled by a successful equivalence comparison.','',
        '| Case | Mode | Runtime, streamed | Traced working peak | Native state |','|---|---|---:|---:|---:|']
    for row in rows:
        if 'runtime_s' in row:
            lines.append(f"| {row['kind']} | {'27-column tangent' if row['input']['tangent'] else 'Value'} | {row['runtime_s']:.2f} s | {row['peak_traced_bytes']/1024**2:.3f} MiB | {row['state_bytes']:,} bytes |")
    lines+=['','Reference arrays/compiler/shared-library storage are outside the traced streamed working allocation. '
        'Predicted observations and derivatives are compared and discarded one block at a time. '
        'These generated controls do not establish observational accuracy, global rounding bounds or calibrated uncertainty.','',
        f"Charged {summary['charged']['native_calls']:,} calls and {summary['charged']['packet_visits']:,} packet visits in {summary['elapsed_s']:.2f} seconds; zero archive fits.",'',
        '[Frozen plan](PLAN.md) · [First qualification and retained failure](../ilvis0-streaming-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).']
    (PUBLIC/'README.md').write_text('\n'.join(lines)+'\n')
    base.write(PUBLIC/'evidence-receipt.json',dict(artifacts={n:base.sha(PUBLIC/n) for n in names+['PLAN.md','README.md']}),replace=True)


def main():
    configure();parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for name in ('prepare','run','package-only','check'):group.add_argument('--'+name,action='store_true')
    args=parser.parse_args()
    if args.prepare:base.prepare();print('Frozen six independent generated precision controls.')
    elif args.run:base.run();print('Separate streaming precision controls finished.')
    elif args.package_only:publish();print('Published saved results; no evaluations.')
    else:base.verify();print('Verified separate streaming precision freeze/results.')


if __name__=='__main__':main()
