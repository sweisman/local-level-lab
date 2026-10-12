# SPDX-License-Identifier: AGPL-3.0-or-later
"""Descriptive dependence in saved residuals; no covariance calibration or refits."""
import numpy as np

VERSION='ilvis0-saved-residual-covariance-v1'
AXES=('north','east','up')


def correlation(covariance,variance):
    denominator=np.sqrt(np.outer(variance,variance))
    return [[float(covariance[i,j]/denominator[i,j]) if denominator[i,j]>0 else None
             for j in range(3)] for i in range(3)]


def describe(times,values,*,max_lag=60):
    t=np.asarray(times,float);x=np.asarray(values,float)
    if (t.ndim!=1 or len(t)<3 or x.shape!=(len(t),3) or
        not np.all(np.isfinite(t)) or not np.all(np.isfinite(x)) or
        np.any(np.diff(t)<=0) or not isinstance(max_lag,int) or isinstance(max_lag,bool) or max_lag<0):
        raise ValueError('finite aligned residuals, increasing epochs and nonnegative integer lag required')
    n=len(t);step=np.diff(t);cadence=float(np.median(step))
    centered=x-x.mean(axis=0)
    covariance=centered.T@centered/n;variance=np.diag(covariance)
    if not np.all(np.isfinite(covariance)):raise ValueError('nonfinite covariance')
    lags=[]
    for lag in range(min(max_lag,n-1)+1):
        if lag:
            c=centered[:-lag].T@centered[lag:]/n
            elapsed=t[lag:]-t[:-lag]
        else:
            c=covariance;elapsed=np.zeros(n)
        lags.append(dict(lag_epochs=lag,pairs=n-lag,min_lag_s=float(elapsed.min()),
            median_lag_s=float(np.median(elapsed)),max_lag_s=float(elapsed.max()),
            covariance=c.tolist(),correlation=correlation(c,variance)))
    uniform=bool(np.max(abs(step-cadence))<=max(1e-9,1e-6*cadence))
    spectrum=None;status='irregular_cadence_not_resampled'
    axes=[];relative_t=t-t.mean()
    for j,name in enumerate(AXES):
        axes.append(dict(axis=name,mean=float(x[:,j].mean()),rms=float(np.sqrt(np.mean(x[:,j]**2))),
            centered_rms=float(np.sqrt(variance[j])),linear_slope_per_s=float(relative_t@centered[:,j]/(relative_t@relative_t)),
            period_ge_60s_power_fraction=None))
    if uniform and n>=8:
        window=np.hanning(n);normalization=float(window@window)
        frequency=np.fft.rfftfreq(n,cadence)
        density=abs(np.fft.rfft(centered*window[:,None],axis=0))**2*cadence/normalization
        density[1:(-1 if n%2==0 else None)]*=2
        positive=frequency>0;low=positive&(frequency<=1/60.)
        for j in range(3):
            total=float(density[positive,j].sum())
            if total>0 and np.any(low):
                axes[j]['period_ge_60s_power_fraction']=float(density[low,j].sum()/total)
        spectrum=dict(frequencies_hz=frequency.tolist(),density=density.tolist(),
            resolution_hz=1/(n*cadence),lowest_positive_hz=float(frequency[1]),
            maximum_bin_hz=float(frequency[-1]),period_ge_60s_bin_count=int(np.sum(low)),
            method='one_sided_hann_periodogram_global_mean_removed_no_linear_detrend',
            dc_excluded_from_band_fraction=True)
        status='uniform_cadence_hann_periodogram'
    elif uniform:status='too_few_epochs_for_spectrum'
    return dict(version=VERSION,epochs=n,duration_s=float(t[-1]-t[0]),
        median_cadence_s=cadence,min_cadence_s=float(step.min()),max_cadence_s=float(step.max()),
        spectral_status=status,covariance=covariance.tolist(),correlation=correlation(covariance,variance),
        covariance_normalization='centered_product_sum_divided_by_total_epochs',
        axes=axes,lags=lags,spectrum=spectrum,resampled=False,
        covariance_calibrated=False,scientific_decision='abstain')
