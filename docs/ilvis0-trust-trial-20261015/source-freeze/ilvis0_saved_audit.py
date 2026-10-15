# SPDX-License-Identifier: AGPL-3.0-or-later
"""Calibration and residual audit of saved fits; never integrate or optimize data."""
import hashlib
import itertools
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

VERSION = 'ilvis0-saved-calibration-adequacy-audit-v1'


def verify_artifacts(directory, receipt):
    directory = Path(directory).resolve()
    artifacts = receipt['artifacts']
    if not artifacts:
        raise ValueError('empty artifact receipt')
    for name, wanted in artifacts.items():
        path = (directory/name).resolve()
        if not path.is_relative_to(directory):
            raise ValueError('artifact outside publication directory')
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != wanted:
            raise ValueError(f'artifact hash mismatch: {name}')


def fit_status(fit):
    if 'error' in fit:
        return 'failed'
    gradient = fit.get('exact_projected_gradient_relative')
    finished = fit.get('solver_reported_success') or fit.get('stopping_rule_verified')
    return ('converged' if fit.get('converged') and finished and
            isinstance(gradient, (float, int)) and math.isfinite(gradient) and
            0 <= gradient <= fit.get('stationarity_tolerance', 1e-4) else 'unresolved')


def boundary_coordinate(value):
    return math.copysign(1., value) if abs(value) >= .999 else value


def _units(name):
    if name.startswith('gyro_bias_'):
        return 180*3600/math.pi, 'deg/hour'
    if name.startswith(('gyro_gain_', 'accel_gain_')):
        return 100., '%'
    if name.startswith('attitude_'):
        return 180/math.pi, 'deg'
    if name.startswith('velocity_'):
        return 1., 'm/s'
    if name.startswith(('accel_bias_', 'gravity_')):
        return 1., 'm/s2'
    if name == 'time_offset':
        return 1., 's'
    if name == 'earth_removal':
        return 1., 'fraction'
    return 1., 'm'


def parameter_rows(fit, limits, *, profile=False):
    names = fit['active_parameters']; values = fit['normalized_parameters']
    if len(names) != len(values) or len(set(names)) != len(names):
        raise ValueError('invalid saved parameter dimensions')
    rows = []
    for name, u in zip(names, values):
        if not math.isfinite(u) or abs(u) > 1+1e-12:
            raise ValueError('invalid normalized parameter')
        value = fit['parameters'][name]
        if name == 'earth_removal':
            if not profile:
                raise ValueError('unexpected profiled removal parameter')
            lower, upper, expected = 0., 1., (u+1)/2
        else:
            limit = limits[name]
            if not math.isfinite(limit) or limit <= 0:
                raise ValueError('invalid parameter limit')
            lower, upper, expected = -limit, limit, u*limit
        if not math.isfinite(value) or not math.isclose(value, expected, rel_tol=1e-8, abs_tol=1e-15):
            raise ValueError('physical and normalized parameters disagree')
        factor, unit = _units(name)
        boundary = 'lower' if u <= -.999 else 'upper' if u >= .999 else 'interior'
        rows.append(dict(parameter=name, value=value*factor, unit=unit,
                         lower_limit=lower*factor, upper_limit=upper*factor,
                         normalized_value=u, normalized_distance_to_limit=max(0., 1-abs(u)),
                         boundary=boundary, correlation_coordinate=boundary_coordinate(u)))
    reported = fit['active_bounds']
    actual = {r['parameter'] for r in rows if r['boundary'] != 'interior'}
    if len(set(reported)) != len(reported) or set(reported) != actual:
        raise ValueError('saved active bounds disagree with parameter estimates')
    return rows


def _nonnegative(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid saved residual statistic')
    return value


def residual_summary(fit, receiver_epochs):
    if not isinstance(receiver_epochs, int) or receiver_epochs <= 0:
        raise ValueError('invalid receiver count')
    sections = fit['diagnostic_sections']
    if sum(s['epochs'] for s in sections) != receiver_epochs:
        raise ValueError('section epochs disagree with receiver count')
    if fit['sections_are_refits'] or fit['sections_are_independent_trials']:
        raise ValueError('unsupported section interpretation')
    rms = fit['residual_rms_neu_m']; header = fit['header_fixed_parameter_rms_neu_m']
    if len(rms) != 3 or len(header) != 3:
        raise ValueError('invalid residual axis dimensions')
    for value in rms+header:
        _nonnegative(value)
    n = 3*receiver_epochs
    cost = _nonnegative(fit['residual_sum_squares'])
    conservative = _nonnegative(fit['conservative_fixed_parameter_cost'])
    norm = math.hypot(*rms)
    for axis in range(3):
        pooled = sum(s['epochs']*_nonnegative(s['residual_rms_neu_m'][axis])**2 for s in sections)/receiver_epochs
        if not math.isclose(pooled, rms[axis]**2, rel_tol=1e-8, abs_tol=1e-12):
            raise ValueError('section and whole-stretch residual RMS disagree')
    return dict(receiver_epochs=receiver_epochs, residual_components=n,
                whitened_rms=math.sqrt(cost/n),
                conservative_whitened_rms=math.sqrt(conservative/n),
                north_rms_m=rms[0], east_rms_m=rms[1], vertical_rms_m=rms[2],
                horizontal_rms_m=math.hypot(rms[0], rms[1]),
                header_to_nominal_rms_ratio=math.hypot(*header)/norm if norm else None,
                section_count=len(sections), held_out_validation=False,
                epoch_residuals_available=False, absolute_fit_status='not_calibrated')


def _ranks(values):
    order = sorted(range(len(values)), key=values.__getitem__)
    ranks = [0.]*len(values); start = 0
    while start < len(order):
        end = start+1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        for index in order[start:end]:
            ranks[index] = (start+end-1)/2
        start = end
    return ranks


def rank_correlation(x, y):
    if len(x) != len(y) or any(not math.isfinite(v) for v in x+y):
        raise ValueError('invalid correlation inputs')
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return None
    a, b = _ranks(x), _ranks(y)
    mean = (len(x)-1)/2
    numerator = sum((u-mean)*(v-mean) for u, v in zip(a, b))
    denominator = math.sqrt(sum((u-mean)**2 for u in a)*sum((v-mean)**2 for v in b))
    return numerator/denominator


def weak_directions(fit):
    if 'right_singular_vectors' not in fit:
        return []
    names = fit['active_parameters']; singular = fit['singular_values']
    vectors = fit['right_singular_vectors']
    if len(singular) != len(vectors) or any(len(v) != len(names) for v in vectors):
        raise ValueError('invalid saved singular vector dimensions')
    if any(not math.isfinite(v) for row in vectors for v in row):
        raise ValueError('invalid saved singular vector')
    for value in singular:
        _nonnegative(value)
    largest = max(singular, default=0.)
    rows = []
    for rank, i in enumerate(sorted(range(len(singular)), key=singular.__getitem__)[:3], 1):
        dominant = sorted(zip(names, vectors[i]), key=lambda v: (-abs(v[1]), v[0]))[:5]
        rows.append(dict(weak_direction=rank, singular_value=singular[i],
                         relative_singular_value=singular[i]/largest if largest else None,
                         dominant_parameters=';'.join(f'{name}:{value:.6g}' for name, value in dominant)))
    return rows


def summarize_parameters(rows):
    groups = defaultdict(list)
    for row in rows:
        for model, case, status in [('all', 'all', 'all'),
                                     (row['model'], row['case_id'], 'all'),
                                     (row['model'], row['case_id'], row['status'])]:
            groups[row['study'], model, case, status, row['parameter']].append(row)
    output = []
    for (study, model, case, status, parameter), values in sorted(groups.items()):
        counts = Counter(r['boundary'] for r in values)
        output.append(dict(study=study, model=model, case_id=case, status=status,
                           parameter=parameter, fits=len(values), lower=counts['lower'],
                           upper=counts['upper'], interior=counts['interior'],
                           boundary_fraction=(counts['lower']+counts['upper'])/len(values),
                           median_value=median(r['value'] for r in values), unit=values[0]['unit']))
    return output


def parameter_correlations(rows):
    groups = defaultdict(dict)
    for row in rows:
        for scope in ['all_saved', 'converged_only'] if row['status'] == 'converged' else ['all_saved']:
            key = row['study'], row['model'], row['case_id'], scope
            groups[key].setdefault(row['fit_id'], {})[row['parameter']] = row['correlation_coordinate']
    output = []
    for (study, model, case, scope), fits in sorted(groups.items()):
        names = sorted(set().union(*(r.keys() for r in fits.values())))
        for a, b in itertools.combinations(names, 2):
            paired = [(r[a], r[b]) for r in fits.values() if a in r and b in r]
            output.append(dict(study=study, model=model, case_id=case, scope=scope,
                               parameter_a=a, parameter_b=b, fits=len(paired),
                               spearman_rho=rank_correlation([r[0] for r in paired], [r[1] for r in paired])))
    return output


def analyze(studies, selection, cases):
    selected = {r['segment']['segment_id']: r['segment'] for r in selection['selected']}
    case_lookup = {r['case_id']: r for r in cases}
    parameters, fits, directions = [], [], []; identities = set()
    for study, summary in studies.items():
        for result in summary['results']:
            sid = result['segment_id']; segment = selected[sid]
            fixes = segment['receiver_fixes']; epochs = result['provenance']['receiver_epochs']
            if epochs != len(fixes):
                raise ValueError('selected fixes disagree with fitted receiver epochs')
            context = dict(study=study, segment_id=sid, filename=result['filename'],
                           imu_type=segment['imu_type'], duration_min=segment['duration_s']/60,
                           median_speed_kmh=segment['median_receiver_ground_speed_kmh'],
                           median_latitude_deg=math.degrees(median(f['latitude_rad'] for f in fixes)),
                           median_receiver_height_m=median(f['height_m'] for f in fixes),
                           shape_outcome=result['profile']['conditional_shape_preference'])
            for case in result['cases']:
                declared = case_lookup[case['case_id']]
                for fit in case['fits']:
                    identity = '::'.join([study, sid, case['case_id'], fit['model']])
                    if identity in identities:
                        raise ValueError('duplicate fit identity')
                    identities.add(identity)
                    common = dict(fit_id=identity, study=study, segment_id=sid,
                                  case_id=case['case_id'], model=fit['model'], status=fit_status(fit))
                    decoded = parameter_rows(fit, declared['limits'], profile=declared['profile'])
                    parameters.extend(dict(**common, **r) for r in decoded)
                    fits.append(dict(**context, fit_id=identity, case_id=case['case_id'], model=fit['model'],
                                     status=common['status'], active_bound_count=len(fit['active_bounds']),
                                     **residual_summary(fit, epochs)))
                    directions.extend(dict(**common, **r) for r in weak_directions(fit))
    return dict(parameters=parameters, fits=fits, weak_directions=directions,
                boundary_summary=summarize_parameters(parameters),
                correlations=parameter_correlations(parameters),
                model_evaluations_performed=0, optimizer_starts=0, scientific_decision='abstain')
