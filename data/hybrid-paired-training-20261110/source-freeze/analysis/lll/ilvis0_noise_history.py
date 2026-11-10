# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fixed-calibration packet noise and native trajectory error propagation.

No sensor defaults, original reads, fitting or estimated confidence are supplied.
The caller supplies a frozen measurement-error law and finite native allowance.
"""
from functools import lru_cache


class PacketNoise:
    """Exact raw increment/bias-endpoint Gaussian loading for an OU bias law."""

    def __init__(self, *, gyro_white_psd, accel_white_psd, gyro_bias_covariance,
                 accel_bias_covariance, gyro_bias_tau_s, accel_bias_tau_s):
        from .measurement_noise import _root, ou_moments
        self.roots = tuple(_root(a) for a in (gyro_white_psd, accel_white_psd,
            gyro_bias_covariance, accel_bias_covariance))
        self.taus = (gyro_bias_tau_s, accel_bias_tau_s)
        for tau in self.taus:
            ou_moments([.005], tau_s=tau)
        for root in self.roots:
            root.flags.writeable = False

    @lru_cache(maxsize=32)
    def at(self, dt):
        """Return increment6/endpoint6 loading, bias decay and mean integral6."""
        import numpy as np
        from .covariance_roots import loading_root
        from .measurement_noise import ou_moments
        load = np.zeros((12, 18)); rho = np.empty(6); mean = np.empty(6)
        for i, tau in enumerate(self.taus):
            m = {k: v[0] for k, v in ou_moments([dt], tau_s=tau).items()}
            state = np.sqrt(m['state_variance'])
            coupled = m['state_integral_covariance']/state
            remainder = m['integral_variance']-coupled*coupled
            if state <= 0 or remainder <= 0:
                raise ValueError('unsupported OU interval; no covariance repair')
            sl = slice(3*i, 3*i+3); end = slice(6+3*i, 9+3*i)
            common = slice(6+6*i, 9+6*i); extra = slice(9+6*i, 12+6*i)
            load[sl, sl] = self.roots[i]*np.sqrt(dt)
            load[sl, common] = self.roots[i+2]*coupled
            load[end, common] = self.roots[i+2]*state
            load[sl, extra] = self.roots[i+2]*np.sqrt(remainder)
            rho[sl] = m['rho']
            mean[sl] = -tau*np.expm1(-dt/tau)
        root = loading_root(load, maximum_rows=12, maximum_columns=18)
        for value in (root, rho, mean):
            value.flags.writeable = False
        return root, rho, mean

    def initial_loading(self):
        import numpy as np
        root = np.zeros((15, 6))
        root[9:12, :3] = self.roots[2]
        root[12:15, 3:] = self.roots[3]
        return root


def associate_queries(dt, query_times, *, time_offset_s):
    """Associate queries using the native path's sequential binary64 clock.

    At most one query per packet is supported. Initial-time and out-of-range
    queries fail; they are never discarded, clamped or retimed.
    """
    import numpy as np
    intervals = np.asarray(dt, float); queries = np.asarray(query_times, float)
    if (intervals.ndim != 1 or not len(intervals) or np.any(intervals <= 0)
            or not np.all(np.isfinite(intervals)) or queries.ndim != 1
            or not len(queries) or not np.all(np.isfinite(queries))
            or np.any(np.diff(queries) <= 0) or not np.isfinite(time_offset_s)):
        raise ValueError('finite ordered queries and positive packet intervals required')
    ends = np.empty(len(intervals)); elapsed = 0.
    for i, interval in enumerate(intervals):
        previous = elapsed; elapsed += float(interval); ends[i] = elapsed
        if not np.isfinite(elapsed) or elapsed <= previous:
            raise ValueError('unsupported accumulated binary64 packet clock')
    effective = np.array([float(t)+float(time_offset_s) for t in queries])
    indices = np.searchsorted(ends, effective, side='left')
    if (np.any(effective <= 0) or np.any(effective > elapsed)
            or np.any(np.diff(effective) <= 0) or np.any(np.diff(indices) <= 0)):
        raise ValueError('queries must be inside distinct supported packets')
    starts = np.concatenate(([0.], ends[:-1]))
    fractions = (effective-starts[indices])/intervals[indices]
    if np.any(fractions <= 0) or np.any(fractions > 1+1e-10):
        raise ValueError('unsupported query fraction; no clock repair')
    return indices, fractions


class NativeNoiseHistory:
    """Stream fixed-parameter 15/21-state errors along an unchanged native mean.

    Pose errors are true minus nominal; the six bias coordinates are positive
    raw-sensor errors. Thus the increment and bias corrections have negative
    signs. Receiver observations use native chart coordinates, not metres.
    Callers must supply receiver loadings in that same chart.

    One query per packet is supported. Its partial increment shares the entire
    packet's Gaussian driver with the full endpoint. Every packet, including
    those after the last query, is evaluated. No per-packet matrix history is
    retained. The steps iterator is single-use, including after a failure.
    """

    def __init__(self, *, kernel, coordinates, velocity, rotation, theta, delta_v,
                 dt, query_times, time_offset_s, model, gravity, radius, removal,
                 anchor_height, lever, correction_scales, noise, white_loadings,
                 maximum_packets, maximum_epochs, reserve):
        import numpy as np
        from .linear_point_noise import LinearPointNoise
        self.dt = np.array(dt, dtype=float, copy=True)
        self.queries = np.array(query_times, dtype=float, copy=True)
        if (type(maximum_packets) is not int or type(maximum_epochs) is not int
                or not 1 <= len(self.dt) <= maximum_packets
                or not 1 <= len(self.queries) <= maximum_epochs
                or not isinstance(noise, (PacketNoise, LinearPointNoise)) or not callable(reserve)):
            raise ValueError('explicit bounded packet/query history, noise and work accounting required')
        self.indices, self.fractions = associate_queries(self.dt, self.queries,
            time_offset_s=time_offset_s)
        n = len(self.dt); self.kernel = kernel; self.noise = noise; self.reserve = reserve
        self.hidden_dimension = 12 if isinstance(noise, LinearPointNoise) else 6
        self.state_dimension = 9+self.hidden_dimension
        def array(value, shape, dtype):
            a = np.array(value, dtype=dtype, copy=True, order='C')
            if a.shape != shape or not np.all(np.isfinite(a)):
                raise ValueError('complete finite aligned state, increment and loading arrays required')
            a.flags.writeable = False
            return a
        self.theta = array(theta, (n, 3), np.longdouble)
        self.dv = array(delta_v, (n, 3), np.longdouble)
        self.initial = dict(coordinates=array(coordinates, (3,), np.longdouble),
            velocity=array(velocity, (3,), np.longdouble),
            rotation=array(rotation, (3, 3), np.longdouble))
        self.correction_scales = array(correction_scales, (6,), float)
        if np.any(self.correction_scales <= 0):
            raise ValueError('explicit positive raw-to-corrected sensor scales required')
        self.white = array(white_loadings, (len(self.queries), 3, 3), float)
        from .ilvis0_error_model import factor
        for loading in self.white:
            factor(loading@loading.T)
        # Force validation of the explicit sensor law before any native work.
        for interval in set(self.dt):
            noise.at(float(interval))
        if (type(model) is not int or model not in (0, 1, 2)
                or not np.all(np.isfinite([gravity, radius, removal]))
                or gravity <= 0 or radius <= 0 or not 0 <= removal <= 1):
            raise ValueError('explicit supported candidate and physical scalars required')
        self.fixed = dict(model=model, gravity=np.longdouble(gravity), radius=np.longdouble(radius),
            removal=np.longdouble(removal), anchor_height=anchor_height,
            lever=array(lever, (3,), np.longdouble))
        self.observations = np.empty((len(self.queries), 3), dtype=np.longdouble)
        self.final_state = None; self._used = False
        self.error_law_calibrated = False; self.parameter_uncertainty_included = False

    def steps(self):
        import numpy as np
        from .covariance_roots import loading_root
        from .ilvis0_noise_step import evaluate
        if self._used:
            raise ValueError('native history can be consumed only once')
        self._used = True
        nstate = self.state_dimension; hidden = self.hidden_dimension
        state = self.initial; gap_f = np.eye(nstate); gap_l = np.zeros((nstate, 0)); query = 0
        def reserve(**counts):
            self.reserve(**counts, packet_steps=1)
        def call(interval, theta, dv):
            return evaluate(self.kernel, **state, **self.fixed, theta=theta,
                delta_v=dv, dt=interval, derivatives=True, reserve=reserve)
        for i, interval in enumerate(self.dt):
            packet_l, rho, mean = self.noise.at(float(interval))
            full = call(np.longdouble(interval), self.theta[i], self.dv[i])
            jac = full['state_jacobian']; f = np.zeros((nstate, nstate)); g = np.zeros((nstate, 6+hidden))
            f[:9, :9] = jac[:, :9]
            if mean.ndim == 1:
                f[:9, 9:] = -jac[:, 9:]*((self.correction_scales*mean)[None, :])
            else:
                f[:9, 9:] = -(jac[:, 9:]*self.correction_scales[None, :])@mean
            f[9:, 9:] = np.diag(rho)
            g[:9, :6] = -jac[:, 9:]*self.correction_scales[None, :]
            g[9:, 6:] = np.eye(hidden)
            if query < len(self.indices) and self.indices[query] == i:
                fraction = float(self.fractions[query]); q = full
                if fraction != 1.:
                    part = np.longdouble(fraction)
                    q = call(np.longdouble(interval)*part, self.theta[i]*part, self.dv[i]*part)
                observed = q['observation_jacobian']; h = np.zeros((3, nstate)); d = np.zeros((3, 6+hidden))
                h[:, :9] = observed[:, :9]
                if mean.ndim == 1:
                    h[:, 9:] = -observed[:, 9:]*((self.correction_scales*mean*fraction)[None, :])
                else:
                    h[:, 9:] = -(observed[:, 9:]*((self.correction_scales*fraction)[None, :]))@mean
                d[:, :6] = -observed[:, 9:]*((self.correction_scales*fraction)[None, :])
                self.observations[query] = q['observation']
                step = dict(transition=f@gap_f,
                    process_loading=np.column_stack((f@gap_l, g@packet_l)),
                    observation=h@gap_f,
                    observation_process_loading=np.column_stack((h@gap_l, d@packet_l)),
                    white_loading=self.white[query])
                gap_f = np.eye(nstate); gap_l = np.zeros((nstate, 0)); query += 1
            else:
                gap_f = f@gap_f
                gap_l = loading_root(np.column_stack((f@gap_l, g@packet_l)),
                    maximum_rows=nstate, maximum_columns=64)
                step = None
            state = {key: full[key] for key in ('coordinates', 'velocity', 'rotation')}
            if step is not None:
                yield step
        if query != len(self.queries):
            raise ValueError('incomplete native query history')
        self.final_state = state
