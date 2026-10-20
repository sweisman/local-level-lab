# SPDX-License-Identifier: AGPL-3.0-or-later
"""Extend the sealed development snapshot with catalog and operation lineage."""
import argparse
import collections
import csv
import gzip
import io
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'analysis'))
from lll import evidence_snapshot as snapshot,ilvis0_evidence_dataset as dataset
from lll import ilvis0_evidence_lineage as lineage,ilvis0_lineage_sources as sources

HERE=ROOT/'docs/paper-development-dataset-v2';DATA=ROOT/'data/paper-development-dataset-v2';BASE='docs/paper-development-dataset-v1'
ALIASES={
    'original_first_pass':('original','docs/ilvis0-highspeed-segments-20261008',None),
    'qualified_subset':('trial','docs/ilvis0-position-stability-trial-20261013',None),
    'completed_wider_recovery':('trial','docs/ilvis0-position-recovery-20261013',None),
    'qualified_paired_precision':('trial','docs/ilvis0-paired-precision-trial-20261014',None),
    'completed_cost_precision':('trial','docs/ilvis0-cost-precision-recovery-20261014',None)}
for name in ('ilvis0-budget-continuation-20261014','ilvis0-remaining-precision-20261014','ilvis0-trust-trial-20261015',
        'ilvis0-hybrid-remaining-20261015','ilvis0-timing-trial-20261016'):
    ALIASES['completed_'+name]=('trial','docs/'+name,None)
for name in ('ilvis0-boundary-review-20261016','ilvis0-neighbor-review-20261017','ilvis0-cluster-review-20261018',
        'ilvis0-representable-review-20261018','ilvis0-scaled-pair-review-20261018','ilvis0-last-review-20261018'):
    ALIASES['completed_'+name]=('review','docs/'+name,None)


def csv_data(reader,name,expected=None):
    data=reader.named(name,expected)
    if name.endswith('.gz'):data=gzip.decompress(data)
    return list(csv.DictReader(io.StringIO(data.decode())))


def json_lines(reader,name):return [json.loads(row) for row in reader.named(name).decode().splitlines() if row.strip()]


def collect():
    previous=snapshot.check(ROOT/BASE);reader=sources.Reader(ROOT);inherited={}
    for name in ('manifest.json','evidence-receipt.json'):reader.json(BASE+'/'+name)
    for name in ('stretches.csv','latest-primary-comparisons.csv','numerical-history.csv.gz','recording-groups.csv','retained-file-eligibility.csv',
            'gyro-baselines.csv','diagnostic-studies.csv','validation-gates.csv','ELIGIBILITY.md'):
        inherited[name]=reader.named(BASE+'/'+name,previous['artifacts'][name])
    current=csv_data(reader,BASE+'/stretches.csv');retained=csv_data(reader,BASE+'/retained-file-eligibility.csv')
    history=csv_data(reader,BASE+'/numerical-history.csv.gz')
    initial_report=reader.json('docs/ilvis0-physical-validation-20261007/corpus-screening.json')
    inventory=reader.json('data/ilvis0-ready/inventory.json',initial_report['provenance_sha256']['inventory.json'])
    acquisition=reader.json('data/ilvis0-ready/manifest.json',initial_report['provenance_sha256']['manifest.json'])
    catalog=reader.json('docs/ilvis0-physical-validation-20261007/catalog/catalog.json',acquisition['catalog_sha256'])
    if catalog['count']!=len(catalog['files']) or inventory['catalog_count']!=len(inventory['files']):
        raise ValueError('declared catalog/inventory counts disagree with their records')
    followup=json_lines(reader,'data/ilvis0-followup-20261007/cleanup.jsonl')
    clean=reader.json('docs/ilvis0-followup-20261007/cleanup-completion.json')
    if reader.inputs['data/ilvis0-followup-20261007/cleanup.jsonl']!=clean['disposition_journal_sha256']:
        raise ValueError('later no-level cleanup journal changed')
    duplicates=json_lines(reader,'data/ilvis0-retention-84-20261007/cleanup.jsonl')
    final_storage=reader.json('docs/ilvis0-retention-84-20261007/completion.json')
    removed={r['task_id']:r for r in duplicates if r['state']=='removed'}
    if len(removed)!=final_storage['removed_duplicates']:raise ValueError('duplicate removal completion disagrees')
    for record in final_storage['removals']:
        if record['task_id'] not in removed or any(removed[record['task_id']].get(k)!=v for k,v in record.items()):
            raise ValueError('duplicate cleanup source changed')
    census=lineage.reconcile_catalog(catalog=catalog['files'],inventory=inventory['files'],retained=retained,
        followup=followup,duplicates=duplicates,selected=current)
    if (census['summary']['catalog_rows']!=326 or census['summary']['storage_counts']!=dict(retained=232,discarded_no_level=93,duplicate_removed=1,unresolved=0)
            or census['summary']['initial_no_level_rejections']!=58 or census['summary']['later_no_level_rejections']!=35):
        raise ValueError('catalog storage conservation failed')
    records={}
    if {r['result_origin'] for r in history}!=set(ALIASES):raise ValueError('unexpected numerical history origins')
    for origin,(kind,directory,role) in ALIASES.items():
        records[origin]=(reader.original_records(directory) if kind=='original' else reader.trial_records(directory,published_role=role)
            if kind=='trial' else reader.review_records(directory))
    origin_index=sources.index_history(history,records,reader)
    environments={}
    for row in origin_index:
        key=row['execution_manifest_sha256']
        if key not in environments:
            environments[key]={k:row[k] for k in ('execution_manifest','execution_manifest_sha256','environment_id','execution_python',
                'execution_numpy','execution_scipy','environment_json','kernel_metadata_json')}
            environments[key]['history_record_count']=0
        environments[key]['history_record_count']+=1
    origins=[]
    for origin in ALIASES:
        selected=[r for r in origin_index if r['result_origin']==origin]
        origins.append(dict(result_origin=origin,history_record_count=len(selected),publication_manifest=selected[0]['publication_manifest'],
            publication_manifest_sha256=selected[0]['publication_manifest_sha256'],
            execution_manifest_count=len({r['execution_manifest_sha256'] for r in selected}),
            environment_count=len({r['environment_id'] for r in selected}),operation_classes=';'.join(sorted({r['operation_class'] for r in selected}))))
    complete=all(all(row[k] for k in ('execution_python','execution_numpy','execution_scipy')) for row in origin_index)
    summary=dict(previous['summary'],acquisition_census_complete=census['summary']['complete'],fit_origin_environment_index_complete=complete,
        operation_origin_environment_index_complete=complete,catalog_files=326,initial_no_level_rejections=58,later_no_level_rejections=35,
        recorded_duplicate_removals=1,history_origin_tags=len(origins),history_rows_linked=len(origin_index),
        execution_manifests=len(environments),recorded_numerical_environments=len({r['environment_id'] for r in origin_index}),
        operation_classes=dict(collections.Counter(r['operation_class'] for r in origin_index)),
        interrupted_history_rows=sum(r['execution_state']=='interrupted' for r in origin_index),
        diagnostic_point_ancestry_unresolved_rows=sum(r['operation_class']!='full_fit' and not r['parameter_point_ancestry_fully_resolved'] for r in origin_index),
        parent_snapshot_version=previous['version'])
    if len(origin_index)!=791 or len(origins)!=16 or not complete:raise ValueError('operation/environment index is incomplete')
    return reader,inherited,census,origin_index,list(environments.values()),origins,summary


def build():
    if (DATA/'manifest.json').exists():raise ValueError('version 2 is already immutable; use --check or --publish')
    reader,outputs,census,origin_index,environments,origins,summary=collect()
    outputs=dict(outputs)
    for name,values in (('acquisition-census.csv',census['rows']),('numerical-origin-index.csv',origin_index),
            ('execution-environments.csv',environments),('origin-summary.csv',origins)):
        outputs[name]=dataset.encode_csv(values)
    outputs['acquisition-summary.json']=snapshot.encoded(census['summary'])
    outputs['source-index.csv']=dataset.encode_csv([dict(source_path=n,sha256=h,role='frozen acquisition/operation lineage metadata') for n,h in sorted(reader.inputs.items())])
    text=f'''# Development evidence dataset: complete provenance indices

**All 326 catalog entries and all 791 numerical-history rows are now indexed.**
The original 53 selected stretches and their 53 globe / zero flat / zero unresolved
numerical preferences are unchanged. Version 1 remains sealed and independently checkable.

## Acquisition and selection

| Recorded pipeline disposition | Files |
|---|---:|
| Retained | 232 |
| Initial no-level rejections | 58 |
| Later no-level rejections | 35 |
| Verified duplicate removed | 1 |
| Unresolved final storage disposition | 0 |
| **Catalog total** | **326** |

The [catalog census](acquisition-census.csv) retains every URL, original-byte hash,
reported size, observed byte length, storage evidence and eligibility state.
The 232 retained sources contain 53 eligible stretches from 53 files; 179 retained
files have no stretch under the current four-minute/high-speed policy. Retention
does not itself mean scientific eligibility. Historical reference copies outside
the pipeline are outside this storage census. No file was opened, removed or
downloaded to produce the table.

## Numerical operation provenance

The [row index](numerical-origin-index.csv) links every history entry to its exact
publication record and execution manifest. [Sixteen origin labels](origin-summary.csv)
resolve to {summary['execution_manifests']} execution manifests and
{summary['recorded_numerical_environments']} recorded numerical environments.
[Environment details](execution-environments.csv) preserve Python, NumPy, SciPy,
thread settings and kernel metadata from each operation, rather than using today's
environment or the environment of a later publication review.

There are {summary['operation_classes'].get('full_fit',0)} full-fit records,
{summary['operation_classes'].get('conditional_profile',0)} conditional profiles and
{summary['operation_classes'].get('endpoint_diagnostic',0)} endpoint-diagnostic records.
These are not independent trials. Failed and interrupted results retain their
original labels. The interrupted entry has no asserted evaluation count; its
reserved allowance remains visible. Diagnostics may reuse an earlier fitted point:
the direct source identity is preserved, but full point ancestry is not claimed
where it has not been reconstructed.

## Tables and interpretation

- [All 53 stretches](stretches.csv) and [318 latest primaries](latest-primary-comparisons.csv).
- [Complete numerical history](numerical-history.csv.gz), including failed records.
- [Conservative recording groups](recording-groups.csv) and [retained-file eligibility](retained-file-eligibility.csv).
- [Raw-gyro baselines](gyro-baselines.csv), [diagnostic studies](diagnostic-studies.csv), and [validation gates](validation-gates.csv).
- [Input hashes](source-index.csv), [selection criteria](ELIGIBILITY.md), and [assembly plan](PLAN.md).

An **IMU (inertial measurement unit)** records turning and specific force. Its
gyro increments supply turning observations; receiver positions supply route
context. Numerical preference, descriptive gyro agreement, predictive adequacy
and calibrated detection remain separate fields.

This is a development dataset, not the final validated paper dataset. The
27 conservative split groups are not verified independent flights. Qualified
withheld predictions, observational covariance, independent confirmation and
dependence-aware calibration remain open. Protected ESA measurements and model
outcomes were not read. No new fit, model evaluation or original-file read occurred.

Run `~/venv/bin/python docs/paper-development-dataset-v2/build_dataset.py --check`
to verify both versions and their frozen inputs. `--check-live` also checks named
current project inputs. `--publish` copies the completed snapshot without rebuilding
tables or running analysis. `--preflight` validates current metadata joins without
creating a snapshot. `--check-public` verifies the two public snapshots in a
repository checkout without any private runtime directory or original corpus.
Changed evidence requires a new version.

[Previous version](../paper-development-dataset-v1/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
'''
    outputs['README.md']=text.encode();outputs['PLAN.md']=(HERE/'PLAN.md').read_bytes()
    names=['analysis/lll/evidence_snapshot.py','analysis/lll/ilvis0_evidence_dataset.py','analysis/lll/ilvis0_evidence_lineage.py',
        'analysis/lll/ilvis0_lineage_sources.py','analysis/tests/test_evidence_snapshot.py','analysis/tests/test_ilvis0_evidence_lineage.py',
        'analysis/tests/test_ilvis0_lineage_sources.py','analysis/tests/test_paper_development_dataset_v2.py',
        'docs/paper-development-dataset-v2/build_dataset.py','docs/paper-development-dataset-v2/PLAN.md']
    snapshot.create(ROOT,DATA,version='paper-development-evidence-v2',inputs=reader.inputs,sources={n:snapshot.sha(ROOT/n) for n in names},
        outputs=outputs,summary=summary);snapshot.publish(DATA,HERE)


def main():
    parser=argparse.ArgumentParser(description=__doc__);group=parser.add_mutually_exclusive_group(required=True)
    for flag in ('build','check','check-live','check-public','publish','preflight'):group.add_argument('--'+flag,action='store_true')
    args=parser.parse_args()
    if args.preflight:
        *_,summary=collect();print(json.dumps(summary,sort_keys=True,indent=2))
    elif args.build:build();print('Built and verified development dataset version 2; no scientific computation.')
    elif args.publish:snapshot.publish(DATA,HERE);print('Published frozen version 2; no reconstruction.')
    elif args.check_public:
        for location in (HERE,ROOT/BASE):snapshot.check(location)
        print('Verified both public snapshots without runtime or original data.')
    else:
        for location in (DATA,HERE,ROOT/'data/paper-development-dataset-v1',ROOT/BASE):
            snapshot.check(location,live_root=ROOT if args.check_live else None)
        print('Verified both runtime/public dataset versions'+(' and named current inputs.' if args.check_live else '.'))


if __name__=='__main__':main()
