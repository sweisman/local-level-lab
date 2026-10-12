# SPDX-License-Identifier: AGPL-3.0-or-later
"""Longer-lag/cross-axis/spectral audit of saved fits; no native predictions."""
import csv
import gzip
import hashlib
import io
import itertools
import json
import os
from pathlib import Path

import numpy as np
from lll import ilvis0_residual_covariance as analysis
from lll import ilvis0_z_followup_audit as grid_audit
from lll import ilvis0_z_profile_audit as profiles
from lll import ilvis0_solver_diagnosis as diagnosis
from lll import ilvis0_saved_audit as saved
from lll import runtime

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PLAN=HERE/'ERROR_MODEL_PLAN.md'
INPUTS={s:HERE.parent/p for s,p in (
    ('original','ilvis0-z-profile-20261011'),('removal','ilvis0-z-profile-removal-20261011'),
    ('replication','ilvis0-z-profile-replication-20261011'))}


def load(p):return json.loads(p.read_text())


def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read_inputs():
    grids={}
    for study,path in INPUTS.items():
        saved.verify_artifacts(path,load(path/'evidence-receipt.json'))
        done=load(path/'completion.json')
        if (done['state']!='complete' or done['starts']!=27 or
            done['manifest_sha256']!=sha(path/'manifest.json') or
            done['summary_sha256']!=sha(path/'summary.json')):
            raise ValueError('invalid published completion')
        grids[study]=load(path/'summary.json'),load(path/'manifest.json')
    grid_audit.compare(grids)
    return grids


def epoch_values(study,fit):
    path=INPUTS[study]/fit['residual_file']
    if path.resolve().parent!=INPUTS[study].resolve() or sha(path)!=fit['residual_sha256']:
        raise ValueError('invalid saved residual artifact')
    with gzip.open(path,'rt') as stream:rows=list(csv.DictReader(stream))
    t=np.array([float(r['time_utc_week_s']) for r in rows])
    x=np.array([[float(r[a+'_residual_m']) for a in analysis.AXES] for r in rows])
    z=np.array([[float(r[a+'_primary_innovation']) for a in analysis.AXES] for r in rows])
    if (len(t)<3 or not np.all(np.isfinite(t)) or np.any(np.diff(t)<=0) or
        not np.all(np.isfinite(x)) or not np.all(np.isfinite(z)) or
        not np.allclose(np.sqrt(np.mean(x*x,axis=0)),fit['residual_rms_neu_m'],rtol=1e-10,atol=1e-12) or
        not np.isclose(float(np.sum(z*z)),fit['residual_sum_squares'],rtol=1e-6,atol=1e-9)):
        raise ValueError('invalid epoch values or disagreement with saved RMS/cost')
    return t,x,z


def table(name,rows,compressed=False):
    rows=iter(rows);first=next(rows);path=HERE/name;temporary=path.with_suffix(path.suffix+'.partial')
    with temporary.open('wb') as binary:
        raw=gzip.GzipFile(filename='',mode='wb',fileobj=binary,mtime=0) if compressed else binary
        with io.TextIOWrapper(raw,encoding='utf-8',newline='') as text:
            writer=csv.DictWriter(text,fieldnames=list(first),lineterminator='\n')
            writer.writeheader();writer.writerows(itertools.chain((first,),rows))
    temporary.replace(path)


def figures(curves):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/lll-residual-covariance-mpl')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    matplotlib.rcParams.update({'svg.hashsalt':analysis.VERSION,'svg.fonttype':'none'})
    colors=('tab:blue','tab:orange','tab:green')
    figure,axes=plt.subplots(2,3,figsize=(12,6),sharex=True,sharey=True,layout='constrained')
    for column,study in enumerate(INPUTS):
        for row,kind in enumerate(('physical','innovation')):
            groups=[v for k,v in curves.items() if k[:2]==(study,kind) and
                    v['model']=='sphere_rotating' and v['status']=='converged']
            for j,name in enumerate(analysis.AXES):
                values=np.array([[v['lags'][lag]['correlation'][j][j] for lag in range(61)] for v in groups],float)
                lag=np.array([r['median_lag_s'] for r in groups[0]['lags']])
                axes[row,column].plot(lag,np.median(values,axis=0),color=colors[j],label=name)
                axes[row,column].fill_between(lag,values.min(axis=0),values.max(axis=0),color=colors[j],alpha=.12)
            axes[row,column].axhline(0,color='gray',lw=.6)
            axes[row,column].set_title(f'{study}: {kind} ({len(groups)} completed variants)')
            axes[row,column].set_ylim(-1,1);axes[row,column].grid(alpha=.2)
            if row:axes[row,column].set_xlabel('Actual lag (seconds)')
            if not column:axes[row,column].set_ylabel('Centered correlation')
    axes[0,0].legend();figure.suptitle('Specified-field globe: median curves; shading is calibration-grid range, not uncertainty')
    figure.savefig(HERE/'autocorrelation.svg',metadata={'Date':None});plt.close(figure)
    figure,axes=plt.subplots(2,3,figsize=(11,6),layout='constrained')
    for column,study in enumerate(INPUTS):
        for row,kind in enumerate(('physical','innovation')):
            v=curves[study,kind,'sphere_rotating',0,0];matrix=np.asarray(v['correlation'],float)
            plotted=axes[row,column].imshow(matrix,vmin=-1,vmax=1,cmap='coolwarm')
            axes[row,column].set_xticks(range(3),analysis.AXES);axes[row,column].set_yticks(range(3),analysis.AXES)
            axes[row,column].set_title(f'{study}: {kind}')
            for i in range(3):
                for j in range(3):axes[row,column].text(j,i,f'{matrix[i,j]:.2f}',ha='center',va='center')
    figure.colorbar(plotted,ax=axes.ravel().tolist(),shrink=.8)
    figure.suptitle('Zero-Z-correction anchor: cross-axis correlation; innovation labels denote whitening channels')
    figure.savefig(HERE/'cross-axis.svg',metadata={'Date':None});plt.close(figure)
    figure,axes=plt.subplots(2,3,figsize=(12,6),layout='constrained')
    for column,study in enumerate(INPUTS):
        for row,kind in enumerate(('physical','innovation')):
            v=curves[study,kind,'sphere_rotating',0,0];s=v['spectrum']
            if s is not None:
                f=np.array(s['frequencies_hz']);p=np.array(s['density'])
                for j,name in enumerate(analysis.AXES):
                    mask=(f>0)&(p[:,j]>0);axes[row,column].loglog(f[mask],p[mask,j],label=name,color=colors[j])
                axes[row,column].axvline(1/60,color='gray',ls='--',lw=.7)
            axes[row,column].set_title(f'{study}: {kind}');axes[row,column].grid(alpha=.2)
            if row:axes[row,column].set_xlabel('Frequency (Hz)')
            if not column:axes[row,column].set_ylabel('m²/Hz' if kind=='physical' else 'Innovation²/Hz')
    axes[0,0].legend();figure.suptitle('Zero-Z-correction anchor: mean-removed Hann spectra; dashed line = 60-second period')
    figure.savefig(HERE/'spectra.svg',metadata={'Date':None});plt.close(figure)
    return ['autocorrelation.svg','cross-axis.svg','spectra.svg'],matplotlib.__version__


def build():
    grids=read_inputs();curves={};series=[];axis_rows=[]
    for study,(summary,_) in grids.items():
        for fit in summary['fits']:
            t,x,z=epoch_values(study,fit)
            for kind,values in (('physical',x),('innovation',z)):
                d=analysis.describe(t,values)
                common=dict(study=study,identity=fit['identity'],model=fit['model'],status=saved.fit_status(fit),
                    kind=kind,gain_percent=fit['fixed_z_gain_percent'],bias_dph=fit['fixed_z_bias_dph'])
                d.update(common);curves[study,kind,fit['model'],common['gain_percent'],common['bias_dph']]=d
                compact={k:v for k,v in d.items() if k not in ('lags','spectrum')}
                compact['spectrum_info']=({k:v for k,v in d['spectrum'].items() if k not in ('frequencies_hz','density')}
                                          if d['spectrum'] else None)
                series.append(compact)
                for j,a in enumerate(d['axes']):
                    axis_rows.append(dict(**common,**a,epochs=d['epochs'],duration_s=d['duration_s'],
                        lag1=d['lags'][1]['correlation'][j][j],lag10=d['lags'][10]['correlation'][j][j],
                        lag30=d['lags'][30]['correlation'][j][j],lag60=d['lags'][60]['correlation'][j][j]))
    artifacts=['axes.csv','lags.csv.gz','spectra.csv.gz','cross-axis.csv']
    table('axes.csv',axis_rows)
    def lag_rows():
        for v in curves.values():
            for lag in v['lags']:
                for i,a in enumerate(analysis.AXES):
                    for j,b in enumerate(analysis.AXES):
                        yield dict(identity=v['identity'],study=v['study'],model=v['model'],status=v['status'],kind=v['kind'],
                            from_axis=a,to_axis=b,lag_epochs=lag['lag_epochs'],pairs=lag['pairs'],
                            min_lag_s=lag['min_lag_s'],median_lag_s=lag['median_lag_s'],max_lag_s=lag['max_lag_s'],
                            covariance=lag['covariance'][i][j],correlation=lag['correlation'][i][j])
    table('lags.csv.gz',lag_rows(),True)
    def spectral_rows():
        for v in curves.values():
            s=v['spectrum']
            if s is not None:
                for f,density in zip(s['frequencies_hz'],s['density']):
                    for i,a in enumerate(analysis.AXES):
                        yield dict(identity=v['identity'],study=v['study'],model=v['model'],status=v['status'],kind=v['kind'],
                            axis=a,frequency_hz=f,density=density[i],resolution_hz=s['resolution_hz'])
    table('spectra.csv.gz',spectral_rows(),True)
    table('cross-axis.csv',(dict(identity=v['identity'],study=v['study'],model=v['model'],status=v['status'],kind=v['kind'],
        from_axis=a,to_axis=b,covariance=v['covariance'][i][j],correlation=v['correlation'][i][j])
        for v in curves.values() for i,a in enumerate(analysis.AXES) for j,b in enumerate(analysis.AXES)))
    names,mpl_version=figures(curves);artifacts+=names
    out=dict(version=analysis.VERSION,saved_fits=81,unique_recordings=2,series=series,
        optimizer_starts=0,native_predictions=0,covariance_calibrated=False,scientific_decision='abstain')
    (HERE/'summary.json').write_text(json.dumps(out,sort_keys=True,indent=2,allow_nan=False)+'\n');artifacts.append('summary.json')
    text=['# Are the remaining track errors independent?','',
        '**The saved errors remain correlated after the current whitening. A shared error model needs further qualification.**',
        'This audit does not alter the observed model separation, any convergence label or any scientific decision.',
        '', 'An IMU (inertial measurement unit) measures turning and acceleration. This report examines saved position errors',
        'from 81 fits of two survey-grade IMU recordings, not 81 independent flights. The first two grids reuse October 5;',
        'the third uses the preselected September 24 stretch. Each spans roughly seven minutes.',
        '', '## Correlation after whitening','',
        'The table summarizes completed specified-field globe fits across their fixed Z calibration variants.',
        'The two unfinished September 24 fits remain in the detailed tables, with their original status.',
        '', '| Grid / innovation channel | Completed variants | Median RMS | Lag 1 / 10 / 60 seconds | Power at periods ≥60 seconds |',
        '|---|---:|---:|---:|---:|']
    for study in INPUTS:
        for axis in analysis.AXES:
            rows=[r for r in axis_rows if r['study']==study and r['model']=='sphere_rotating' and r['status']=='converged'
                  and r['kind']=='innovation' and r['axis']==axis]
            med=lambda k:float(np.median([r[k] for r in rows]))
            text.append(f"| {study} / {axis} | {len(rows)} | {med('rms'):.4f} | {med('lag1'):.3f} / {med('lag10'):.3f} / {med('lag60'):.3f} | {100*med('period_ge_60s_power_fraction'):.1f}% |")
    text+=['', 'Whitening expresses errors relative to the assumed covariance. Its channel labels follow the saved factorization;',
        'they are not three new independent physical sensors. Small innovation RMS values do not establish GPS precision',
        'or calibrated likelihoods. Correlation can reflect receiver error, IMU error, fitted calibration and model mismatch.',
        '', '![Autocorrelation](autocorrelation.svg)','',
        'Lines are medians over calibration-grid variants. Shaded ranges show sensitivity to those choices, not confidence intervals.',
        'Each grid is kept separate. All physical models are included in the detailed tables; their mismatches are not pooled as noise.',
        '', '## Cross-axis and slow behavior','', '![Cross-axis correlation](cross-axis.svg)','',
        'These matrices use the predeclared zero-gain/zero-offset grid anchor. The physical residuals share one north/east/up',
        'conversion for all models: latitude and longitude errors use the receiver’s latitude, height and a 6,378,137 m radius.',
        'The covariance is centered over the complete record, so constant residual means are reported separately.',
        '', '![Spectra](spectra.svg)','',
        'The spectra remove the mean and apply a Hann window; no linear trend is removed. The dashed line marks a',
        '60-second period. Positive-frequency band power excludes DC and is a fraction of the displayed spectrum,',
        'not an estimate of sensor drift. These approximately seven-minute records offer only a few minute-scale cycles.',
        'Longer-than-record periods, multi-hour drift and unique correlation time scales cannot be established here.',
        '', '## Methods and scope','',
        'Lag products are centered using the whole-record mean and divided by the total epoch count, including at nonzero lag.',
        'Every lag retains pair count and actual minimum/median/maximum elapsed times. All series retain their saved timestamps.',
        'Uniform cadence is checked within 1 part per million (at least 1 ns); irregular series receive lag diagnostics but no FFT.',
        'There is no interpolation or resampling. The one-sided periodogram uses interval/window normalization verified by',
        'frequency and time-domain energy controls, for both odd and even sample counts.',
        '', 'Selected receiver epochs preserve position/time but no fix-quality or precision fields. This audit does not invent',
        'formal receiver covariance. Empirical fitted residual covariance is not uniquely the receiver’s measurement covariance,',
        'and these descriptive checks do not prove stationarity. Group1 fused navigation supplies no independent inertial evidence.',
        '', 'Detailed outputs: [axis summaries](axes.csv), [cross-axis matrices](cross-axis.csv),',
        '[dense lag matrices](lags.csv.gz) and [spectral bins](spectra.csv.gz). Failures remain explicitly labeled.',
        'All input hashes, completion receipts and saved epoch RMS/objectives are checked before analysis.',
        'This work adds **zero optimizer starts and zero native predictions**.',
        '', '## Next step','',
        'The [shared error-model plan](ERROR_MODEL_PLAN.md) describes a covariance with white error, correlated error',
        'and cross-axis terms. Its specification must be justified or estimated on designated development data, then frozen',
        'identically for all physical candidates and tested with blocked predictions. It is not fitted or deployed here.',
        'A new observed-data comparison needs separate numerical qualification and a finite allowance.',
        'The globe/flat hierarchy and distinction between a measured background field and its physical cause remain unchanged.',
        '', '## Reproduce','', '```sh',
        'env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 ~/venv/bin/python docs/ilvis0-residual-covariance-20261012/build_report.py',
        '```','']
    (HERE/'README.md').write_text('\n'.join(text));artifacts.append('README.md')
    dependencies=[Path(__file__).resolve(),*[Path(m.__file__).resolve() for m in (analysis,grid_audit,profiles,diagnosis,saved)],
                  ROOT/'analysis/tests/test_ilvis0_residual_covariance.py',ROOT/'analysis/tests/test_ilvis0_residual_covariance_report.py']
    receipt=dict(version=analysis.VERSION,optimizer_starts=0,native_predictions=0,
        environment=dict(runtime.numerical_environment(),matplotlib=mpl_version),
        inputs={str(p.resolve()):sha(p) for d in INPUTS.values()
                for p in (d/'manifest.json',d/'summary.json',d/'completion.json',d/'evidence-receipt.json',d/'selection.json.gz')},
        sources={str(p):sha(p) for p in dependencies},artifacts={n:sha(HERE/n) for n in artifacts})
    receipt['inputs'][str(PLAN)]=sha(PLAN)
    (HERE/'report-receipt.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print('Audited 81 saved fits / 162 residual streams; two recordings; zero fits or native predictions.')


if __name__=='__main__':build()
