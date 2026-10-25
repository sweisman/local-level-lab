# SPDX-License-Identifier: AGPL-3.0-or-later
"""Explicit synthetic receiver errors and integrated sensor noise.

No hardware defaults, noise estimation, fitting, interpolation or measurements
are provided here. Callers freeze parameters, seed, software environment and
finite work allowances before drawing. White sensor PSD has units rate²·s;
stationary bias covariance has units rate². Returned sensor errors are increments.
"""
import hashlib
import math

VERSION = 'measurement-noise-v1'


def stream(seed, label):
    """A named PCG64 stream, independent of global RNG and other component sizes."""
    import numpy as np
    if (type(seed) is not int or not 0 <= seed < 2**64 or not isinstance(label, str)
            or not label or len(label) > 128 or not label.isascii()):
        raise ValueError('explicit uint64 seed and nonempty ASCII stream label required')
    key = hashlib.sha256((VERSION + ':' + label).encode()).digest()
    entropy = [seed & 0xffffffff, seed >> 32]
    entropy += [int.from_bytes(key[i:i+4], 'little') for i in range(0, 32, 4)]
    return np.random.Generator(np.random.PCG64(np.random.SeedSequence(entropy)))


def _times(values, cap, *, increments=False):
    import numpy as np
    result = np.array(values, dtype=float, copy=True)
    if (type(cap) is not int or cap < 1 or result.ndim != 1 or not 1 <= len(result) <= cap
            or not np.all(np.isfinite(result))
            or (np.any(result <= 0) if increments else np.any(np.diff(result) <= 0))):
        raise ValueError('finite ordered epochs/positive intervals within an explicit work allowance required')
    return result


def _root(values):
    """Permit zero/rank-deficient components; never clip negative eigenvalues."""
    import numpy as np
    from lll.ilvis0_error_model import symmetric, factor
    matrix = symmetric(values, size=3)
    if not matrix.any():
        return np.zeros((3, 3))
    eigenvalues, vectors = np.linalg.eigh(matrix)
    if np.any(eigenvalues < 0):
        raise ValueError('nonnegative covariance required; no eigenvalue repair')
    if np.all(eigenvalues > 0):
        return factor(matrix)
    return vectors * np.sqrt(eigenvalues)


def white_increments(dt, psd, *, rng, maximum_steps):
    """Integrate continuous white rate noise over the actual adjacent intervals."""
    import numpy as np
    intervals = _times(dt, maximum_steps, increments=True)
    root = _root(psd)
    result = (rng.standard_normal((len(intervals), 3)) @ root.T) * np.sqrt(intervals[:, None])
    if not np.all(np.isfinite(result)):
        raise ValueError('unrepresentable white increments')
    return result


def ou_moments(dt, *, tau_s):
    """Exact OU endpoint/integral innovations for unit stationary variance.

    The integral innovation is correlated with the endpoint innovation.
    A power series avoids cancellation when dt is much shorter than tau.
    """
    import numpy as np
    intervals = np.asarray(dt, float)
    if (intervals.ndim != 1 or not len(intervals) or not np.all(np.isfinite(intervals))
            or np.any(intervals <= 0) or type(tau_s) not in (int, float)
            or not math.isfinite(tau_s) or tau_s <= 0):
        raise ValueError('positive finite intervals and correlation time required')
    x = intervals / tau_s
    a = -np.expm1(-x)
    state_variance = -np.expm1(-2*x)
    integral_scaled = 2*x - 2*a - a*a
    small = x < .05
    if np.any(small):
        u = x[small]
        series = np.zeros_like(u)
        for k in range(3, 16):
            series += (4*(-1)**k - (-2)**k) * u**k / math.factorial(k)
        integral_scaled[small] = series
    result = dict(rho=np.exp(-x), state_variance=state_variance,
        state_integral_covariance=tau_s*a*a, integral_variance=tau_s*tau_s*integral_scaled)
    if any(not np.all(np.isfinite(v)) for v in result.values()):
        raise ValueError('unrepresentable OU moments')
    return result


def ou_increments(dt, covariance, *, tau_s, rng, maximum_steps, initial=None):
    """Stationary OU bias integrated exactly, with optional uninterrupted continuation."""
    import numpy as np
    intervals = _times(dt, maximum_steps, increments=True)
    root = _root(covariance)
    moments = ou_moments(intervals, tau_s=tau_s)
    variance = moments['state_variance']
    lower = np.sqrt(variance)
    loading = moments['state_integral_covariance'] / lower
    remainder = moments['integral_variance'] - loading*loading
    if np.any(variance <= 0) or np.any(remainder <= 0):
        raise ValueError('OU covariance is numerically unsupported; no variance repair')
    if initial is not None:
        initial = np.array(initial, float, copy=True)
        if initial.shape != (3,) or not np.all(np.isfinite(initial)):
            raise ValueError('finite three-axis continuing bias state required')
    states = np.empty((len(intervals)+1, 3))
    states[0] = rng.standard_normal(3) @ root.T if initial is None else initial
    draws = rng.standard_normal((len(intervals), 2, 3)) @ root.T
    output = np.empty((len(intervals), 3))
    for i, interval in enumerate(intervals):
        rho = moments['rho'][i]
        # expm1 retains the conditional mean at very short intervals.
        mean_loading = -tau_s*np.expm1(-interval/tau_s)
        output[i] = mean_loading*states[i] + loading[i]*draws[i, 0] + np.sqrt(remainder[i])*draws[i, 1]
        states[i+1] = rho*states[i] + lower[i]*draws[i, 0]
    if not np.all(np.isfinite(states)) or not np.all(np.isfinite(output)):
        raise ValueError('unrepresentable OU path')
    return dict(increments=output, states=states, initial_state_sampled=initial is None)


def receiver_errors(times, spec, *, seed, maximum_epochs, transforms=None):
    """Draw the supplied receiver law independently of its whitening operator.

    Every component has a separate stream. Extending later times cannot change
    an earlier prefix. Drift uses the Spec's fixed origin, never the subset mean.
    """
    import numpy as np
    from lll.ilvis0_error_model import Spec
    t = _times(times, maximum_epochs)
    if not isinstance(spec, Spec):
        raise ValueError('explicit receiver error Spec required')
    roots = dict(white=_root(spec.white), offset=_root(spec.offset), drift=_root(spec.drift))
    components = [(tau, _root(covariance)) for tau, covariance in spec.components]
    if transforms is not None:
        transforms = np.asarray(transforms, float)
        if (transforms.shape != (len(t), 3, 3) or not np.all(np.isfinite(transforms))
                or np.any(np.linalg.slogdet(transforms)[0] == 0)):
            raise ValueError('finite invertible per-epoch transforms required')
    result = stream(seed, 'receiver.white').standard_normal((len(t), 3)) @ roots['white'].T
    result += stream(seed, 'receiver.offset').standard_normal(3) @ roots['offset'].T
    drift = stream(seed, 'receiver.drift').standard_normal(3) @ roots['drift'].T
    result += ((t-spec.drift_origin_s)/spec.drift_span_s)[:, None] * drift
    for j, (tau, root) in enumerate(components):
        rng = stream(seed, 'receiver.ou.' + str(j))
        draws = rng.standard_normal((len(t), 3)) @ root.T
        state = draws[0]
        result[0] += state
        for i in range(1, len(t)):
            x = (t[i]-t[i-1])/tau
            state = np.exp(-x)*state + np.sqrt(-np.expm1(-2*x))*draws[i]
            result[i] += state
    if transforms is not None:
        result = np.einsum('nij,nj->ni', transforms, result)
    if not np.all(np.isfinite(result)):
        raise ValueError('unrepresentable receiver noise')
    return result


def perturb_imu(theta, dv, dt, *, seed, gyro_white_psd, accel_white_psd,
                gyro_bias_covariance, accel_bias_covariance, gyro_bias_tau_s,
                accel_bias_tau_s, maximum_steps):
    """Add independent body-axis noise to generated angle/velocity increments.

    Covariances and correlation times are required; they are not inferred from
    an instrument name or a model preference. No constant calibration is changed.
    """
    import numpy as np
    intervals = _times(dt, maximum_steps, increments=True)
    theta, dv = (np.asarray(v, float) for v in (theta, dv))
    if (theta.shape != (len(intervals), 3) or dv.shape != theta.shape
            or not np.all(np.isfinite(theta)) or not np.all(np.isfinite(dv))):
        raise ValueError('complete finite angle/velocity increments required')
    # Validate every component before consuming any random stream.
    for covariance in (gyro_white_psd, accel_white_psd, gyro_bias_covariance, accel_bias_covariance):
        _root(covariance)
    for tau in (gyro_bias_tau_s, accel_bias_tau_s):
        ou_moments(intervals[:1], tau_s=tau)
    noise = {}
    for name, psd, covariance, tau in (
            ('gyro', gyro_white_psd, gyro_bias_covariance, gyro_bias_tau_s),
            ('accel', accel_white_psd, accel_bias_covariance, accel_bias_tau_s)):
        white = white_increments(intervals, psd, rng=stream(seed, 'imu.'+name+'.white'), maximum_steps=maximum_steps)
        bias = ou_increments(intervals, covariance, tau_s=tau,
            rng=stream(seed, 'imu.'+name+'.bias'), maximum_steps=maximum_steps)
        noise[name] = dict(white_increments=white, bias_increments=bias['increments'], bias_states=bias['states'])
    observed_theta = theta + noise['gyro']['white_increments'] + noise['gyro']['bias_increments']
    observed_dv = dv + noise['accel']['white_increments'] + noise['accel']['bias_increments']
    if not np.all(np.isfinite(observed_theta)) or not np.all(np.isfinite(observed_dv)):
        raise ValueError('unrepresentable noisy IMU inputs')
    return dict(theta=observed_theta, dv=observed_dv, dt=intervals, noise=noise)


def perturb_linear_rate_points(theta,dv,dt,*,seed,gyro_point_covariance,accel_point_covariance,
        gyro_bias_covariance,accel_bias_covariance,gyro_bias_tau_s,accel_bias_tau_s,
        maximum_steps,reserve):
    """Add trapezoid-integrated point errors to generated clean increments.

    Point covariance has squared-rate units. Bias is sampled at endpoints;
    this is deliberately distinct from the exact continuous OU interval integral.
    This generator does not use the covariance operator's transition/loading.
    No observed measurements are interpolated or repaired.
    """
    import numpy as np
    intervals=_times(dt,maximum_steps,increments=True)
    theta,dv=(np.asarray(a,float) for a in (theta,dv));n=len(intervals)
    if (theta.shape!=(n,3) or dv.shape!=theta.shape
            or not np.all(np.isfinite(theta)) or not np.all(np.isfinite(dv))
            or not callable(reserve) or type(seed) is not int or not 0<=seed<2**64):
        raise ValueError('finite generated increments, uint64 seed and prepaid variate callback required')
    roots=tuple(_root(c) for c in (gyro_point_covariance,accel_point_covariance,
        gyro_bias_covariance,accel_bias_covariance))
    taus=(gyro_bias_tau_s,accel_bias_tau_s)
    for tau in taus:ou_moments(intervals[:1],tau_s=tau)
    reserve(noise_normal_variates=12*(n+1))
    noise={}
    for i,name in enumerate(('gyro','accel')):
        white=stream(seed,'imu.'+name+'.rate_points.white').standard_normal((n+1,3))@roots[i].T
        draws=stream(seed,'imu.'+name+'.rate_points.bias').standard_normal((n+1,3))@roots[i+2].T
        bias=np.empty_like(draws);bias[0]=draws[0]
        for j,interval in enumerate(intervals):
            x=interval/taus[i]
            bias[j+1]=np.exp(-x)*bias[j]+np.sqrt(-np.expm1(-2*x))*draws[j+1]
        noise[name]=dict(white_points=white,bias_states=bias,
            white_increments=(white[:-1]+white[1:])*(intervals[:,None]/2),
            bias_increments=(bias[:-1]+bias[1:])*(intervals[:,None]/2))
    observed_theta=theta+noise['gyro']['white_increments']+noise['gyro']['bias_increments']
    observed_dv=dv+noise['accel']['white_increments']+noise['accel']['bias_increments']
    if not np.all(np.isfinite(observed_theta)) or not np.all(np.isfinite(observed_dv)):
        raise ValueError('unrepresentable linear-rate point inputs')
    return dict(theta=observed_theta,dv=observed_dv,dt=intervals,noise=noise,
        input_error_law='linear_rate_points')
