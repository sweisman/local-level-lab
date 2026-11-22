# SPDX-License-Identifier: AGPL-3.0-or-later
"""Earlier-only error contribution diagnostics for the sealed ESA drift replay."""

import argparse
from contextlib import closing
import gzip
import json
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

from . import esa_changing_drift_transfer as parent
from .airquantumgrav_error_policy import reported_covariance
from .ilvis0_control_shards import runtime_environment
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy
from .studies.dependencies import source_closure


PLAN = parent.FOLDER+'ESA_DRIFT_CORRECTION_AUDIT_PLAN.md'
FREEZE = parent.FOLDER+'esa-drift-correction-audit-freeze.json'
RESULT = parent.FOLDER+'esa-drift-correction-audit-result.json'
DRIVERS = {'inertial_acceleration': (1, 'acceleration_psd'),
           'inertial_jerk': (2, 'jerk_psd'), 'inertial_snap': (3, 'snap_psd'),
           'receiver_walk': (0, 'receiver_random_walk_psd')}
FACTORIALS = np.array([1., 1., 2., 6.])


def _precision_residual(operator, innovations):
    """Apply the transpose of the existing forward innovations recursion."""
    adjoint = np.zeros(operator.state_dimension)
    output = np.empty_like(innovations)
    for i in range(len(innovations)-1, -1, -1):
        gradient = solve_triangular(operator._lower[i].T, innovations[i]) + operator._gain[i].T @ adjoint
        adjoint = operator._transition[i].T @ adjoint-operator._observation[i].T @ gradient
        output[i] = gradient
    return output


def _powers(time, order):
    return np.asarray(time)[..., None]**np.arange(order+1)/FACTORIALS[:order+1]


def _driver(earlier, later, precision, *, order, psd, nodes, weights):
    """Integrate adjoint polynomials without forming any epoch covariance."""
    moments = np.zeros((order+1, 3))
    derivatives = np.zeros_like(moments)
    energy = 0.
    final = earlier[-1]
    # Anchor the running sums at the right edge of each interval. Moving
    # backwards, the binomial shift preserves the moments already accumulated.
    for i in range(len(earlier)-1, 0, -1):
        gap = earlier[i]-earlier[i-1]
        moments[0] += precision[i]
        local = gap*nodes
        adjoint = _powers(local, order) @ moments[::-1]
        integral = gap*weights
        energy += float(np.sum(integral[:, None]*adjoint**2))
        kernel_at_cut = _powers(final-earlier[i]+local, order)[:, ::-1]
        derivatives += kernel_at_cut.T @ (integral[:, None]*adjoint)
        shift = _powers(gap, order)
        moments = np.stack([shift[:j+1] @ moments[j::-1] for j in range(order+1)])
    means = psd*(_powers(later-final, order) @ derivatives)
    return psd*energy, means


def decompose(operator, earlier, later, receiver_loading, residual):
    """Return energies and future means for the frozen drift law's drivers."""
    earlier, later, residual = (np.asarray(arr, float) for arr in (earlier, later, residual))
    if (operator.observation_form != 'after_transition' or operator.state_dimension != 15
            or earlier.ndim != 1 or later.ndim != 1 or not len(earlier) or not len(later)
            or residual.shape != (len(earlier), 3) or np.shape(receiver_loading) != (len(earlier), 3, 3)
            or len(earlier)+len(later) != operator.epoch_count or earlier[-1] >= later[0]
            or np.any(np.diff(earlier) <= 0.) or np.any(np.diff(later) <= 0.)):
        raise ValueError('unchanged integrated-drift training split and scales required')
    normalized, state = operator.apply_block(residual.ravel(), first_epoch=0)
    innovations = normalized.reshape(residual.shape)
    precision = _precision_residual(operator, innovations)
    nodes, weights = np.polynomial.legendre.leggauss(4)
    nodes, weights = (1.+nodes)/2., weights/2.
    energies, means = {}, {}
    for name, (order, key) in DRIVERS.items():
        energies[name], means[name] = _driver(earlier, later, precision, order=order,
            psd=parent.POLICY[key], nodes=nodes, weights=weights)
    white = np.einsum('nji,nj->ni', receiver_loading, precision)
    total = precision.sum(axis=0)
    offset_variance = parent.POLICY['initial_receiver_offset_std_m']**2
    energies['receiver_white'] = float(np.sum(white**2))
    energies['receiver_offset'] = float(offset_variance*(total@total))
    means['receiver_white'] = np.zeros((len(later), 3))
    means['receiver_offset'] = np.repeat((offset_variance*total)[None, :], len(later), axis=0)
    future = operator.conditional_marginals(state=state)['mean']
    total_energy = float(normalized@normalized)
    if (not np.isclose(sum(energies.values()), total_energy, rtol=5e-8, atol=1e-8)
            or not np.allclose(sum(means.values()), future, rtol=5e-8, atol=5e-7)):
        raise ValueError('driver allocation differs from the original innovations operator')
    return dict(energies=energies, future_means=means, innovations=innovations)


def _rms_path(values):
    return float(np.sqrt(np.mean(np.sum(values**2, axis=1))))


def _summarize(result, sealed_mean):
    innovations, means = result['innovations'], result['future_means']
    actual = sum(means.values())
    if not np.allclose(actual, sealed_mean, rtol=5e-8, atol=5e-7):
        raise ValueError('driver allocation does not reproduce sealed conditional mean')
    energies = result['energies']
    energy = float(np.sum(innovations**2))
    receiver = sum(values for key, values in means.items() if key.startswith('receiver'))
    return dict(total_standardized_energy=energy,
        rms_standardized=float(np.sqrt(np.mean(innovations**2))),
        rms_standardized_axes=np.sqrt(np.mean(innovations**2, axis=0)).tolist(),
        rms_standardized_quarters=[float(np.sqrt(np.mean(v**2))) for v in np.split(innovations, 4)],
        maximum_absolute_standardized=float(np.max(abs(innovations))),
        component_energies=energies,
        receiver_energy_fraction=sum(v for key,v in energies.items() if key.startswith('receiver'))/energy if energy else 0.,
        component_future_mean_rms_m={key:_rms_path(values) for key,values in means.items()},
        receiver_future_mean_rms_m=_rms_path(receiver),
        inertial_future_mean_rms_m=_rms_path(actual-receiver),
        total_future_mean_rms_m=_rms_path(actual),
        sealed_mean_maximum_difference_m=float(np.max(abs(actual-sealed_mean))))


def _compute(matrix, raw_training, times, saved, task_rows):
    training = json.loads(gzip.decompress(raw_training))
    base = parent._coordinates(training)
    observed = parent._chart(base, base[0])
    cut, later = parent.CUT, parent.LATER
    earlier_cov = np.linalg.cholesky(np.array([reported_covariance(row) for row in training]))
    loadings = dict(zip(parent.WEIGHTS, (np.broadcast_to(np.eye(3)*parent.POLICY['receiver_white_std_m'],
        (cut+later, 3, 3)), np.concatenate((earlier_cov, np.repeat(earlier_cov[-1:], later, axis=0)))), strict=True))
    operators = {key:parent.operator(times, value) for key,value in loadings.items()}
    if {key:v.configuration for key,v in operators.items()} != saved['operator_configurations']:
        raise ValueError('unchanged receiver law required')
    by_identity = {row['identity']: row for row in saved['rows']}
    rows = []
    for task in task_rows:
        if not task['passed']:
            rows.append(task)
            continue
        raw = matrix.artifact(task['identity'], 'forecast.json', raw=True)
        forecast = json.loads(raw)
        if (digest(raw) != task['forecast_sha256'] or forecast['times_s'] != times
                or forecast['prediction_receiver_positions_used'] is not False
                or forecast['training_epochs'] != cut or forecast['prediction_epochs'] != later):
            raise ValueError('unchanged earlier forecast supports required')
        path = parent._chart(forecast['coordinates'], base[0])
        row = by_identity[task['identity']]
        if not np.array_equal(row['raw_future_m'], path[cut:]):
            raise ValueError('changed raw future path')
        residual = path[:cut]-observed
        cases = {}
        for key, error in operators.items():
            diagnostic = decompose(error, times[:cut], times[cut:], loadings[key][:cut], residual)
            center = np.asarray(row['ranges'][key]['center_m'])
            cases[key] = _summarize(diagnostic, path[cut:]-center)
        rows.append(dict(task, cases=cases))
    return rows


def run(root, action):
    with closing(ClosedStudy(root, 'data/'+parent.ID)) as matrix:
        inputs = {path:(root/path).read_bytes() for path in (parent.FREEZE, parent.RANGES, parent.SEAL)}
        frozen = json.loads(inputs[parent.FREEZE])
        seal = json.loads(inputs[parent.SEAL])
        saved = json.loads(gzip.decompress(inputs[parent.RANGES]))
        tasks = frozen['tasks']
        if (matrix.completion != frozen['parents'][0] or matrix.manifest['scope'] != parent.SCOPE
                or len(tasks) != 24 or len(saved['rows']) != 24 or saved['later_receiver_positions_used'] is not False
                or matrix.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'
                or seal != dict(freeze_sha256=digest(inputs[parent.FREEZE]),
                                ranges_sha256=digest(inputs[parent.RANGES]), later_receiver_reads=0)
                or saved['freeze_sha256'] != seal['freeze_sha256']
                or {key:matrix.manifest['inputs'][key]['sha256'] for key in frozen['earlier']} != frozen['earlier']
                or any(matrix.rows[row['identity']]['passed'] is not row['passed'] for row in tasks)):
            raise ValueError('unchanged opened development forecasts and earlier-only seal required')
        own = Path(__file__).relative_to(root).as_posix()
        test = 'analysis/tests/test_esa_drift_correction_audit.py'
        freeze = encoded(dict(sources={name:digest((root/name).read_bytes()) for name in
            source_closure(root, (own, PLAN, test))}, inputs={p:digest(raw) for p,raw in inputs.items()},
            parent=matrix.completion, earlier=frozen['earlier'], environment=runtime_environment(),
            maximum_operators=2, maximum_history_evaluations=48, earlier_epochs=400,
            integration_nodes=4, threads=1, fit_starts=0, later_receiver_reads=0))
        if action == 'freeze':
            _write_equal(root/FREEZE, freeze)
            return dict(freeze_sha256=digest(freeze))
        if (root/FREEZE).read_bytes() != freeze:
            raise ValueError('changed drift audit freeze')
        times = matrix.input('forecast_times')
        raw_training = matrix.input('training', raw=True)
        if len(times) != parent.CUT+parent.LATER:
            raise ValueError('unchanged earlier and future query times required')
        rows = _compute(matrix, raw_training, times, saved, tasks)
    result = encoded(dict(freeze_sha256=digest(freeze), rows=rows, later_receiver_reads=0,
        original_reads=0, protected_reads=0, fit_starts=0, calibrated=False, scientific_decision='abstain'))
    _write_equal(root/RESULT, result)
    return dict(tasks=len(rows), scored=sum(row['passed'] for row in rows), sha256=digest(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('freeze', 'replay'))
    print(run(Path.cwd(), parser.parse_args().action))
