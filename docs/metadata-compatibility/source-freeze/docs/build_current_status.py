# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish one status snapshot from sealed metadata; no originals or numerical work."""
import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.studies.readers import read as evidence_read
FINDINGS='docs/ilvis0-current-findings-20261015'
START='<!-- current-status:start -->'
END='<!-- current-status:end -->'
PAGES=('README.md','docs/ILVIS0.md','docs/ANALYSIS_ROADMAP.md')


def sha_bytes(data): return hashlib.sha256(data).hexdigest()


def sha(path):
    path=Path(path)
    if not path.is_file() and path.is_relative_to(ROOT):
        return sha_bytes(evidence_read(ROOT,str(path.relative_to(ROOT))))
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
    return digest.hexdigest()


def public_path(root,name):
    path=Path(name)
    if path.is_absolute() or '..' in path.parts: raise ValueError('invalid evidence path')
    # Published copies make checks reproducible in a clean public checkout.
    if path.parts[:1]==('data',): path=Path('docs',*path.parts[1:])
    result=root/path
    if not result.resolve().is_relative_to(root.resolve()): raise ValueError('invalid evidence path')
    return result


def verify_inputs(root,inputs):
    for name,digest in inputs.items():
        path=public_path(root,name)
        try:actual=sha(path)
        except FileNotFoundError as error:
            raise ValueError('missing evidence: '+name) from error
        if actual!=digest: raise ValueError('evidence hash mismatch: '+name)


def summarize(rows):
    tally=dict(globe=0,flat=0,unresolved=0,ambiguous=0);seen=set();background=0;seconds=0.
    for row in rows:
        sid=row['segment_id'];shape=row['shape_preference'];flag=row['specified_background_preferred']
        if sid in seen or shape not in tally or flag not in ('True','False'):
            raise ValueError('invalid or duplicate stretch disposition')
        if flag=='True' and shape!='globe': raise ValueError('background comparison requires globe')
        seen.add(sid);tally[shape]+=1;background+=flag=='True';seconds+=float(row['duration_s'])
    return dict(tally=tally,total=len(seen),background=background,minutes=seconds/60,
                imu_types=sorted({r['imu_type'] for r in rows}))


def load_snapshot(root,findings=FINDINGS):
    directory=root/findings
    receipt=json.loads((directory/'findings-receipt.json').read_text())
    verify_inputs(root,receipt['inputs']);verify_inputs(root,receipt['sources'])
    verify_inputs(root,{findings+'/'+name:digest for name,digest in receipt['artifacts'].items()})
    if 'publication_builder' in receipt:
        path=public_path(root,receipt['publication_builder'])
        spec=importlib.util.spec_from_file_location('current_publication',path)
        publication=importlib.util.module_from_spec(spec);spec.loader.exec_module(publication)
        expected=publication.verified_rows(root)
        with (directory/'current-stretches.csv').open(newline='') as stream: rows=list(csv.DictReader(stream))
        if rows!=expected: raise ValueError('current inventory differs from sealed result ledgers')
        snapshot=summarize(rows)
        if snapshot['tally']!=receipt['tally']: raise ValueError('current tally differs from sealed results')
        snapshot['receipt_sha256']=sha(directory/'findings-receipt.json')
        return snapshot
    path=directory/'build_findings.py'
    spec=importlib.util.spec_from_file_location('sealed_findings',path)
    report=importlib.util.module_from_spec(spec);spec.loader.exec_module(report)
    baseline=json.loads(gzip.decompress((root/'docs/ilvis0-highspeed-segments-20261008/summary.json.gz').read_bytes()))
    records={row['segment_id']:row for row in baseline['results']}
    if len(records)!=len(baseline['results']): raise ValueError('duplicate baseline stretch')
    recovery=root/'docs/ilvis0-position-recovery-20261013'
    updates=report.recovery_updates(baseline,json.loads((recovery/'summary.json').read_text()))
    for name,qualify in (
        ('ilvis0-paired-precision-trial-20261014',report.precision_updates),
        ('ilvis0-cost-precision-recovery-20261014',report.cost_precision_updates),
    ):
        trial=root/'docs'/name
        summary,manifest=report.sealed_precision(trial)
        updates.update(qualify(updates,summary,manifest['plan']['target_segment_ids']))
    records.update(updates)
    with (directory/'current-stretches.csv').open(newline='') as stream: rows=list(csv.DictReader(stream))
    snapshot=summarize(rows)
    if {r['segment_id'] for r in rows}!=set(records) or snapshot['tally']!=receipt['tally']:
        raise ValueError('inventory differs from sealed results')
    for row in rows:
        profile=records[row['segment_id']]['profile'];shape=profile['conditional_shape_preference']
        rotation=profile['rotation_diagnostics']
        field=bool(shape=='globe' and rotation and all(r['conditional_still_minus_rotating_cost']>0 for r in rotation))
        if (row['shape_preference'],row['specified_background_preferred'])!=(shape,str(field)):
            raise ValueError('inventory disposition differs from result ledger')
    snapshot['receipt_sha256']=sha(directory/'findings-receipt.json')
    return snapshot


def headline(snapshot):
    tally=snapshot['tally']
    return (f"**{tally['globe']} globe preferences, {tally['flat']} flat preferences, "
            f"{tally['unresolved']} unresolved** among {snapshot['total']} preselected stretches.")


def status_block(snapshot,prefix):
    coverage=('All selected comparisons have passed their required numerical checks.'
              if snapshot['tally']['unresolved']==0 and snapshot['tally']['ambiguous']==0
              else 'Unfinished comparisons are not evidence for either shape.')
    return (START+'\n'+headline(snapshot)+'\n'
            f"See the [verified current status]({prefix}CURRENT_STATUS.md) for coverage, background-field comparisons "
            'and the supporting result records. '+coverage+'\n'+END)


def replace_block(text,block):
    if text.count(START)!=1 or text.count(END)!=1 or text.index(START)>text.index(END):
        raise ValueError('expected one pair of current-status markers')
    a=text.index(START);b=text.index(END)+len(END)
    return text[:a]+block+text[b:]


def render(snapshot):
    tally=snapshot['tally'];prefix=FINDINGS.removeprefix('docs/')+'/'
    text='# Current airborne analysis status\n\n'
    text+=headline(snapshot)+'\n\n'
    text+=f"The selected stretches total **{snapshot['minutes']:.1f} minutes**. "
    text+='The same preselected intervals and original measurements are retained through numerical recovery.\n\n'
    text+='| Current disposition | Stretches |\n|---|---:|\n'
    for name,label in [('globe','Globe preferred'),('flat','Specified flat disc preferred'),
                       ('unresolved','Unresolved'),('ambiguous','Different preferences across assumptions')]:
        text+=f'| {label} | {tally[name]} |\n'
    text+=f"\nOf the globe-preferred stretches, **{snapshot['background']}** also favor the specified background "
    text+='rotation field over zero field under both processing assumptions. That comparison does not '
    text+="identify the field's physical cause or distinguish a solar from a sidereal day.\n\n"
    text+='These are numerical model preferences; statistical significance is not yet calibrated. '
    text+='Overlapping recordings and shared instruments mean stretches cannot be counted as independent replications. '
    text+='An unresolved comparison has not passed its required calculations and checks; it supplies no opposing shape finding.\n\n'
    text+=f'[Findings and source tracks]({prefix}FINDINGS.md) · [All selected stretches]({prefix}STRETCHES.md) '
    text+=f'· [Comprehensive metadata]({prefix}ANALYTICS.md) · [Next steps](NEXT_STEPS.md)\n\n'
    text+='## Evidence and history\n\n'
    text+='This snapshot is generated from published, hash-verified result ledgers and their '
    text+='qualified per-stretch comparisons. It excludes active workers and incomplete publications. '
    text+='The original [first-pass report](ilvis0-highspeed-segments-20261008/FINDINGS.md) '
    text+='and preserved trial reports describe their own historical stages; their earlier totals remain unchanged.\n\n'
    text+='Snapshot receipt SHA-256: `'+snapshot['receipt_sha256']+'`.\n\n'
    text+='Reproduce with `~/venv/bin/python docs/build_current_status.py`; '
    text+='`--check` verifies the evidence and checks this page and the landing-page excerpts without writing. '
    text+='Only published metadata is read; no original IMU files, model refits or numerical predictions are needed.\n'
    return text


def generate(root=ROOT,check=False):
    snapshot=load_snapshot(root)
    outputs={root/'docs/CURRENT_STATUS.md':render(snapshot)}
    for name in PAGES:
        path=root/name;prefix='docs/' if name=='README.md' else ''
        outputs[path]=replace_block(path.read_text(),status_block(snapshot,prefix))
    stale=[str(path.relative_to(root)) for path,text in outputs.items() if not path.exists() or path.read_text()!=text]
    if not check:
        for path,text in outputs.items():
            if str(path.relative_to(root)) in stale:
                temporary=path.with_suffix(path.suffix+'.tmp');temporary.write_text(text);temporary.replace(path)
    return stale


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    try: stale=generate(check=args.check)
    except (ValueError,OSError,KeyError) as error: parser.exit(1,str(error)+'\n')
    if args.check and stale: parser.exit(1,'Stale status pages: '+', '.join(stale)+'; run docs/build_current_status.py\n')
    print('Verified current status; '+('all pages match.' if args.check else f'updated {len(stale)} pages.'))


if __name__=='__main__': main()
