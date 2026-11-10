# SPDX-License-Identifier: AGPL-3.0-or-later
"""Add declared persistent receiver errors to a fixed joint-noise history."""


class ReceiverAugmentation:
    """Streaming independent receiver offsets, drift and stationary OU errors.

    Native states retain their packet-endpoint clock; receiver states use the
    observation clock. This is a joint-observation transition, so the current
    receiver innovation is shared by the observation and receiver endpoint.
    The given white observation loading is checked and preserved, not added
    twice. No error parameters are estimated and no data are read here.
    """

    def __init__(self, steps, *, times, spec, transforms, state_dimension,
                 initial_loading, maximum_epochs, receiver_epochs=None):
        import numpy as np
        from .covariance_roots import loading_root
        from .ilvis0_error_model import Spec
        from .measurement_noise import _root
        t = np.array(times, dtype=float, copy=True)
        if (type(maximum_epochs) is not int or maximum_epochs < 1 or t.ndim != 1
                or not 1 <= len(t) <= maximum_epochs or not np.all(np.isfinite(t))
                or np.any(np.diff(t) <= 0) or not isinstance(spec, Spec)
                or type(state_dimension) is not int or not 1 <= state_dimension <= 21):
            raise ValueError('bounded ordered receiver epochs, explicit Spec and native state required')
        n = len(t); k = state_dimension; r = 6+3*len(spec.components)
        if receiver_epochs is None:receiver_epochs=n
        if type(receiver_epochs) is not int or not 1<=receiver_epochs<=n:
            raise ValueError('explicit earlier receiver observation support required')
        self.receiver_epochs=receiver_epochs
        a = np.array(transforms, dtype=float, copy=True)
        if (a.shape != (n, 3, 3) or not np.all(np.isfinite(a))
                or np.any(np.linalg.slogdet(a)[0] == 0)):
            raise ValueError('finite invertible per-epoch receiver transformations required')
        initial = np.array(np.zeros((k, 0)) if initial_loading is None else initial_loading,
            dtype=float, copy=True)
        if (initial.ndim != 2 or initial.shape[0] != k or initial.shape[1] > 40
                or not np.all(np.isfinite(initial))):
            raise ValueError('complete finite native initial loading required')
        roots = [_root(spec.offset), _root(spec.drift)]
        roots += [_root(covariance) for _, covariance in spec.components]
        combined = np.zeros((k+r, initial.shape[1]+r)); combined[:k, :initial.shape[1]] = initial
        for j, root in enumerate(roots):
            combined[k+3*j:k+3*j+3, initial.shape[1]+3*j:initial.shape[1]+3*j+3] = root
        self.initial_loading = loading_root(combined, maximum_rows=33, maximum_columns=64)
        for value in (t, a, self.initial_loading):
            value.flags.writeable = False
        self.times = t; self.transforms = a; self.spec = spec; self.roots = roots
        self.native_dimension = k; self.receiver_dimension = r; self.state_dimension = k+r
        self._steps = iter(steps); self._used = False
        self.error_law_calibrated = False; self.parameter_uncertainty_included = False

    def steps(self):
        import numpy as np
        from .covariance_roots import loading_root
        from .ilvis0_error_model import factor
        if self._used:
            raise ValueError('receiver augmentation can be consumed only once')
        self._used = True
        k = self.native_dimension; r = self.receiver_dimension
        def matrix(value, shape=None, rows=None):
            a = np.asarray(value, dtype=float)
            if (a.ndim != 2 or not np.all(np.isfinite(a))
                    or (shape is not None and a.shape != shape)
                    or (rows is not None and (a.shape[0] != rows or a.shape[1] > 40))):
                raise ValueError('finite aligned joint-noise step matrices required')
            return a
        for i, t in enumerate(self.times):
            try:
                step = next(self._steps)
            except StopIteration as error:
                raise ValueError('complete native step history required') from error
            keys = {'transition', 'process_loading', 'observation', 'white_loading',
                'observation_process_loading'}
            if not isinstance(step, dict) or set(step) != keys:
                raise ValueError('explicit shared-noise observation step required')
            f = matrix(step['transition'], shape=(k, k))
            b = matrix(step['process_loading'], rows=k)
            h = matrix(step['observation'], shape=(3, k))
            d = matrix(step['observation_process_loading'], shape=(3, b.shape[1]))
            white = matrix(step['white_loading'], rows=3)
            actual = white@white.T;expected = self.transforms[i]@self.spec.white@self.transforms[i].T
            factor(actual)
            scales = np.sqrt(np.diag(expected))
            if np.max(abs((actual-expected)/scales[:, None]/scales[None, :])) > 1e-11:
                raise ValueError('native white covariance differs from the declared receiver law')
            transition = np.eye(k+r); transition[:k, :k] = f
            receiver_loading = np.zeros((r, 3*len(self.spec.components)))
            interval = 0. if i == 0 else t-self.times[i-1]
            for j, (tau, _) in enumerate(self.spec.components):
                sl = slice(6+3*j, 9+3*j)
                transition[k+6+3*j:k+9+3*j, k+6+3*j:k+9+3*j] = np.eye(3)*np.exp(-interval/tau)
                receiver_loading[sl, 3*j:3*j+3] = self.roots[j+2]*np.sqrt(-np.expm1(-2*interval/tau))
            u = (t-self.spec.drift_origin_s)/self.spec.drift_span_s
            observe = np.column_stack([np.eye(3), u*np.eye(3)]+[np.eye(3)]*len(self.spec.components))
            observe = self.transforms[i]@observe
            if i>=self.receiver_epochs:observe[:]=0.
            observation = np.column_stack((h, observe@transition[k:, k:]))
            loading = np.zeros((k+r, b.shape[1]+receiver_loading.shape[1]))
            loading[:k, :b.shape[1]] = b
            loading[k:, b.shape[1]:] = receiver_loading
            observed_loading = np.column_stack((d, observe@receiver_loading))
            # Compress the joint loading; separate QR factorizations would
            # rotate shared drivers differently and corrupt cross-covariance.
            joint = loading_root(np.vstack((loading, observed_loading)),
                maximum_rows=36, maximum_columns=64)
            yield dict(transition=transition, process_loading=joint[:k+r],
                observation=observation, observation_process_loading=joint[k+r:],
                white_loading=white.copy() if i<self.receiver_epochs else np.zeros_like(white))
        try:
            next(self._steps)
        except StopIteration:
            pass
        else:
            raise ValueError('extra native steps outside receiver epoch support')
