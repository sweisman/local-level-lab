# SPDX-License-Identifier: AGPL-3.0-or-later
"""Replay the ESA paired comparison across original and recovery evidence."""
from pathlib import Path

from lll.studies.closed import ClosedStudy
from lll.studies.combined_task_evidence import inspect as inspect_lineage
from lll.studies.artifacts import ArchiveStore


class _SnapshotStore(ArchiveStore):
    """Use one verified read-only archive index across sealed stages."""

    def __init__(self,root):
        super().__init__(root)
        self._snapshot=super().catalog()

    def catalog(self):
        return self._snapshot


class CombinedStudy:
    """Present one verified completed outcome per prescribed scientific task."""

    def __init__(self, root, ledger):
        self.root=Path(root).resolve()
        self.ledger=ledger
        origins={entry['origin'] for entry in ledger['selected'].values()}
        origins.add(ledger['parent'])
        self.store=_SnapshotStore(self.root)
        self.studies={}
        try:
            for name in sorted(origins):
                self.studies[name]=ClosedStudy(self.root,name,store=self.store)
            parent=self.studies[ledger['parent']]
            self.manifest=parent.manifest
            self.tasks=parent.tasks
            self.rows={identity:self.studies[item['origin']].rows[identity]
                       for identity,item in ledger['selected'].items()}
            self.completion=dict(manifest_sha256=parent.completion['manifest_sha256'],
                                 summary_sha256=ledger['lineage_sha256'])
            charged={key:0 for key in parent.summary['charged']}
            for identity in self.rows:
                envelope=self.envelope(identity)
                for key in charged:charged[key]+=envelope['charged'][key]
            self.summary=dict(charged=charged)
        except Exception:
            self.close()
            raise

    def _origin(self, identity):
        return self.studies[self.ledger['selected'][identity]['origin']]

    def origin_manifest(self, identity):
        return self._origin(identity).manifest

    def native_by_identity(self, checker):
        results={}
        for name,study in self.studies.items():
            selected={identity for identity,item in self.ledger['selected'].items()
                      if item['origin']==name}
            if not selected:continue
            for shard in range(study.manifest['allocation']['workers']):
                assigned={identity for identity,task in study.tasks.items()
                          if task['shard']==shard}
                counted=checker(study.read(
                    f'shards/{shard:03d}/charges/journal.sqlite',raw=True),
                    study.completion['manifest_sha256'],assigned,per_call_visits=None)
                results.update({identity:counted[identity]
                                for identity in selected & assigned})
        if set(results)!=set(self.ledger['selected']):
            raise ValueError('complete selected native accounting required')
        return results

    def input(self,key,*,raw=False):
        return self.studies[self.ledger['parent']].input(key,raw=raw)

    def read(self,name,expected=None,*,raw=False):
        return self.studies[self.ledger['parent']].read(name,expected,raw=raw)

    def read_artifact(self,identity,name,expected,*,raw=False):
        return self._origin(identity).read(name,expected,raw=raw)

    def envelope(self,identity):
        return self._origin(identity).envelope(identity)

    def artifact(self,identity,name):
        return self._origin(identity).artifact(identity,name)

    def close(self):
        for study in self.studies.values():study.close()
        self.store.close()


def inspect(root,campaign='data/esa-observed-hybrid-continuation-20261111'):
    """Verify lineage, then independently replay all 24 paired outcomes."""
    from lll.airquantumgrav_observed_hybrid_audit_v2 import inspect as replay

    root=Path(root).resolve()
    ledger=inspect_lineage(root,root/campaign)
    view=CombinedStudy(root,ledger)
    report=replay(root,study=view)
    if (report['total']!=ledger['total']
            or report['returned']!=ledger['completed']
            or report['passed']!=ledger['passing']):
        raise ValueError('paired replay differs from combined task ledger')
    report['original_manifest_sha256']=ledger['parent_manifest_sha256']
    report['original_completion_sha256']=ledger['parent_completion_sha256']
    report['continuation_completion_sha256']=ledger['campaign_completion_sha256']
    report['combined_lineage_sha256']=ledger['lineage_sha256']
    report['technical_interruptions']=ledger['technical_interruptions']
    report['attempts']=ledger['attempts']
    report['parent_study']=ledger['parent']
    report['terminal_reason']=ledger['terminal_reason']
    report['pending_identities']=ledger['pending_identities']
    report['continuation_state']=ledger['state']
    return report


SOURCES=(
    'docs/esa-observed-hybrid/PLAN.md',
    'docs/esa-observed-hybrid/AUDIT_PLAN.md',
    'analysis/lll/airquantumgrav_observed_hybrid_combined_audit.py',
    'analysis/lll/airquantumgrav_observed_hybrid_audit_v2.py',
    'analysis/lll/studies/combined_task_evidence.py',
    'analysis/lll/studies/task_resume.py',
    'analysis/lll/studies/task_continuation.py',
    'analysis/tests/test_airquantumgrav_observed_hybrid_audit_v2.py',
    'analysis/tests/test_combined_task_evidence.py',
    'analysis/tests/test_esa_combined_publication.py',
)


def render(report):
    """Short public account of the paired software-method result."""
    from math import isfinite
    from lll.airquantumgrav_observed_hybrid_audit_v2 import (
        FORECAST_TOLERANCE_M, substitution_qualified)

    if (report.get('verified') is not True or report.get('total')!=24
            or len(report.get('rows',()))!=24
            or not 0<=report.get('returned',-1)<=24
            or report['returned']!=sum(row.get('returned') is True
                                       for row in report['rows'])
            or report.get('passed',-1)+report.get('errors',-1)!=24
            or report.get('qualified')!=substitution_qualified(
                report['rows'],report.get('primary_checks',()),
                returned=report['returned'])
            or (report['returned']<24 and not report.get('terminal_reason'))):
        raise ValueError('complete independently replayed 24-pair report required')
    verdict='qualified' if report['qualified'] else 'did not qualify'
    original=[row for row in report['attempts']
              if row['origin']==report['parent_study']]
    original_passing=sum(row['status']=='complete' and row['passed']
                         for row in original)
    original_interrupted=sum(row['status']=='interrupted' for row in original)
    lines=['# ESA paired tangent check','',
           f"**{report['passed']}/24 paired cases passed; the method substitution {verdict}.**",'',
           'The same prepared development measurements and fitting source were used for',
           'both calculations in each pair. The tangent method was the within-pair',
           'change. This checks software behavior on one recording, not an independent',
           'Earth-model detection.','',
           f'The original allowance closed with {original_passing} passing pairs and {original_interrupted} technical',
           'interruptions. A separate, finite continuation reserved the missing',
           'identities without refitting sealed results. The complete attempt ledger',
           f"records {report['technical_interruptions']} technical interruptions.",'']
    if report['returned']<24:
        lines+= [f"The continuation stopped with {24-report['returned']} pairs without a sealed result.",
                 f"Its terminal reason was {report['terminal_reason']}. The substitution did not qualify.",'']
    failures=[row for row in report['rows'] if not row['passed']]
    if failures:
        lines+=['## Pairs that did not pass','','| Case | Reason |','|---|---|']
        for row in failures:
            comparison=row.get('comparison') or {}
            reason=row.get('reason') or comparison.get('reason')
            difference=comparison.get('maximum_position_difference_m')
            if (not reason and isinstance(difference,(int,float))
                    and isfinite(difference) and difference>FORECAST_TOLERANCE_M):
                reason=(f'Forecasts differ by {difference:.6f} m; '
                        f'fixed limit {FORECAST_TOLERANCE_M:g} m')
            reason=reason or 'paired check failed'
            lines.append(f"| {row['identity']} | {reason} |")
        lines.append('')
    checks=report.get('primary_checks',())
    lines += [f"Training-cost primary starts agree in {sum(row['same'] for row in checks)}/{len(checks)} complete groups.",'',
              '[All 24 paired outcomes](pair-results.csv) · '
              '[Every charged attempt](attempt-ledger.csv) · '
              '[Original plan](../PLAN.md) · [Audit method](../AUDIT_PLAN.md).','']
    return '\n'.join(lines)


REQUIRED_AUDIT_CASES = {
    'test_airquantumgrav_observed_hybrid_audit_v2': {
        'test_hybrid_audit_binds_qualified_subset_and_frozen_engine_extension',
        'test_hybrid_audit_rejects_unclosed_study_before_numeric_imports',
        'test_hybrid_public_summary_keeps_failed_pair_and_historical_baseline_separate',
        'test_hybrid_public_summary_rejects_qualified_label_with_failed_pair',
        'test_hybrid_publication_rows_keep_failed_pairs_and_measured_differences',
        'test_hybrid_qualification_requires_all_distinct_primary_groups',
    },
    'test_combined_task_evidence': {
        'test_combines_original_and_recovery_without_repeating_a_failed_result',
        'test_expired_continuation_reports_unfinished_identities_without_rerunning',
        'test_attempt_cap_reports_terminal_failure_with_every_charge',
    },
    'test_esa_combined_publication': {
        'test_public_report_requires_complete_verified_replay',
        'test_publication_contains_the_full_report_and_source_hashes',
        'test_publication_rejects_failing_test_report',
        'test_publication_rejects_missing_charged_attempt',
        'test_publication_receipt_detects_a_changed_artifact',
        'test_publication_rejects_unrelated_passing_suite',
        'test_publication_preserves_an_unfinished_pair_as_a_failed_gate',
        'test_public_report_names_forecast_equivalence_failure',
    },
}


def validate_test_report(raw):
    """Require a recorded passing local audit suite before sealing results."""
    from xml.etree import ElementTree

    try:
        root=ElementTree.fromstring(raw)
        suites=[root] if root.tag=='testsuite' else list(root)
        cases=list(root.iter('testcase'))
        if (root.tag not in ('testsuite','testsuites') or not suites
                or any(suite.tag!='testsuite' for suite in suites)
                or len(cases)!=sum(map(len, REQUIRED_AUDIT_CASES.values()))
                or sum(int(suite.attrib['tests']) for suite in suites)!=len(cases)
                or any(int(suite.attrib.get(key,0))!=0 for suite in suites
                       for key in ('failures','errors','skipped'))
                or any(child.tag in ('failure','error','skipped')
                       for case in cases for child in case)
                or {(case.attrib['classname'].rsplit('.',1)[-1],
                     case.attrib['name']) for case in cases}
                   != {(module,name) for module,names in REQUIRED_AUDIT_CASES.items()
                       for name in names}):
            raise ValueError('passing audit tests required')
    except (ElementTree.ParseError,KeyError,TypeError,ValueError) as exc:
        raise ValueError('passing audit tests required') from exc
    return len(cases)


def publication_artifacts(root,report,test_report):
    """Build small reproducible publication bytes; make no filesystem changes."""
    import csv
    import io
    from lll.airquantumgrav_observed_hybrid_audit_v2 import pair_rows
    from lll.studies.artifacts import digest,encoded,safe_path

    root=Path(root).resolve()
    validate_test_report(test_report)
    attempts=report.get('attempts',())
    complete=[row for row in attempts if row['status']=='complete']
    if (len(complete)!=report['returned']
            or len({row['identity'] for row in complete})!=report['returned']
            or {row['identity'] for row in complete}
               !={row['identity'] for row in report['rows'] if row['returned']}
            or (report['returned']<24 and
                sorted(row['identity'] for row in report['rows'] if not row['returned'])
                !=report.get('pending_identities'))
            or sum(row['status']=='interrupted' for row in attempts)
               !=report['technical_interruptions']
            or any(row['status'] not in ('complete','interrupted')
                   for row in attempts)):
        raise ValueError('complete charged-attempt ledger required')
    origins={row['identity']:row['origin'] for row in complete}
    rows=[dict(origin=origins.get(row['identity']),**row)
          for row in pair_rows(report)]
    if len(rows)!=24:
        raise ValueError('all prescribed pair rows required')
    stream=io.StringIO(newline='')
    writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
    attempts_stream=io.StringIO(newline='')
    fields=('attempt_index','origin','identity','status','passed','artifact',
            'artifact_sha256','native_calls','packet_visits','bound_calls','bound_steps')
    attempts_writer=csv.DictWriter(attempts_stream,fieldnames=fields)
    attempts_writer.writeheader()
    for index,row in enumerate(attempts):
        attempts_writer.writerow(dict(
            attempt_index=index,origin=row['origin'],identity=row['identity'],
            status=row['status'],passed=row['passed'],
            artifact=row.get('artifact'),artifact_sha256=row.get('artifact_sha256'),
            **{key:row['charged'][key] for key in fields[-4:]}))
    source_bytes={name:safe_path(root,name).read_bytes() for name in SOURCES}
    hashes={name:digest(raw) for name,raw in source_bytes.items()}
    materials=dict(
        **{'README.md':render(report).encode(),
           'pair-results.csv':stream.getvalue().encode(),
           'attempt-ledger.csv':attempts_stream.getvalue().encode(),
           'verified-report.json':encoded(report),
           'audit-tests.xml':test_report,
           'source-hashes.json':encoded(hashes)})
    for name,raw in source_bytes.items():
        materials['artifacts/source/'+Path(name).name]=raw
    return materials


def publish(root,*,test_report,campaign='data/esa-observed-hybrid-continuation-20261111',
            output='docs/esa-observed-hybrid/combined'):
    """Publish only a closed, independently replayed combined result."""
    from lll.studies.artifacts import atomic,digest,encoded,safe_path
    from lll.studies.closed import ClosedStudy

    root=Path(root).resolve();public=safe_path(root,output)
    receipt_path=public/'evidence-receipt.json'
    if receipt_path.exists():
        raise ValueError('combined ESA publication already sealed')
    report=inspect(root,campaign)
    parent=ClosedStudy(root,'data/esa-observed-hybrid-pilot-20261110')
    try:
        if digest((root/'docs/esa-observed-hybrid/PLAN.md').read_bytes())!=(
                parent.manifest['sources']['docs/esa-observed-hybrid/PLAN.md']):
            raise ValueError('original paired plan differs from frozen source')
    finally:parent.close()
    materials=publication_artifacts(root,report,
        safe_path(root,test_report).read_bytes())
    hashes={}
    for name,raw in materials.items():
        target=safe_path(public,name);atomic(target,raw);hashes[name]=digest(raw)
    receipt=dict(version='esa-hybrid-combined-publication-v1',
        artifacts=hashes,qualified=report['qualified'],
        parent_completion_sha256=report['original_completion_sha256'],
        continuation_completion_sha256=report['continuation_completion_sha256'],
        combined_lineage_sha256=report['combined_lineage_sha256'],
        original_reads=0,protected_reads=0,native_calls=0,
        scientific_decision='abstain')
    atomic(receipt_path,encoded(receipt))
    return dict(published=output,qualified=report['qualified'],cases=24,
                receipt_sha256=digest(encoded(receipt)))


def verify_publication(root,output='docs/esa-observed-hybrid/combined'):
    """Check every published byte without fitting or reading aircraft originals."""
    import json
    from lll.studies.artifacts import digest,safe_path

    root=Path(root).resolve();public=safe_path(root,output)
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    if (receipt.get('version')!='esa-hybrid-combined-publication-v1'
            or receipt.get('scientific_decision')!='abstain'
            or receipt.get('original_reads')!=0
            or receipt.get('protected_reads')!=0
            or receipt.get('native_calls')!=0):
        raise ValueError('invalid combined publication receipt')
    required={'README.md','pair-results.csv','attempt-ledger.csv',
              'verified-report.json','source-hashes.json','audit-tests.xml'}
    required.update('artifacts/source/'+Path(name).name for name in SOURCES)
    if not required.issubset(receipt['artifacts']):
        raise ValueError('incomplete combined publication receipt')
    for name,expected in receipt['artifacts'].items():
        if digest(safe_path(public,name).read_bytes())!=expected:
            raise ValueError('published evidence changed: '+name)
    validate_test_report((public/'audit-tests.xml').read_bytes())
    report=json.loads((public/'verified-report.json').read_bytes())
    if (report.get('qualified')!=receipt.get('qualified')
            or report.get('original_completion_sha256')!=receipt.get('parent_completion_sha256')
            or report.get('continuation_completion_sha256')!=receipt.get('continuation_completion_sha256')
            or report.get('combined_lineage_sha256')!=receipt.get('combined_lineage_sha256')
            or render(report).encode()!=(public/'README.md').read_bytes()):
        raise ValueError('publication receipt differs from report')
    source_hashes=json.loads((public/'source-hashes.json').read_bytes())
    if (set(source_hashes)!=set(SOURCES)
            or any(source_hashes[name]!=digest((public/'artifacts/source'/Path(name).name).read_bytes())
                   for name in SOURCES)):
        raise ValueError('published source hash differs from archived source')
    return dict(verified=True,artifacts=len(receipt['artifacts']),
                receipt_sha256=digest((public/'evidence-receipt.json').read_bytes()))


def main():
    """Seal or verify the completed ESA paired comparison from a fresh process."""
    import argparse
    import json

    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('publish','verify'))
    parser.add_argument('--project',default='.')
    parser.add_argument('--test-report')
    args=parser.parse_args()
    if args.action=='publish':
        if not args.test_report:
            parser.error('publish requires --test-report')
        result=publish(args.project,test_report=args.test_report)
    else:
        result=verify_publication(args.project)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
