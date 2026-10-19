# SPDX-License-Identifier: AGPL-3.0-or-later
"""Publish deterministic provenance groups from explicit saved metadata only."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from lll.evidence_groups import build

HERE=Path(__file__).resolve().parent
FINDINGS=ROOT/'docs/ilvis0-current-findings-20261015'
ESA=ROOT/'docs/external-imu-data'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def rows(path):
    with path.open(newline='') as stream:return list(csv.DictReader(stream))


def outputs():
    names=['stretch-analytics.csv','shared-leg-pairs.csv']
    receipt=json.loads((FINDINGS/'findings-receipt.json').read_text())
    for name in names:
        if sha(FINDINGS/name)!=receipt['artifacts'][name]:raise ValueError('changed findings artifact: '+name)
    policy_path=ESA/'ESA_CONFIRMATION_POLICY.json';policy=json.loads(policy_path.read_text())
    ledger=build(rows(FINDINGS/names[0]),rows(FINDINGS/names[1]),rows(ESA/'esa-live-imu-files.csv'),policy)
    files=[FINDINGS/name for name in names]+[FINDINGS/'findings-receipt.json',
        ESA/'esa-live-imu-files.csv',policy_path,Path(__file__),ROOT/'analysis/lll/evidence_groups.py']
    ledger['inputs']={str(path.relative_to(ROOT)):sha(path) for path in files}
    result={'ledger.json':encoded(ledger)}
    fields=['record_id','archive','filename','source_sha256','start_utc','end_utc','date',
        'imu_type','mounting_configuration','shared_leg_id','group_id','role',
        'physical_instrument_id','installation_id','reported_flight_labels']
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    writer.writeheader()
    for row in ledger['records']:
        value={key:row.get(key,'') for key in fields};value['reported_flight_labels']=';'.join(value['reported_flight_labels'])
        writer.writerow(value)
    result['recording-groups.csv']=stream.getvalue().encode()
    stream=io.StringIO(newline='');fields=['group_id','archive','role','record_ids','utc_dates','reported_flight_labels','identity_status']
    writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader()
    for group in ledger['groups']:
        writer.writerow({key:';'.join(value) if isinstance(value,list) else value for key,value in group.items()})
    result['groups.csv']=stream.getvalue().encode()
    nasa=[g for g in ledger['groups'] if g['archive']=='ilvis0'];esa=[g for g in ledger['groups'] if g['archive']=='esa']
    protected=[g for g in esa if g['role']=='protected_confirmation']
    text=['# Shared observations and protected confirmation data','',
        f"The 53 selected archive stretches form **{len(nasa)} conservative split groups**. These groups keep same-date observations, byte aliases, overlapping intervals and candidate shared legs together. They are not {len(nasa)} verified independent flights or installations.",'',
        f"The nine cataloged ESA files form **{len(esa)} conservative date/file groups**: one development group (recording 187) and **{len(protected)} protected confirmation groups**. Reported flight labels sharing a file stay together. Model outcomes from protected groups remain unexamined.",'',
        '[Every recording/stretch](recording-groups.csv) · [Every split group](groups.csv) · [Complete relationship graph](ledger.json) · [Execution roadmap](../ANALYSIS_ROADMAP.md).','',
        '## What is known and what is grouped conservatively','',
        'Source hashes identify byte aliases; UTC intervals identify temporal overlap. Saved shared-leg matches remain candidate same-track relationships. Same-date grouping is a deliberate protection against leakage, not proof of one aircraft. Physical instrument and installation identities remain unknown; matching configuration bytes do not fill those fields. Separate dates may still share hardware and systematic errors.','',
        'Different groups are therefore units for conservative development splits, not a measured number of independent replications. Later evidence may merge groups; any split-policy change needs a new version before evaluation.','',
        '## ESA reservation','',
        'Use recording 187 for development. The other eight currently cataloged files are protected confirmation material. Integrity, inventory and receiver-only eligibility checks are allowed. Model fitting and model-outcome inspection wait until selection, method, uncertainty, adequacy rules and confirmation identities are frozen. A new or unassigned file is not development data by default.','',
        'The metadata helper rejects development/confirmation membership in a shared group and exposes a development-only guard for future workers. No model worker is launched by this ledger; confirmation authorization must be implemented and checked in its separately frozen worker.','',
        'The original 53 intervals, measurements and dispositions are unchanged. The NASA corpus has already informed method development; new blocked predictions are retrospective validation rather than untouched confirmation.','',
        '## Reproducibility','',
        'Run `~/venv/bin/python docs/analysis-provenance/build_ledger.py` to regenerate, or append `--check` for a read-only consistency check. The builder reads only named saved metadata, verifies the source findings hashes, and performs no original-file reads, integrations, fits or network requests. Input and output hashes are recorded in the receipt.','',
        '[ESA source inventory](../external-imu-data/README.md) · [Findings](../CURRENT_STATUS.md).']
    result['README.md']=('\n'.join(text)+'\n').encode()
    result['provenance-receipt.json']=encoded(dict(inputs=ledger['inputs'],artifacts={name:hashlib.sha256(value).hexdigest()
        for name,value in result.items()},observed_starts=0,native_predictions=0,original_files_read=0))
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    result=outputs()
    if args.check:
        bad=[name for name,value in result.items() if not (HERE/name).exists() or (HERE/name).read_bytes()!=value]
        if bad:raise ValueError('provenance publication differs: '+', '.join(bad))
        print('Verified provenance groups, reservation policy and publication hashes.')
    else:
        for name,value in result.items():(HERE/name).write_bytes(value)
        ledger=json.loads(result['ledger.json'])
        print(f"Published {len(ledger['records'])} records in {len(ledger['groups'])} conservative groups; zero original reads or fits.")


if __name__=='__main__':main()
