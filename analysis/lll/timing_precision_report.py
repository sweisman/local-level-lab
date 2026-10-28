# SPDX-License-Identifier: AGPL-3.0-or-later
"""Package small timing controls and hash-checked saved-clock metadata only."""
import bisect
import csv
import io
import json
from pathlib import Path
import struct


def query_alignment(times,offset,*,packets,expected_dt_sha256):
    from lll.studies.artifacts import digest
    # A tested reconstruction of the declared generated grid, accepted only
    # when every interval byte matches the previously saved input hash.
    dt=[(i+1)/300-i/300 for i in range(packets)]
    if digest(struct.pack('<'+str(packets)+'d',*dt))!=expected_dt_sha256:
        raise ValueError('saved interval hash does not match the proposed 300 Hz grid')
    ends=[];elapsed=0.
    for d in dt:elapsed+=d;ends.append(elapsed)
    distances=[];exact=0;near=0
    for t in times:
        query=t+offset;k=bisect.bisect_left(ends,query)
        if k==packets or query<0:raise ValueError('saved query lacks packet support')
        gap=ends[k]-query;distances.append(gap);exact+=int(gap==0)
        near+=int(gap/dt[k]<1e-8)
    return dict(rate_hz=300,interval_hash_verified=True,queries=len(times),
        exact_packet_end_queries=exact,native_near_end_queries=near,
        packet_end_distance_max_s=max(distances))


def inspect(root,prefix):
    from lll.studies.closed import ClosedStudy
    from lll.studies.journal import inspect_snapshot
    from lll.studies.artifacts import digest
    from lll.timing_precision_controls import cases,SCOPE
    root=Path(root);s=ClosedStudy(root,prefix)
    try:
        if s.manifest['scope']!=SCOPE or tuple(s.tasks)!=cases() or len(s.rows)!=7:
            raise ValueError('exact complete seven-case control required')
        rows=[]
        for identity in s.tasks:
            d=s.artifact(identity,'control.json')
            s.artifact(identity,'native-binding.json')
            if (d['identity']!=identity or d['native_evaluations']!=s.rows[identity]['charged']['native_calls']
                    or any(d[k]!=0 for k in ('nonlinear_fit_starts','original_reads','protected_reads'))
                    or d['whole_pipeline_qualified']):raise ValueError('control accounting or scope changed')
            rows.append(d)
        builds=s.read('builds.sqlite',raw=True) if (root/prefix/'builds.sqlite').is_file() else s.read('artifacts/publication/builds.sqlite',raw=True)
        journal=inspect_snapshot(builds,s.completion['manifest_sha256'])
        if journal['starts']!=1 or journal['sweeps']!=1:raise ValueError('one charged compiler build required')
        return dict(manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            rows=rows,complete=7,passed=sum(r['passed'] for r in rows),
            native_evaluations=sum(r['native_evaluations'] for r in rows),
            charged=s.summary['charged'],elapsed_s=s.summary['elapsed_s'],builds_sha256=digest(builds),
            compiler_builds=1,nonlinear_fit_starts=0,original_reads=0,protected_reads=0,
            whole_pipeline_qualified=False,scientific_decision='abstain')
    finally:s.close()


def saved_alignment(root):
    from lll.studies.closed import ClosedStudy
    s=ClosedStudy(root,'data/prediction-stopping-consistency-20261026')
    try:
        rows=[]
        for point in s.input('points'):
            identity=point['identity'];fit=point['fit']
            observed=s.artifact(identity,'reconstructed/training-observations.json')
            offset=fit['parameters']['time_offset']
            rows.append(dict(identity=identity,normalized_offset=fit['normalized_parameters'][fit['active_parameters'].index('time_offset')],
                physical_offset_s=offset,**query_alignment(observed['times_s'],offset,
                    packets=observed['native_prefix_packets'],expected_dt_sha256=observed['training_prefix_sha256']['dt'])))
        return dict(manifest_sha256=s.completion['manifest_sha256'],summary_sha256=s.completion['summary_sha256'],
            source='previously exposed saved metadata, not a new residual evaluation',rows=rows)
    finally:s.close()


def publish(root,prefix='data/timing-precision-controls-20261026',output='docs/timing-precision-controls'):
    from lll.ilvis0_control_publication import publish as package,check
    from lll.studies.artifacts import atomic,encoded,digest
    root=Path(root).resolve();public=root/output
    if (public/'evidence-receipt.json').exists():raise ValueError('immutable publication already exists')
    report=inspect(root,prefix);alignment=saved_alignment(root)
    interpretation=public/'INTERPRETATION.md'
    package(root/prefix,public,interpretation.read_text(),plan='docs/TIMING_PRECISION_CONTROLS.md')
    stream=io.StringIO(newline='');fields=['identity','passed','native_evaluations','derivative_column',
        'position_error','derivative_error','analytic_error_to_left','derivative_branch_gap',
        'analytic_relative_error','finite_difference_relative_error']
    writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore',lineterminator='\n')
    writer.writeheader();writer.writerows(report['rows'])
    extras={'results.csv':stream.getvalue().encode(),'artifacts/publication/verified-report.json':encoded(report),
        'artifacts/publication/saved-clock-alignment.json':encoded(alignment),
        'artifacts/publication/builds.sqlite':(root/prefix/'builds.sqlite').read_bytes(),
        'artifacts/publication/report-source.py':Path(__file__).read_bytes(),
        'artifacts/publication/report-tests.py':Path(__file__).parents[1].joinpath('tests/test_timing_precision_report.py').read_bytes(),
        'INTERPRETATION.md':interpretation.read_bytes()}
    receipt=json.loads((public/'evidence-receipt.json').read_bytes())
    for name,raw in extras.items():atomic(public/name,raw);receipt['artifacts'][name]=digest(raw)
    atomic(public/'evidence-receipt.json',encoded(receipt));check(root/prefix,public)
    if encoded(inspect(root,output))!=encoded(report):raise ValueError('published control replay differs')
    return dict(path=output,complete=report['complete'],native_calls=0,nonlinear_fit_starts=0,
        saved_alignment=alignment)
