# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent seed-family prediction scores and exact tolerance bookkeeping.

No fitting or draw generation occurs here. Probability statements require the
declared iid score population; they do not establish aircraft error coverage.
"""
import math
import re


def _probability(value):
    if type(value) not in (int,float) or not math.isfinite(value) or not 0<value<1:
        raise ValueError('finite probability strictly between zero and one required')
    return value


def _population(value):
    if not isinstance(value,str) or not re.fullmatch('[0-9a-f]{64}',value):
        raise ValueError('explicit frozen population SHA-256 required')


def _seed(value):
    if type(value) is not int or not 0<=value<2**64:raise ValueError('unsigned 64-bit draw identity required')
    return value


def _score(value):
    if type(value) not in (int,float) or not math.isfinite(value) or value<0:
        raise ValueError('finite nonnegative saved score required; use None for unavailable')
    return value


def aggregate_draws(rows,tasks,*,role,population_sha256,excluded_seeds):
    """Maximum over training-selected settings; missing settings retain the seed."""
    import json
    from .ilvis0_forecast_publication import primary
    _population(population_sha256)
    if role not in ('calibration','validation') or not isinstance(tasks,dict) or not tasks:
        raise ValueError('explicit nonempty task family and calibration/validation role required')
    excluded={_seed(v) for v in excluded_seeds};groups={};matrices={}
    for identity,task in tasks.items():
        p=task['payload'];seed=_seed(p['draw_seed']);case=p['case']
        if p['role']!=role or seed in excluded or type(case['start']) is not int or case['start']<0:
            raise ValueError('disjoint predeclared draw roles and starts required')
        key=json.dumps({k:v for k,v in case.items() if k!='start'},sort_keys=True,separators=(',',':'))
        matrix=matrices.setdefault(seed,set());entry=(key,case['start'])
        if entry in matrix:raise ValueError('duplicate setting/start in a seed family')
        matrix.add(entry);groups.setdefault(seed,{}).setdefault(key,[])
    values=list(matrices.values())
    if any(v!=values[0] for v in values):raise ValueError('same preregistered settings/starts in every seed family required')
    seen=set()
    for row in rows:
        identity=row['identity']
        if identity in seen or identity not in tasks:raise ValueError('unique declared saved row required')
        seen.add(identity);p=tasks[identity]['payload'];case=p['case']
        if (row.get('draw_seed')!=p['draw_seed'] or row.get('role')!=role
                or any(row.get(k)!=v for k,v in case.items())
                or any(type(row.get(k)) is not bool for k in ('complete','converged'))):
            raise ValueError('saved row differs from its frozen task')
        if row['complete']:_score(row['maximum_standardized_error'])
        key=json.dumps({k:v for k,v in case.items() if k!='start'},sort_keys=True,separators=(',',':'))
        groups[p['draw_seed']][key].append(dict(row,passed=row['complete'] and row['converged']))
    result=[]
    for seed,settings in sorted(groups.items()):
        chosen=[v for values in settings.values() if (v:=primary(values)) is not None]
        available=len(chosen)==len(settings)
        result.append(dict(seed=seed,role=role,population_sha256=population_sha256,
            maximum_score=max(v['maximum_standardized_error'] for v in chosen) if available else None,
            expected_settings=len(settings),available_settings=len(chosen),
            selected_identities=[v['identity'] for v in chosen],
            selection='qualified training cost, then declared start order'))
    return result


def order_statistic_plan(draws,*,coverage,confidence):
    """Smallest supported ascending rank of an upper iid tolerance limit."""
    if type(draws) is not int or not 1<=draws<=1000000:raise ValueError('finite positive independent-draw count required')
    _probability(coverage);_probability(confidence)
    from scipy.stats import binom
    from .research_calibration import required_calibration_n
    minimum=required_calibration_n(1-coverage,tail_observations=1,confidence=confidence)
    rank=None;achieved=0.
    if draws>=minimum:
        low,high=0,draws
        while low+1<high:
            middle=(low+high)//2
            if binom.cdf(middle-1,draws,coverage)>=confidence:high=middle
            else:low=middle
        rank=high;achieved=float(binom.cdf(rank-1,draws,coverage))
    return dict(draws=draws,minimum_draws=minimum,coverage=coverage,confidence=confidence,
        rank=rank,achieved_confidence=achieved,
        probability_scope='iid seed-family scores under the single frozen generating population')


def _draws(records,*,role,population_sha256,excluded_seeds):
    _population(population_sha256);excluded={_seed(v) for v in excluded_seeds};seen=set();result=[]
    for record in records:
        seed=_seed(record['seed'])
        if (seed in seen or seed in excluded or record['role']!=role
                or record['population_sha256']!=population_sha256):
            raise ValueError('unique disjoint draw roles and unchanged generating population required')
        seen.add(seed);value=record['maximum_score']
        if value is not None:_score(value)
        result.append(dict(seed=seed,role=role,population_sha256=population_sha256,maximum_score=value))
    if not result:raise ValueError('preassigned nonempty independent draws required')
    return sorted(result,key=lambda v:v['seed'])


def calibrate(draws,*,coverage,confidence,population_sha256,excluded_seeds):
    """Unavailable draws sort after finite scores; none are filtered out."""
    excluded=sorted({_seed(v) for v in excluded_seeds})
    records=_draws(draws,role='calibration',population_sha256=population_sha256,excluded_seeds=excluded)
    plan=order_statistic_plan(len(records),coverage=coverage,confidence=confidence)
    values=sorted((v['maximum_score'] for v in records),key=lambda x:math.inf if x is None else x)
    threshold=values[plan['rank']-1] if plan['rank'] is not None else None
    return dict(plan,version='prediction-tolerance-calibration-v1',population_sha256=population_sha256,
        records=records,excluded_seeds=excluded,unavailable_draws=sum(v is None for v in values),
        threshold=threshold,status='available' if threshold is not None else 'unavailable',
        aircraft_coverage_established=False,scientific_decision='abstain')


def validate(calibration,draws,*,confidence,population_sha256,coverage=None):
    """Exact upper failure bound with unavailable predictions counted as failures."""
    from .studies.artifacts import encoded,digest
    from .research_calibration import tail_upper
    _probability(confidence)
    target=calibration['coverage'] if coverage is None else _probability(coverage)
    expected=calibrate(calibration['records'],coverage=calibration['coverage'],confidence=calibration['confidence'],
        population_sha256=population_sha256,excluded_seeds=calibration['excluded_seeds'])
    if encoded(calibration)!=encoded(expected):raise ValueError('calibration record or selected threshold differs')
    records=_draws(draws,role='validation',population_sha256=population_sha256,
        excluded_seeds=[*calibration['excluded_seeds'],*(v['seed'] for v in calibration['records'])])
    threshold=calibration['threshold'];available=threshold is not None
    failures=sum(v['maximum_score'] is None or v['maximum_score']>threshold for v in records) if available else len(records)
    upper=tail_upper(len(records),failures,family_size=1,confidence=confidence)
    return dict(version='prediction-tolerance-validation-v1',population_sha256=population_sha256,
        calibration_sha256=digest(encoded(calibration)),draws=len(records),failures=failures,
        unavailable_draws=sum(v['maximum_score'] is None for v in records),failure_upper=upper,
        calibration_coverage=calibration['coverage'],target_coverage=target,
        target_failure_rate=1-target,confidence=confidence,
        passed=bool(available and upper<=1-target),
        status='available' if available else 'unavailable',records=records,all_preassigned_draws_counted=True,
        aircraft_coverage_established=False,scientific_decision='abstain')
