# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded checks of previously unchecked neighbors; original gate unchanged."""
import numpy as np
from . import ilvis0_boundary_adapter as adapter, ilvis0_boundary_stop as stopping

VERSION = 'ilvis0-adjacent-boundary-check-v1'
POLICY = dict(maximum_checks=3, maximum_evaluations=30, stopping=stopping.POLICY,
              scientific_eligible=False, scope='local adjacent-boundary qualification')


def selected_evaluation(point, result, cache):
    selected = tuple(result.get('normalized_parameters', point))
    if selected in cache:
        return cache[selected]
    if result.get('evaluations') == 0 and not result.get('passed'):
        return None
    raise ValueError('selected result lacks its native evaluation')


def _movement_and_stationarity_pass(branch):
    p = stopping.POLICY
    gradients = branch.get('side_stationarity', []) + [branch.get('fresh_stationarity', np.inf)]
    rms = np.asarray(branch.get('position_rms', []), float)
    maximum = np.asarray(branch.get('position_maximum', []), float)
    continuity = branch.get('probe_continuity')
    return bool(len(gradients) == 3 and np.all(np.isfinite(gradients))
        and max(gradients) <= p['stationarity_tolerance']
        and np.isfinite(branch.get('relative_cost_change', np.inf))
        and branch['relative_cost_change'] <= p['relative_cost_tolerance']
        and rms.shape == maximum.shape == (3,) and np.all(np.isfinite(rms))
        and np.all(np.isfinite(maximum)) and np.all(rms >= 0) and np.all(maximum >= 0)
        and np.all(rms <= p['position_rms_tolerance_m'])
        and np.all(maximum <= p['position_max_tolerance_m'])
        and (continuity is None or continuity['passed']))


def check(point, evaluate, physical_step, *, time_index, geometry_at, maximum_evaluations=30):
    if type(maximum_evaluations) is not int or maximum_evaluations != 30:
        raise ValueError('exact thirty-call allowance required')
    point = np.array(point, float)
    if (point.ndim != 1 or not len(point) or not np.all(np.isfinite(point))
            or np.any(abs(point) > 1) or type(time_index) is not int
            or not 0 <= time_index < len(point)):
        raise ValueError('finite feasible point and time index required')
    checks, geometries, movements, trace = [], [], [], []
    residuals = []
    seen = set()
    origin = None

    def fresh(u, *, fresh=True):
        nonlocal origin
        if not fresh or len(trace) >= maximum_evaluations:
            raise ValueError('fresh bounded native evaluation required')
        value = evaluate(u.copy(), fresh=True)
        residual = np.asarray(value[0], float)
        if origin is None:
            origin = residual.copy()
        residuals.append(residual.copy())
        trace.append(dict(point=np.asarray(u).tolist(), cost=float(residual @ residual)))
        return value

    def result(passed, reason):
        return dict(version=VERSION, passed=bool(passed), reason=reason,
            normalized_parameters=point.tolist(), checks=checks, geometries=geometries,
            movements_from_initial=movements, evaluations=len(trace), evaluation_trace=trace,
            maximum_evaluations=30, policy=POLICY, scientific_eligible=False,
            scientific_decision='abstain')

    for _ in range(POLICY['maximum_checks']):
        key = tuple(point)
        if key in seen:
            return result(False, 'boundary_cycle')
        seen.add(key)
        geometry = geometry_at(float(point[time_index]))
        geometries.append(geometry)
        if not geometry['side_geometry_supported'] or geometry['point'] != point[time_index]:
            return result(False, 'unsupported_exact_neighbor_geometry')
        start = len(trace)
        current = stopping.check(point, fresh, physical_step, time_index=time_index,
                                  knots=geometry['knots'])
        checks.append(current)
        # The first native call of each check is its center. Compare actual saved
        # residuals, including every accumulated nuisance correction, to the origin.
        center_key = tuple(trace[start]['point'])
        assert center_key == key
        # Each center is freshly evaluated twice by the unchanged stopping rule.
        # Retain that first residual without another native call.
        movement = adapter.displacement_metrics(origin, residuals[start], physical_step)
        movements.append(movement)
        if not movement['passed']:
            return result(False, 'cumulative_relocation_not_stable')
        if current['passed']:
            return result(True, 'checked_adjacent_boundary_stability')
        unresolved = [b for b in current['branches'] if not b['passed']]
        if (len(current['branches']) != 2 or len(unresolved) != 1
                or unresolved[0]['reason'] != 'unchecked_neighbor_boundary'
                or not _movement_and_stationarity_pass(unresolved[0])):
            return result(False, 'nonedge_failure_preserved')
        branch = unresolved[0]
        edge = current['neighbor_edges'][0 if branch['side'] == 'left' else 1]
        correction = np.asarray(branch['correction'], float)
        if correction.shape != point.shape or not np.all(np.isfinite(correction)):
            raise ValueError('invalid saved branch correction')
        next_point = np.clip(point + correction, -1., 1.)
        if abs(next_point[time_index] - edge) > 4*np.finfo(float).eps:
            raise ValueError('branch correction did not reach declared neighbor')
        next_point[time_index] = edge
        if len(checks) == POLICY['maximum_checks']:
            return result(False, 'boundary_check_limit')
        point = next_point
    raise AssertionError('unreachable finite check state')
