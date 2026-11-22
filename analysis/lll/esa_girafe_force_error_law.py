# SPDX-License-Identifier: AGPL-3.0-or-later
"""Chronological within-flight test of two relative force-error laws."""

from contextlib import closing
import json
import math
from pathlib import Path
from statistics import NormalDist
import sys

from . import esa_girafe_force_overlap as overlap
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy

ID = 'esa-girafe-force-error-law-v1'
SCOPE = 'train relative force-error covariance on the first four open ESA 187 windows'
PLAN = overlap.transfer.FOLDER + 'ESA_GIRAFE_FORCE_ERROR_LAW_PLAN.md'
RESULT = overlap.transfer.FOLDER + 'esa-girafe-force-error-law-result.json'
SOURCE_SHA = '7091570b29db240a1609b55d1e516fd1459e99fc919b8b11ec5f5b6f0ca8acb4'
TRAINING_WINDOWS = 4
WIDTHS = (11, 25)
TASKS = [dict(identity=f'width-{width}', input_key='force', payload=dict(width=width),
              limits=dict(native_calls=0, packet_visits=0, bound_calls=1, bound_steps=2))
         for width in WIDTHS]


def fit_laws(training):
    """Learn both working covariances from complete earlier windows."""
    import numpy as np

    d = np.asarray(training, float)
    if d.ndim != 2 or d.shape[0] < 2 or d.shape[1] < 3 or not np.isfinite(d).all():
        raise ValueError('finite earlier windows sharing common support required')
    windows, supports = d.shape
    mu = float(np.mean(d))
    iid_variance = float(np.var(d, ddof=1))
    means = np.mean(d, axis=1)
    centered = d-means[:, None]
    pair_variation = float(np.sum(centered[:, :-1]**2))
    if iid_variance <= 0. or pair_variation <= 0.:
        raise ValueError('positive earlier support variance required')
    lag = float(np.sum(centered[:, :-1]*centered[:, 1:])/pair_variation)
    rho = min(.95, max(-.95, lag))
    indices = np.arange(supports)
    correlation = rho**abs(indices[:, None]-indices)
    mean_fraction = float(np.mean(correlation))
    within = float(np.mean(centered**2)/(1.-mean_fraction))
    variance_of_mean = within*mean_fraction
    between = max(0., float(np.var(means, ddof=1))-variance_of_mean)
    iid_mean_variance = iid_variance/d.size
    mean_variance = (between+variance_of_mean)/windows
    return {
        'iid': dict(mean=mu, support_variance=iid_variance, fitted_mean_variance=iid_mean_variance,
                    covariance=iid_variance*np.eye(supports)+iid_mean_variance),
        'correlated': dict(mean=mu, raw_lag=lag, rho=rho, support_variance=within,
                           window_variance=between, fitted_mean_variance=mean_variance,
                           covariance=within*correlation+between+mean_variance),
    }


def score_window(values, law):
    import numpy as np

    values = np.asarray(values, float)
    covariance = law['covariance']
    if (values.ndim != 1 or not len(values) or covariance.shape != (len(values), len(values))
            or not np.isfinite(values).all()):
        raise ValueError('finite complete held-out window required')
    residual = values-law['mean']
    factor = np.linalg.cholesky(covariance)
    whitened = np.linalg.solve(factor, residual)
    standardized = float(np.mean(whitened**2))
    radius = NormalDist().inv_cdf(.975)*math.sqrt(float(np.mean(covariance)))
    return dict(observed_mean_mps2=float(np.mean(values)), mean_error_mps2=float(np.mean(residual)),
                rms_mps2=float(np.sqrt(np.mean(residual**2))), mean_square_standardized=standardized,
                log_score_per_support=float((standardized+math.log(2.*math.pi))/2.+np.mean(np.log(factor.diagonal()))),
                working_95_mean_radius_mps2=radius, mean_supported=bool(abs(np.mean(residual)) <= radius))


def _input(root):
    source = (root / overlap.RESULT).read_bytes()
    if digest(source) != SOURCE_SHA:
        raise ValueError('original GIRAFE–iMAR force-overlap report required')
    raw = json.loads(source)
    entries = sorted(raw['windows'], key=lambda w: w['range_utc_s'][0])
    if (len(entries) != 8 or any(a['range_utc_s'][1] >= b['range_utc_s'][0] for a, b in zip(entries, entries[1:]))
            or raw['protected_reads'] != 0):
        raise ValueError('eight distinct chronological development windows required')
    return source


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    directory = root / 'data' / (ID+'-inputs')
    if directory.exists() or (root / 'data' / ID).exists():
        raise ValueError('existing force-error law freeze must stay intact')
    target = directory / 'force-overlap.json'
    atomic(target, _input(root))
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=dict(force=target.relative_to(root).as_posix()),
        tasks=TASKS, sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_girafe_force_error_law.py']),
        workers=1, threads=1, maximum_wall_s=60.)
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or declared not in TASKS:
        raise ValueError('exact chronological force-error task required')
    raw = context.input_path('force').read_bytes()
    if digest(raw) != SOURCE_SHA:
        raise ValueError('original force values differ')
    entries = sorted(json.loads(raw)['windows'], key=lambda w: w['range_utc_s'][0])
    width = task['payload']['width']
    rows = []
    for window in entries:
        item, = (item for item in window['widths'] if item['width_reports'] == width)
        logged, = (a for a in item['alignments'] if a['girafe_clock_shift_s'] == 0.)
        values = logged['differences']['with_offset']['girafe_minus_imar_mps2']
        if len(values) != 16:
            raise ValueError('fixed sixteen acceleration supports required')
        rows.append(dict(window=window['window'], kind=window['kind'], range_utc_s=window['range_utc_s'],
                         difference_mps2=values))

    context.charge(bound_calls=1, bound_steps=2)
    earlier = rows[:TRAINING_WINDOWS]
    laws = fit_laws([row['difference_mps2'] for row in earlier])
    for row in rows[TRAINING_WINDOWS:]:
        row['scores'] = {name: score_window(row['difference_mps2'], law) for name, law in laws.items()}
    parameters = {name: law | {'covariance': law['covariance'].tolist()} for name, law in laws.items()}
    context.save_bytes('error-law.json', encoded(dict(width_reports=width, training=earlier,
        held_out=rows[TRAINING_WINDOWS:], laws=parameters, scientific_decision='abstain')))
    return dict(passed=True, scientific_decision='abstain')


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (not study.summary['passed'] or len(study.rows) != len(TASKS)
                or study.summary['charged']['bound_calls'] != 2 or study.summary['charged']['bound_steps'] != 4):
            raise ValueError('complete two-width error-law report required')
        widths = [study.artifact(task['identity'], 'error-law.json') for task in TASKS]
        result = dict(widths=widths, charged=study.summary['charged'],
                      manifest_sha256=study.completion['manifest_sha256'], force_report_sha256=SOURCE_SHA,
                      protected_reads=0, original_data_reads=0, scientific_decision='abstain')
    raw = encoded(result)
    path = root / RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('saved GIRAFE force-error report differs')
    print(digest(raw))


if __name__ == '__main__':
    if sys.argv[1:] == ['prepare']:
        prepare(Path.cwd())
    elif sys.argv[1:] == ['report']:
        report(Path.cwd())
    else:
        raise SystemExit('usage: python -m lll.esa_girafe_force_error_law {prepare,report}')
