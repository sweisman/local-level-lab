# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render a fixed-field-subtracted companion from preserved gyro observations."""
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
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def csv_bytes(rows):
    output=io.StringIO(newline='');writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n')
    writer.writeheader();writer.writerows(rows);return output.getvalue().encode()


def build():
    from lll.compute_budget import environment
    if any(os.environ.get(k)!=v for k,v in environment(workers=1,threads=4,reserved=0).items()):
        raise ValueError('launch through run_numerical.py with one worker/four threads')
    os.environ.setdefault('MPLCONFIGDIR','/tmp/local-level-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from lll import ilvis0_gyro_prediction as prediction
    from lll.ilvis0_background_plot import trace
    started=time.monotonic();inputs={};records=[];endpoints=[];traces=[]
    source=ROOT/'docs/ilvis0-gyro-companion-v2'
    receipt=load(source/'evidence-receipt.json');manifest=load(source/'manifest.json')
    def verified(path,expected):
        digest=sha(path)
        if digest!=expected:raise ValueError('preserved source changed: '+str(path))
        inputs[str(path.relative_to(ROOT))]=digest
        return load(path)
    summary=verified(source/'summary.json',receipt['artifacts']['summary.json'])
    if not summary['passed']:raise ValueError('qualified gyro companion required')
    module=Path(prediction.__file__)
    if sha(module)!=manifest['sources']['analysis/lll/ilvis0_gyro_prediction.py']:
        raise ValueError('qualified geographic prediction source changed')
    selection_path=ROOT/'docs/ilvis0-highspeed-segments-20261008/selection.json.gz'
    selected=verified(selection_path,manifest['inputs'][str(selection_path.relative_to(ROOT))])
    selections={r['segment']['segment_id']:r['segment'] for r in selected['selected']}
    observed=[r for r in summary['results'] if r['kind']=='observed']
    if len(observed)!=53 or set(selections)!={r['identity'] for r in observed}:raise ValueError('all 53 selections required')
    for record in observed:
        if time.monotonic()-started>180:raise ValueError('cooperative plotting allowance exhausted')
        result=verified(source/record['artifact'],record['artifact_sha256'])
        sid=record['identity'];support=result['matched_support'];fixes=selections[sid]['receiver_fixes']
        if len(fixes)>1500 or len(support['utc_seconds'])>1000 or not result['supported']:
            raise ValueError('finite supported plotting scope required')
        geometry=prediction.receiver_geometry(fixes);rows=trace(geometry,support)
        baseline={r['model']:r for r in result['baseline']}
        expected_field=baseline['sphere_rotating']['predicted_nose_down_deg']-baseline['sphere_still']['predicted_nose_down_deg']
        if (abs(rows[-1]['raw_nose_down_deg']-baseline['sphere_rotating']['observed_nose_down_deg'])>1e-10
                or abs(rows[-1]['assumed_background_deg']-expected_field)>1e-10):
            raise ValueError('per-bin correction disagrees with sealed companion summaries')
        records.extend(dict(segment_id=sid,**r) for r in rows)
        endpoints.append(dict(segment_id=sid,filename=result['metadata']['filename'],
            duration_s=sum(support['durations_s']),excluded_bins=len(support['excluded']),
            gap_count=sum(r['gap_before'] for r in rows),
            raw_nose_down_deg=rows[-1]['raw_nose_down_deg'],
            assumed_background_deg=rows[-1]['assumed_background_deg'],
            corrected_nose_down_deg=rows[-1]['corrected_nose_down_deg']))
        traces.append(rows)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none',
        'svg.hashsalt':'lll-background-subtracted-v1','axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(12,7));fig.patch.set_facecolor('#fcfcfa');ax.set_facecolor('#fcfcfa')
    by_second={0:[0.]*53}
    for i,rows in enumerate(traces):
        x=[0.];y=[0.]
        for row in rows:
            if row['gap_before']:x.append(float('nan'));y.append(float('nan'))
            x.append(row['elapsed_s']/60);y.append(row['corrected_nose_down_deg'])
            by_second.setdefault(row['elapsed_s'],[]).append(row['corrected_nose_down_deg'])
        ax.plot(x,y,color='#9b6944',alpha=.3,linewidth=1,label='Each of the 53 stretches' if i==0 else None)
    common=[s for s in sorted(by_second) if len(by_second[s])==53]
    tail=[s for s in sorted(by_second) if s>=max(common) and len(by_second[s])>=5]
    for seconds,style,label in ((common,'-','Median: all 53 stretches'),(tail,'--','Median: available stretches (at least 5)')):
        ax.plot([s/60 for s in seconds],[statistics.median(by_second[s]) for s in seconds],
            color='#583821',linewidth=3 if style=='-' else 2.5,linestyle=style,label=label)
    ax.axhline(0,color='#59646d',linewidth=.9,alpha=.7);ax.invert_yaxis()
    ax.set_xlabel('Elapsed time from first matched one-second bin (minutes)',labelpad=12)
    ax.set_ylabel('Accumulated pitch-axis increments (degrees)\nSpecified field subtracted; nose-down increases downward',labelpad=12)
    ax.set_xlim(0,max(rows[-1]['elapsed_s'] for rows in traces)/60+.15)
    ax.grid(axis='y',alpha=.16);ax.legend(loc='upper left',frameon=False,fontsize=10)
    fig.text(.10,.95,'Gyro motion after subtracting the specified background field',
        fontsize=19,fontweight='bold',color='#142f3a')
    fig.text(.10,.905,'Same recordings. Fixed field prediction; level attitude and heading equal to GPS course.',
        fontsize=11,color='#475962')
    fig.text(.10,.055,'Transport rotation and aircraft motion remain. This is a model-adjusted visualization, not an isolated curvature measurement.',
        fontsize=9.5,color='#475962')
    fig.text(.10,.026,'Unlike the raw plot, the subtraction uses receiver coordinates. The field magnitude is supplied, not measured by this plot.',
        fontsize=9.5,color='#475962')
    fig.subplots_adjust(left=.10,right=.97,top=.86,bottom=.17)
    for ext in ('png','svg'):
        fig.savefig(HERE/('background-subtracted.'+ext),dpi=180,metadata={'Date':None} if ext=='svg' else None)
        if ext=='svg':
            path=HERE/'background-subtracted.svg'
            path.write_text('\n'.join(line.rstrip() for line in path.read_text().splitlines())+'\n')
    plt.close(fig)
    (HERE/'plotted-bins.csv.gz').write_bytes(gzip.compress(csv_bytes(records),mtime=0))
    (HERE/'endpoints.csv').write_bytes(csv_bytes(endpoints))
    positive=sum(r['corrected_nose_down_deg']>0 for r in endpoints)
    outputs=['background-subtracted.png','background-subtracted.svg','plotted-bins.csv.gz','endpoints.csv']
    source_names=['analysis/lll/ilvis0_gyro_prediction.py','analysis/lll/ilvis0_background_plot.py',
        'analysis/tests/test_ilvis0_background_plot.py',str(Path(__file__).relative_to(ROOT)),
        'docs/ilvis0-background-subtracted/PLAN.md']
    provenance=dict(stretches=53,bins=len(records),positive_endpoints=positive,negative_endpoints=53-positive,
        corrected_endpoint_minimum_deg=min(r['corrected_nose_down_deg'] for r in endpoints),
        corrected_endpoint_median_deg=statistics.median(r['corrected_nose_down_deg'] for r in endpoints),
        corrected_endpoint_maximum_deg=max(r['corrected_nose_down_deg'] for r in endpoints),
        excluded_bins=sum(r['excluded_bins'] for r in endpoints),interior_gaps=sum(r['gap_count'] for r in endpoints),
        omega_rads=prediction.OMEGA,assumed_roll_deg=0.,assumed_pitch_deg=0.,assumed_crab_deg=0.,
        field_fitted=False,transport_subtracted=False,fused_attitude_used=False,receiver_used_for_subtraction=True,
        original_reads=0,native_evaluations=0,optimizer_starts=0,numerical_threads=4,
        scientific_decision='abstain',inputs=inputs,sources={n:sha(ROOT/n) for n in source_names},
        artifacts={n:sha(HERE/n) for n in outputs})
    (HERE/'provenance.json').write_text(json.dumps(provenance,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:v for k,v in provenance.items() if k not in ('inputs','sources','artifacts')}))


if __name__=='__main__':build()
