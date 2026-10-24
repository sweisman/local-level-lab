# SPDX-License-Identifier: AGPL-3.0-or-later
"""Reusable descriptive saved-error statistics, without fitting or propagation.

Physical prediction errors combine receiver, IMU, calibration and model effects.
Their correlations are not a receiver-noise estimate or a confidence interval.
"""
import math

LAGS=(1,5,10,30,60)
AXES=('north','east','up')


def _arrays(times,errors):
    import numpy as np
    t,e=np.asarray(times,float),np.asarray(errors,float)
    if (t.ndim!=1 or len(t)<3 or e.shape!=(len(t),3)
            or not np.all(np.isfinite(t)) or not np.all(np.isfinite(e)) or np.any(np.diff(t)<=0)):
        raise ValueError('complete finite three-axis errors and strictly ordered epochs required')
    return t,e


def _spectrum(t,x,units):
    import numpy as np
    step=np.diff(t);dt=float(np.median(step))
    if np.max(abs(step-dt))>1e-9*max(1.,dt):
        return dict(supported=False,reason='nonuniform sampling; no interpolation',units_squared=units+' squared')
    n=len(x);transform=np.fft.rfft(x-x.mean());power=abs(transform)**2/n**2
    if n%2==0:power[1:-1]*=2
    else:power[1:]*=2
    frequency=np.fft.rfftfreq(n,d=dt)
    bands={
        'longer_than_60_s':float(power[(frequency>0)&(frequency<1/60)].sum()),
        '10_to_60_s':float(power[(frequency>=1/60)&(frequency<=.1)].sum()),
        'shorter_than_10_s':float(power[frequency>.1].sum())}
    total=float(power.sum())
    return dict(supported=True,method='centred one-sided Fourier variance',sample_interval_s=dt,
        units_squared=units+' squared',total_variance=total,zero_frequency_variance=float(power[0]),bands=bands,
        fraction_longer_than_60_s=bands['longer_than_60_s']/total if total else None)


def _describe(t,e,units):
    import numpy as np
    from lll.ilvis0_residuals import distribution,autocorrelation
    centred=e-e.mean(axis=0);covariance=centred.T@centred/len(t);std=np.sqrt(np.diag(covariance))
    correlation=[[float(covariance[i,j]/(std[i]*std[j])) if std[i] and std[j] else None for j in range(3)] for i in range(3)]
    axes=[]
    for j,name in enumerate(AXES):
        x=e[:,j];lags=[]
        for lag in LAGS:
            delta=t[lag:]-t[:-lag] if lag<len(t) else None
            lags.append(dict(lag_epochs=lag,pairs=max(0,len(t)-lag),value=autocorrelation(x,lag),
                min_lag_s=float(delta.min()) if delta is not None else None,
                median_lag_s=float(np.median(delta)) if delta is not None else None,
                max_lag_s=float(delta.max()) if delta is not None else None))
        # The shared helper's arbitrary threshold of three units is not a
        # three-sigma test and is deliberately absent from this description.
        stats={key:value for key,value in distribution(x).items() if key!='fraction_absolute_gt_3'}
        axes.append(dict(axis=name,distribution=stats,autocorrelation=lags,spectrum=_spectrum(t,x,units)))
    step=np.diff(t)
    return dict(epochs=len(t),units=units,first_time_s=float(t[0]),last_time_s=float(t[-1]),
        sample_intervals_s=dict(min=float(step.min()),median=float(np.median(step)),max=float(step.max())),
        covariance=covariance.tolist(),covariance_units=units+' squared',correlation=correlation,axes=axes)


def section(times,errors):
    import numpy as np
    t,e=_arrays(times,errors)
    try:
        with np.errstate(over='raise',invalid='raise',divide='raise'):
            result=_describe(t,e,'m')
            differences=np.diff(e,axis=0)/np.diff(t)[:,None]
            result['first_differences']=_describe((t[1:]+t[:-1])/2,differences,'m/s')
    except (FloatingPointError,OverflowError) as error:
        raise ValueError('unrepresentable descriptive statistic; inputs were not repaired') from error
    return result


def summarize(times,errors,*,training_epochs):
    from lll.airquantumgrav_diagnosis import fixed_blocks
    t,e=_arrays(times,errors);cut=training_epochs
    if type(cut) is not int or not 3<=cut<=len(t)-3:raise ValueError('separate complete training and prediction sections required')
    blocks=fixed_blocks(t,e,cut)
    return dict(training=section(t[:cut],e[:cut]),prediction=section(t[cut:],e[cut:]),blocks=blocks['blocks'],
        epochs=len(t),training_epochs=cut,prediction_epochs=len(t)-cut,forecasts_changed=False,
        blocks_are_independent_trials=False,error_law_calibrated=False,effective_sample_size=None,
        raw_receiver_or_imu_noise_estimated=False,scientific_decision='abstain')


def error_growth_figure(curves,*,training_epochs):
    """Plot unchanged selected forecasts; selection belongs to the frozen parent."""
    import io
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    labels=dict(sphere_rotating='Globe + specified field',sphere_still='Globe + zero field',flat_still='Tested disc')
    colors=dict(sphere_rotating='#176aa8',sphere_still='#bd6d00',flat_still='#a52958')
    fig,axes=plt.subplots(2,1,figsize=(11,8),sharex=True)
    reference=None
    for curve in curves:
        t,e=_arrays(curve['times_s'],curve['errors_neu_m']);spec=curve['spec']
        if reference is not None and not np.array_equal(t,reference):raise ValueError('identical saved query times required')
        reference=t;minutes=(t-t[0])/60
        label=f"{labels[spec['model']]}; {'profiled' if spec['profile'] else 'zero'} removal; {'short' if spec['policy_id']=='reported-short-v1' else 'persistent'} errors"
        for axis,y in zip(axes,(np.hypot(e[:,0],e[:,1]),e[:,2]),strict=True):
            axis.plot(minutes,y,color=colors[spec['model']],linestyle='--' if spec['profile'] else '-',
                alpha=.85 if spec['policy_id']=='reported-short-v1' else .45,label=label)
    if reference is None or type(training_epochs) is not int or not 0<training_epochs<len(reference):
        raise ValueError('selected saved curves and a supported split required')
    for axis in axes:
        axis.set_yscale('symlog',linthresh=1.);axis.grid(alpha=.2)
        axis.axvline((reference[training_epochs]-reference[0])/60,color='black',linestyle=':')
    axes[0].set_ylabel('Horizontal error (m)');axes[1].set_ylabel('Height error (m)')
    axes[1].set_xlabel('Minutes from first receiver query');axes[0].legend(fontsize=6,ncol=2)
    fig.suptitle('Saved prediction errors; dotted line begins prediction; symmetric log scale beyond 1 m')
    fig.tight_layout();buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=160);plt.close(fig)
    return buffer.getvalue()
