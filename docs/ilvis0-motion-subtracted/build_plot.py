# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render the navigation-assisted display from preserved descriptive caches."""
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import statistics
import sys
import time
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'analysis'))


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
def csv_bytes(rows):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows);return stream.getvalue().encode()


def build():
    from lll.compute_budget import environment
    if any(os.environ.get(k)!=v for k,v in environment(workers=1,threads=1,reserved=2).items()):
        raise ValueError('one plotting thread with two reserved is required')
    scratch=ROOT/'data/ilvis0-source-point-development/scratch/motion-plot-matplotlib'
    scratch.mkdir(parents=True,exist_ok=True);os.environ['MPLCONFIGDIR']=str(scratch)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from lll.ilvis0_gyro_prediction import receiver_geometry,OMEGA
    from lll.ilvis0_motion_plot import trace
    started=time.monotonic();inputs={};records=[];outcomes=[];traces=[]
    source=ROOT/'docs/ilvis0-gyro-companion-v2';receipt=load(source/'evidence-receipt.json');manifest=load(source/'manifest.json')
    for path in (source/'evidence-receipt.json',source/'manifest.json',
            ROOT/'docs/ilvis0-position-stability-trial-20261013/analytics-receipt.json'):
        inputs[str(path.relative_to(ROOT))]=sha(path)
    def verified(path,expected):
        digest=sha(path)
        if digest!=expected:raise ValueError('preserved input changed: '+str(path))
        inputs[str(path.relative_to(ROOT))]=digest;return load(path)
    summary=verified(source/'summary.json',receipt['artifacts']['summary.json'])
    if not summary['passed']:raise ValueError('qualified companion input required')
    selection=ROOT/'docs/ilvis0-highspeed-segments-20261008/selection.json.gz'
    selected=verified(selection,manifest['inputs'][str(selection.relative_to(ROOT))])
    selections={r['segment']['segment_id']:r['segment'] for r in selected['selected']}
    cache=ROOT/'data/ilvis0-stretch-analytics-20261013'
    analytics_receipt=load(ROOT/'docs/ilvis0-position-stability-trial-20261013/analytics-receipt.json')
    verified(cache/'manifest.json',analytics_receipt['cache_manifest_sha256'])
    observed=[r for r in summary['results'] if r['kind']=='observed']
    if len(observed)!=53 or set(selections)!={r['identity'] for r in observed}:raise ValueError('all53 outcomes required')
    for item in observed:
        if time.monotonic()-started>180:raise ValueError('cooperative plotting allowance exhausted')
        result=verified(source/item['artifact'],item['artifact_sha256']);sid=item['identity']
        path=cache/(sid+'.json.gz');saved=verified(path,analytics_receipt['cache_artifacts'][str(path)])
        if saved['cache_manifest_sha256']!=analytics_receipt['cache_manifest_sha256']:
            raise ValueError('cache source freeze mismatch')
        support=result['matched_support'];fixes=selections[sid]['receiver_fixes']
        if len(support['utc_seconds'])>1000 or len(fixes)>1500:raise ValueError('finite plotting scope exceeded')
        rows=trace(receiver_geometry(fixes),support,saved['seconds']);valid=sum(r['supported'] for r in rows)
        plotted=valid==len(rows)
        records.extend(dict(segment_id=sid,plotted_in_figure=plotted,**r) for r in rows)
        outcomes.append(dict(segment_id=sid,filename=result['metadata']['filename'],plotted=plotted,
            matched_bins=len(rows),motion_supported_bins=valid,missing_motion_bins=len(rows)-valid,
            raw_pitch_endpoint_deg=rows[-1]['raw_pitch_deg'],
            residual_across_track_endpoint_deg=rows[-1]['residual_across_track_deg'] if plotted else None,
            reason='' if plotted else 'incomplete navigation correction on matched gyro/receiver support'))
        if plotted:traces.append(rows)
    if not traces:raise ValueError('no complete motion-corrected traces available')
    # Preserve the original plot's vertical range; expand only to avoid clipping.
    original=ROOT/'docs/ilvis0-gyro-overview';prior=load(original/'provenance.json');path=original/'plotted-bins.csv.gz'
    inputs[str((original/'provenance.json').relative_to(ROOT))]=sha(original/'provenance.json')
    if sha(path)!=prior['artifacts']['plotted-bins.csv.gz']:raise ValueError('raw plotted input changed')
    inputs[str(path.relative_to(ROOT))]=sha(path)
    raw=[float(r['accumulated_nose_down_axis_deg']) for r in csv.DictReader(io.StringIO(gzip.decompress(path.read_bytes()).decode()))]
    raw_min,raw_max=min(0.,min(raw)),max(0.,max(raw));pad=.05*(raw_max-raw_min)
    old_limits=[raw_min-pad,raw_max+pad]
    corrected=[r['residual_across_track_deg'] for rows in traces for r in rows]
    limits=[min(old_limits[0],min(corrected)-pad),max(old_limits[1],max(corrected)+pad)]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
        'svg.hashsalt':'lll-navigation-motion-subtracted-v1','axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(12,7));fig.patch.set_facecolor('#fcfcfa');ax.set_facecolor('#fcfcfa')
    count=len(traces);by_second={0:[0.]*count}
    for i,rows in enumerate(traces):
        x=[0.];y=[0.]
        for row in rows:
            if row['gap_before']:x.append(float('nan'));y.append(float('nan'))
            x.append(row['elapsed_s']/60);y.append(row['residual_across_track_deg'])
            by_second.setdefault(row['elapsed_s'],[]).append(row['residual_across_track_deg'])
        ax.plot(x,y,color='#338b79',alpha=.3,linewidth=1,label=f'Each of the {count} supported stretches' if i==0 else None)
    common=[s for s in sorted(by_second) if len(by_second[s])==count]
    tail=[s for s in sorted(by_second) if s>=max(common) and len(by_second[s])>=5]
    for seconds,style,label in ((common,'-',f'Median: all {count} supported stretches'),
            (tail,'--','Median: available stretches (at least 5)')):
        ax.plot([s/60 for s in seconds],[statistics.median(by_second[s]) for s in seconds],
            color='#155f51',linewidth=3 if style=='-' else 2.5,linestyle=style,label=label)
    ax.axhline(0,color='#59646d',linewidth=.9,alpha=.7);ax.set_ylim(limits[1],limits[0])
    ax.set_xlim(0,max(r[-1]['elapsed_s'] for r in traces)/60+.15);ax.grid(axis='y',alpha=.16)
    ax.set_xlabel('Elapsed time from first matched one-second bin (minutes)',labelpad=12)
    ax.set_ylabel('Accumulated across-track tilt (degrees)\nNose-down increases downward',labelpad=12)
    ax.legend(loc='upper left',frameon=False,fontsize=10)
    fig.text(.10,.95,'After background rotation and estimated maneuvers are removed',fontsize=18,fontweight='bold',color='#142f3a')
    fig.text(.10,.905,f'{count} of 53 stretches. Navigation-assisted correction; tilt aligned across the flight path.',fontsize=11,color='#475962')
    fig.text(.10,.055,'Transport rotation and measurement/correction errors remain. This is a visualization, not an independent curvature test.',fontsize=9.5,color='#475962')
    fig.text(.10,.026,'The maneuver estimate uses fused navigation attitude. Unsupported corrections are omitted; none are filled with zeros.',fontsize=9.5,color='#475962')
    fig.subplots_adjust(left=.10,right=.97,top=.86,bottom=.17)
    for ext in ('png','svg'):
        path=HERE/('motion-subtracted.'+ext);fig.savefig(path,dpi=180,metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)
    (HERE/'plotted-bins.csv.gz').write_bytes(gzip.compress(csv_bytes(records),mtime=0))
    (HERE/'stretches.csv').write_bytes(csv_bytes(outcomes))
    endpoints=[r['residual_across_track_endpoint_deg'] for r in outcomes if r['plotted']]
    outputs=['motion-subtracted.png','motion-subtracted.svg','plotted-bins.csv.gz','stretches.csv']
    sources=['analysis/lll/ilvis0_motion_plot.py','analysis/lll/ilvis0_gyro_prediction.py',
        'analysis/lll/ilvis0_stretch_analytics.py','analysis/tests/test_ilvis0_motion_plot.py',
        str(Path(__file__).relative_to(ROOT)),'docs/ilvis0-motion-subtracted/PLAN.md']
    provenance=dict(selected_stretches=53,plotted_stretches=count,matched_bins=len(records),
        plotted_bins=sum(r['plotted_in_figure'] for r in records),missing_motion_bins=sum(not r['supported'] for r in records),
        positive_endpoints=sum(v>0 for v in endpoints),endpoint_minimum_deg=min(endpoints),
        endpoint_median_deg=statistics.median(endpoints),endpoint_maximum_deg=max(endpoints),
        y_limits_deg=limits,raw_plot_y_limits_deg=old_limits,raw_y_range_expanded=limits!=old_limits,
        background_omega_rads=OMEGA,background_rate_fitted=False,upstream_removal_assumed=0.,
        axis='ground-track across-left; differs from aircraft-fixed pitch in first two plots',
        fused_attitude_used=True,fused_gyro_rates_used=False,transport_subtracted=False,
        original_reads=0,native_evaluations=0,optimizer_starts=0,numerical_threads=1,reserved_threads=2,
        scientific_decision='abstain',research_inputs_changed=False,elapsed_s=time.monotonic()-started,
        inputs=inputs,sources={n:sha(ROOT/n) for n in sources},artifacts={n:sha(HERE/n) for n in outputs})
    (HERE/'provenance.json').write_text(json.dumps(provenance,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in provenance.items() if k not in ('inputs','sources','artifacts')}))


if __name__=='__main__':build()
