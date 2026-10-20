# SPDX-License-Identifier: AGPL-3.0-or-later
"""Build/check an immutable development evidence snapshot; no science evaluation."""
import argparse
import csv
import fcntl
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import ilvis0_evidence_dataset as dataset

HERE=ROOT/'docs/paper-development-dataset-v1';DATA=ROOT/'data/paper-development-dataset-v1'
FINDINGS=ROOT/'docs/ilvis0-current-findings-20261015';BASE=ROOT/'docs/ilvis0-highspeed-segments-20261008'
GROUPS=ROOT/'docs/analysis-provenance';GYRO=ROOT/'docs/ilvis0-gyro-companion-v2'
VERSION='paper-development-evidence-v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False,ensure_ascii=False)+'\n').encode()
def rows(path):
    with Path(path).open(newline='') as stream:return list(csv.DictReader(stream))


def freeze(root,destination,inputs,sources,outputs,summary):
    root=Path(root);destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    with (destination/'snapshot.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (destination/'manifest.json').exists():raise ValueError('immutable snapshot already exists; check or use a new version')
        dataset.verify_artifacts(root,inputs);dataset.verify_artifacts(root,sources)
        for prefix,names in (('frozen-inputs',inputs),('source-freeze',sources)):
            for name in names:
                target=destination/prefix/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,target)
        outputs=dict(outputs);outputs['dataset-summary.json']=encoded(summary)
        for name,data in outputs.items():
            target=destination/name
            if Path(name).is_absolute() or not target.resolve().is_relative_to(destination.resolve()):raise ValueError('unsafe snapshot output path')
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        artifacts={name:sha(destination/name) for name in outputs}
        manifest=dict(version=VERSION,inputs=inputs,sources=sources,artifacts=artifacts,summary=summary,
            metadata_python=sys.version,original_reads=0,model_evaluations=0,optimizer_starts=0)
        (destination/'manifest.json').write_bytes(encoded(manifest))
        (destination/'evidence-receipt.json').write_bytes(encoded(dict(manifest_sha256=sha(destination/'manifest.json'),artifacts=artifacts)))
    check(destination)


def check(destination,*,live_root=None):
    destination=Path(destination)
    if not (destination/'manifest.json').exists():raise ValueError('no completed evidence snapshot')
    manifest=load(destination/'manifest.json');receipt=load(destination/'evidence-receipt.json')
    if sha(destination/'manifest.json')!=receipt['manifest_sha256'] or receipt['artifacts']!=manifest['artifacts']:
        raise ValueError('evidence snapshot manifest changed')
    dataset.verify_artifacts(destination,manifest['artifacts'])
    dataset.verify_artifacts(destination/'frozen-inputs',manifest['inputs'])
    dataset.verify_artifacts(destination/'source-freeze',manifest['sources'])
    if load(destination/'dataset-summary.json')!=manifest['summary']:raise ValueError('snapshot summary disagrees with its manifest')
    if live_root is not None:dataset.verify_artifacts(live_root,manifest['inputs'])
    return manifest


def collect():
    inputs={};index=[]
    def remember(path,role):
        name=str(path.relative_to(ROOT));digest=sha(path);inputs[name]=digest
        index.append(dict(source_path=name,sha256=digest,role=role))
    def receipt(directory,name,artifacts,role):
        path=directory/name;r=load(path);dataset.verify_artifacts(directory,{n:r['artifacts'][n] for n in artifacts})
        remember(path,role+' receipt')
        for artifact in artifacts:remember(directory/artifact,role)
    receipt(FINDINGS,'findings-receipt.json',('current-stretches.csv','stretch-analytics.csv','fit-analytics.csv','shared-leg-pairs.csv'),
        'selected-stretch numerical findings and history')
    current_receipt=load(FINDINGS/'findings-receipt.json')
    dataset.verify_artifacts(ROOT,current_receipt['inputs'])
    receipt(BASE,'evidence-receipt.json',('eligible-stretches.csv','files.csv','ELIGIBILITY.md'),'frozen eligibility in the retained 232-file pool')
    receipt(GROUPS,'provenance-receipt.json',('recording-groups.csv','groups.csv','ledger.json'),'conservative grouping and ESA reservation metadata')
    receipt(GYRO,'evidence-receipt.json',('baseline-comparisons.csv','scenario-comparisons.csv.gz','manifest.json','summary.json','completion.json'),
        'descriptive raw-gyro geographic comparison')
    studies=[
        ('ilvis0-channel-envelopes-20261019','C03','observed reduced-channel diagnostic'),
        ('ilvis0-channel-history-v2-20261019','C04','observed reduced-channel diagnostic'),
        ('ilvis0-prediction-covariance-20261012','V01','earlier incomplete observed development prediction'),
        ('ilvis0-bounded-prediction-controls','V01','generated software coverage controls'),
        ('ilvis0-recording-scale-bounds','V01','generated recording-scale bounds; finite study incomplete and bounds too wide'),
        ('ilvis0-shared-reference-scale','V01','generated shared-scale controls; observational covariance unqualified'),
        ('esa-development-selection','E01','development-only receiver selection; no qualifying intervals'),
        ('esa-motion-diagnostic','E01','development-only receiver motion diagnostic'),
        ('ilvis0-gyro-companion','G01','superseded software serialization failure; zero observed comparisons'),
        ('ilvis0-gyro-companion-v2','G01','completed descriptive observed comparison; no fitted correction')]
    study_rows=[]
    for directory,task,scope in studies:
        location=ROOT/'docs'/directory
        for name in ('manifest.json','summary.json','completion.json'):remember(location/name,scope)
        completion=load(location/'completion.json');summary=load(location/'summary.json')
        if completion['manifest_sha256']!=sha(location/'manifest.json') or completion['summary_sha256']!=sha(location/'summary.json'):
            raise ValueError('study completion/source hashes disagree: '+directory)
        study_rows.append(dict(task_id=task,study=directory,scope=scope,execution_state=completion.get('state','complete'),
            reported_passed=summary.get('passed',''),terminal_reason=summary.get('terminal_reason',''),
            calibrated_aircraft_coverage=False,independent_replication_established=False,summary_path=str((location/'summary.json').relative_to(ROOT))))
    assembled=dataset.assemble(current=rows(FINDINGS/'stretch-analytics.csv'),groups=rows(GROUPS/'recording-groups.csv'),
        eligible=rows(BASE/'eligible-stretches.csv'),gyro=rows(GYRO/'baseline-comparisons.csv'),history=rows(FINDINGS/'fit-analytics.csv'),files=rows(BASE/'files.csv'))
    if assembled['summary']['stretches']!=53 or assembled['summary']['latest_primary_comparisons']!=318 or assembled['summary']['conservative_split_groups']!=27:
        raise ValueError('unexpected frozen selected population')
    if assembled['summary']['preferences']!=dict(globe=53,flat=0,unresolved=0,ambiguous=0):
        raise ValueError('baseline version requires its original verified numerical dispositions')
    if {r['segment_id'] for r in rows(FINDINGS/'current-stretches.csv')}!={r['segment_id'] for r in assembled['stretches']}:
        raise ValueError('current disposition and analytic populations disagree')
    gates=[dict(gate_id=key,status=status,scope=scope) for key,status,scope in (
        ('latest_numerical_comparisons','complete','53 stretches; all six latest primary fits per stretch pass'),
        ('gyro_geographic_companion','descriptive_complete','level/course assumptions; 243 finite scenarios; no new fitted corrections'),
        ('shared_scale_software','qualified_under_declared_assumptions','generated Gaussian-family controls; not aircraft error calibration'),
        ('recording_scale_prediction_bounds','not_useful_and_matrix_incomplete','wide mathematical bounds; three complete histories and one partial'),
        ('observational_covariance','not_qualified','shared receiver error shape and selection need assessment'),
        ('withheld_prediction_adequacy','not_qualified','earlier development outputs are retained separately'),
        ('independent_flight_count','not_established','27 conservative groups are not verified independent flights'),
        ('independent_ESA_confirmation','reserved_not_evaluated','protected groups contain no inspected model outcomes'),
        ('calibrated_two_stage_decision','not_established','no significance level or production evidence promotion'),
        ('final_paper_dataset','development_only','withheld adequacy, confirmation and dependence-aware uncertainty remain'))]
    return assembled,inputs,index,study_rows,gates


def build():
    if (DATA/'manifest.json').exists():raise ValueError('immutable version already exists; use --check or --publish')
    assembled,inputs,index,studies,gates=collect();summary=assembled['summary']
    summary.update(gyro_baseline_rows=len(assembled['gyro_baselines']),indexed_diagnostic_studies=len(studies),
        acquisition_census_complete=False,fit_origin_environment_index_complete=False)
    outputs={}
    for name,key in (('stretches.csv','stretches'),('latest-primary-comparisons.csv','primary_comparisons'),
            ('recording-groups.csv','groups'),('retained-file-eligibility.csv','files'),('gyro-baselines.csv','gyro_baselines')):
        outputs[name]=dataset.encode_csv(assembled[key])
    outputs['numerical-history.csv.gz']=gzip.compress(dataset.encode_csv(assembled['numerical_history']),mtime=0)
    outputs['source-index.csv']=dataset.encode_csv(index);outputs['diagnostic-studies.csv']=dataset.encode_csv(studies)
    outputs['validation-gates.csv']=dataset.encode_csv(gates);outputs['ELIGIBILITY.md']=(BASE/'ELIGIBILITY.md').read_bytes()
    text=f'''# Development evidence dataset

**{summary['stretches']} selected stretches, {summary['latest_primary_comparisons']} latest primary comparisons,
{summary['numerical_history_records']} preserved numerical-history records, and {summary['conservative_split_groups']} conservative split groups.**
The current numerical preference is 53 globe, zero flat and zero unresolved.
This snapshot does not report calibrated detections or a verified independent-flight count.

| Table | Contents |
|---|---|
| [Stretches](stretches.csv) | Source hashes, UTC bounds, selection, geometry, latest outcomes, gyro companion and validation fields. |
| [Latest primary comparisons](latest-primary-comparisons.csv) | All three models under both processing cases; kept separate from repeats and failures. |
| [Numerical history](numerical-history.csv.gz) | Every published history row, including {summary['history_rows_not_marked_converged']} rows not marked converged. Some rows are diagnostics, not optimizer starts. |
| [Recording groups](recording-groups.csv) | Shared observations and unknown physical instrument/installation identities. |
| [Retained-file eligibility](retained-file-eligibility.csv) | All {summary['retained_file_eligibility_rows']} files screened for this selected study, including nonqualifying files and aliases. |
| [Gyro baselines](gyro-baselines.csv) | The same observations beside three precomputed level/course predictions. |
| [Diagnostic studies](diagnostic-studies.csv) | Completed, failed and incomplete method studies, with their distinct scopes. |
| [Validation gates](validation-gates.csv) | Numerical completion, uncertainty, prediction and confirmation kept separate. |
| [Source index](source-index.csv) | Named input artifacts and SHA-256 hashes. |

## Scope and remaining work

An **IMU (inertial measurement unit)** records turning and specific force. Recorded
gyro increments are the turning observations; receiver positions locate the route.
The descriptive companion uses no fitted gyro correction or fused-attitude subtraction.

Original measurements, interval choices, failed results and blank hardware identities
are preserved. A history row ID identifies its place in this snapshot; it is not an
invented original worker identity. Repeated fits and overlapping recorders are not
independent replications. Source coordinate, calibration and processing assumptions
remain documented with their studies.

This is **development version 1**, not the final paper dataset. It covers the
53-stretch study and its retained-file selection, not a new 326-file acquisition
census. A complete acquisition-flow index and per-origin environment mapping remain
to be assembled. Earlier prediction outputs are indexed, not represented as qualified
held-out validation. Protected ESA records contribute reservation metadata only.
Withheld predictive adequacy, observational error assessment, independent confirmation
and calibrated dependence-aware decisions remain open.

The copied inputs, builder sources and outputs are immutable under this version.
The checker verifies frozen copies; an optional live-input check reports later
project changes without altering this snapshot. Building performs zero original
reads, model evaluations, optimizer starts or network requests.

`~/venv/bin/python docs/paper-development-dataset-v1/build_dataset.py --check`
checks the runtime and published snapshots. `--check-live` also checks the current
named project inputs. `--publish` only copies an already verified snapshot; it does
not rebuild tables or trigger analysis. A changed evidence set needs a new version.

[Selection criteria](ELIGIBILITY.md) · [Frozen assembly plan](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
'''
    outputs['README.md']=text.encode();outputs['PLAN.md']=(HERE/'PLAN.md').read_bytes()
    names=['analysis/lll/ilvis0_evidence_dataset.py','analysis/tests/test_ilvis0_evidence_dataset.py',
        'analysis/tests/test_paper_development_dataset.py','docs/paper-development-dataset-v1/build_dataset.py','docs/paper-development-dataset-v1/PLAN.md']
    freeze(ROOT,DATA,inputs,{name:sha(ROOT/name) for name in names},outputs,summary);publish()


def publish():
    manifest=check(DATA)
    names=['manifest.json','evidence-receipt.json',*manifest['artifacts']]
    names+=['frozen-inputs/'+name for name in manifest['inputs']]
    names+=['source-freeze/'+name for name in manifest['sources']]
    for name in names:
        target=HERE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(DATA/name,target)
    check(HERE)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for flag in ('build','check','check-live','publish'):group.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if args.build:build();print('Built and verified immutable development evidence snapshot; no model evaluations.')
    elif args.publish:publish();print('Published verified frozen copies; no table regeneration or analysis.')
    else:
        for location in (DATA,HERE):check(location,live_root=ROOT if args.check_live else None)
        print('Verified runtime and public development snapshots'+(' and current named inputs.' if args.check_live else '.'))


if __name__=='__main__':main()
