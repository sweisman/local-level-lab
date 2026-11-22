# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate saved ESA height coverage and height's contribution to ranking."""

import argparse
from contextlib import closing
import gzip
import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import solve_triangular

from . import esa_joint_path_score as prior
from . import esa_matched_uncertainty as uncertainty
from .airquantumgrav_error_policy import reported_covariance
from .esa_matched_conditioning import ID as MATCHED
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy
from .studies.readers import read


ID = 'esa-height-role-v1-20261121'
RANKING_ID = 'esa-height-role-accounting-v2-20261121'
FOLDER = uncertainty.DOCS
PLAN = FOLDER+'ESA_HEIGHT_ROLE_PLAN.md'
RANKING_PLAN = FOLDER+'ESA_HEIGHT_ROLE_ACCOUNTING_PLAN.md'
RESULT = FOLDER+'esa-height-role.json'
SCOPE = 'Saved ESA 187 height coverage and marginal horizontal path ranking'
SCORE_SHA = '1728992da4c559cd0b302ba2df7a8d88b5b3832866fda0d6f24951d4b72c57bf'
UNCERTAINTY_SHA = '54b5c41f9a9608abb2556baac0d60c35a45770405eee74fdb00480803e9c735e'
Z95 = 1.959963984540054
FULL, REDUCED = prior.full, prior.reduced
CUT, LATER = FULL.CUT, FULL.LATER
CASES = {f'{law}-{weight}': (law, weight) for law in prior.LAWS for weight in FULL.WEIGHTS}
HEIGHT = 'short-height'


def band_diagnostic(raw, adjusted, observed, sigma):
    raw, adjusted, observed, sigma = (np.asarray(x, float) for x in (raw, adjusted, observed, sigma))
    if (sigma.ndim != 1 or not len(sigma) or np.any(sigma <= 0)
            or any(v.shape != sigma.shape or not np.isfinite(v).all()
                   for v in (raw, adjusted, observed, sigma))):
        raise ValueError('aligned finite heights and positive stated widths required')
    first, second = raw-observed, adjusted-observed
    a, b = abs(first) <= Z95*sigma, abs(second) <= Z95*sigma
    change = adjusted-raw
    count = len(sigma)
    return dict(epochs=count, raw_inside=int(a.sum()), adjusted_inside=int(b.sum()),
        entered=int(np.sum(~a & b)), left=int(np.sum(a & ~b)),
        raw_rms_m=float(np.linalg.norm(first)/math.sqrt(count)),
        adjusted_rms_m=float(np.linalg.norm(second)/math.sqrt(count)),
        raw_standardized_rms=float(np.linalg.norm(first/sigma)/math.sqrt(count)),
        adjusted_standardized_rms=float(np.linalg.norm(second/sigma)/math.sqrt(count)),
        squared_error_change_m2=float((2.*first+change) @ change),
        adjustment_rms_m=float(np.linalg.norm(change)/math.sqrt(count)))


def partition_scores(lower, paths):
    """Scores before and after dropping later height from a joint Gaussian."""
    lower, paths = np.asarray(lower, float), np.asarray(paths, float)
    if (lower.ndim != 2 or lower.shape[0] != lower.shape[1] or not len(lower)
            or len(lower) % 3 or paths.ndim != 2 or len(paths) != len(lower)
            or np.any(np.diag(lower) <= 0) or np.any(np.triu(lower, 1))
            or not np.isfinite(lower).all() or not np.isfinite(paths).all()):
        raise ValueError('aligned north/east/height paths and lower covariance factor required')
    horizontal = np.arange(len(lower)) % 3 != 2
    # QR supplies a lower factor R.T of the marginal horizontal covariance.
    # The residual in its orthogonal complement is height given horizontal.
    basis, upper = np.linalg.qr(lower[horizontal].T, mode='reduced')
    head = solve_triangular(upper.T, paths[horizontal], lower=True)
    white = solve_triangular(lower, paths, lower=True)
    tail = white-basis @ head
    full = np.sum(white**2, axis=0)
    horizontal = np.sum(head**2, axis=0)
    conditional = np.sum(tail**2, axis=0)
    if not np.allclose(full, horizontal+conditional, rtol=1e-8, atol=1e-10):
        raise ValueError('joint score does not partition into marginal and conditional terms')
    return dict(full=full, horizontal=horizontal, height_given_horizontal=conditional)


def _task(identity):
    return dict(identity=identity, input_key=identity, payload={},
        limits=dict(native_calls=0, packet_visits=0, bound_calls=1 if identity == HEIGHT else 21,
                    bound_steps=0))


def _checked(root, path, sha256):
    raw = read(root, path)
    if digest(raw) != sha256:
        raise ValueError('changed prior scoring receipt: '+path)
    return json.loads(raw)


def _selections(root, scores):
    materials = {p: read(root, p) for m in (FULL, REDUCED)
                 for p in (m.FREEZE, m.SEAL, m.RANGES, m.RESULT)}
    ranges = [prior._ranges(materials, m) for m in (FULL, REDUCED)]
    original = [json.loads(materials[m.RESULT]) for m in (FULL, REDUCED)]
    for record, module in zip(original, (FULL, REDUCED), strict=True):
        if any(record[key] != value for key, value in json.loads(materials[module.SEAL]).items()):
            raise ValueError('saved scores and earlier-only ranges disagree')
    keys = ('profile', 'law', 'primary', 'complete')
    matched, alternative = ([{k: row[k] for k in keys} for row in record['matched_settings']]
                            for record in original)
    if matched != alternative:
        raise ValueError('forecast start selection differs across working covariances')
    with closing(ClosedStudy(root, 'data/'+FULL.ID)) as fit, closing(
            ClosedStudy(root, FULL.PARENT, store=fit.store)) as parent:
        if (json.loads(materials[FULL.FREEZE])['parents'] != [fit.completion, parent.completion]
                or fit.input('parent_identity')['source_id'] != 'esa-99f1530c3eda4318'):
            raise ValueError('exact ESA development forecast inputs required')
        training = json.loads(gzip.decompress(fit.input('training', raw=True)))
        times = fit.input('forecast_times')
        receiver = json.loads(gzip.decompress(parent.input('training', raw=True)))
        later = receiver[CUT:CUT+LATER]
        anchor = FULL._coordinates(training[:1])[0].tolist()
        if (receiver[:CUT] != training or len(times) != CUT+LATER or len(later) != LATER
                or any(digest(encoded(later)) != record['later_receiver_sha256'] for record in original)
                or any(anchor != receipt['anchor'] for receipt in ranges)):
            raise ValueError('exact saved forecast and receiver support required')
        flags = [{r['identity']: r['passed'] for r in receipt['rows']} for receipt in ranges]
        if flags[0] != flags[1] or flags[0] != {k: v['passed'] for k, v in fit.rows.items()}:
            raise ValueError('preserve all original fit dispositions')
    observed = FULL._chart(FULL._coordinates(later), anchor)
    by_id = {row['identity']: row for row in scores['rows']}
    if flags[0] != {k: v['passed'] for k, v in by_id.items()} or sum(flags[0].values()) != 20:
        raise ValueError('unchanged 20 scored paths and four failures required')
    weights = np.linalg.cholesky(np.asarray([reported_covariance(row) for row in training]))
    factors = (np.broadcast_to(np.eye(3)*FULL.POLICY['receiver_white_std_m'], (len(times), 3, 3)),
               np.concatenate((weights, np.repeat(weights[-1:], LATER, axis=0))))
    score_inputs = {}
    for identity, (law, weight) in CASES.items():
        receipt = ranges[prior.LAWS.index(law)]
        rows = []
        for row in receipt['rows']:
            name = row['identity']
            if row['passed']:
                path = np.asarray(row['ranges'][weight]['center_m'])
                rows.append(dict(identity=name, difference=(path-observed).tolist(),
                    saved_score=by_id[name]['scores'][law][weight]['120']['squared_standardized_error']))
        score_inputs[identity] = dict(identity=identity, times=times, rows=rows,
            operator_configuration=receipt['operator_configurations'][weight],
            weights=factors[FULL.WEIGHTS.index(weight)].tolist(),
            settings=matched)
    return score_inputs


def _height_inputs(root, record):
    arm = '800-increment'
    matched = _checked(root, uncertainty.MATCHED_REPORT, uncertainty.MATCHED_SHA)
    with closing(ClosedStudy(root, 'data/'+uncertainty.ID)) as width, closing(
            ClosedStudy(root, 'data/'+MATCHED, store=width.store)) as forecast:
        for study, summary in ((width, record), (forecast, matched)):
            if any(study.completion[k] != summary[k] for k in ('manifest_sha256', 'summary_sha256')):
                raise ValueError('changed sealed inputs for the 800-cut height check')
        band, means = width.input(arm), forecast.input(arm)
        saved = next(r for r in record['rows'] if r['identity'] == arm)
        if (band['forecast'][:LATER] != means['adjusted'] or band['receiver'][:LATER] != means['receiver']
                or saved != width.artifact(arm, 'matched-uncertainty.json')):
            raise ValueError('raw, adjusted and saved widths must bind the same 120 epochs')
    return dict(identity=HEIGHT, raw=[r[2] for r in means['raw']],
        adjusted=[r[2] for r in means['adjusted']], receiver=[r[2] for r in means['receiver']],
        sigma=np.sqrt(np.asarray(band['covariance'][:LATER])[:, 2, 2]).tolist(),
        saved_outside=saved['same_120']['outside_counts']['up'])


def evaluate(task, context):
    key = task['identity']
    data = json.loads(context.input_path().read_bytes())
    if (context.manifest['scope'] != SCOPE or data['identity'] != key
            or {k: v for k, v in task.items() if k not in ('index', 'shard')} != _task(key)):
        raise ValueError('exact frozen diagnostic task required')
    if key == HEIGHT:
        context.charge(bound_calls=1, bound_steps=0)
        outcome = band_diagnostic(data['raw'], data['adjusted'], data['receiver'], data['sigma'])
        if outcome['epochs'] != LATER or LATER-outcome['adjusted_inside'] != data['saved_outside']:
            raise ValueError('did not reproduce the saved 120-report height count')
    else:
        law, weight = CASES[key]
        if len(data['rows']) != 20 or len(data['times']) != CUT+LATER:
            raise ValueError('unchanged scored path inventory required')
        context.charge(bound_calls=1, bound_steps=0)
        maker = FULL.operator if law == 'full' else REDUCED.no_snap_operator
        operator = maker(data['times'], np.asarray(data['weights']))
        if operator.configuration != data['operator_configuration']:
            raise ValueError('original conditional covariance required')
        d = operator.observation_dimension
        _, start = operator.apply_block(np.zeros((CUT*d, LATER*d)), first_epoch=0, inverse=True)
        lower, _ = operator.apply_block(np.eye(LATER*d), first_epoch=CUT, state=start, inverse=True)
        for _ in data['rows']:
            context.charge(bound_calls=1, bound_steps=0)
        paths = np.column_stack([np.asarray(v['difference']).ravel() for v in data['rows']])
        score = partition_scores(lower, paths)
        if not np.allclose(score['full'], [v['saved_score'] for v in data['rows']], rtol=1e-8, atol=1e-9):
            raise ValueError('full joint scores differ from the saved replay')
        rows = {row['identity']: {name: float(v[i]) for name, v in score.items()}
                for i, row in enumerate(data['rows'])}
        settings = []
        for setting in data['settings']:
            ranking = {}
            if setting['complete']:
                for name in ('full', 'horizontal'):
                    ranking[name] = {model: rows[s][name] for model, s in setting['primary'].items()}
            settings.append(dict(setting, ranking=ranking))
        if sum(r['complete'] for r in settings) != 2:
            raise ValueError('same two complete matched comparisons required')
        outcome = dict(law=law, weighting=weight, rows=rows, settings=settings)
    result = dict(identity=key, result=outcome, scientific_decision='abstain')
    context.save('height-role.json', result)
    return dict(result, passed=True)


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(ID+'-inputs')
    if base.exists() or (root/'data'/ID).exists():
        raise ValueError('reuse the existing height-role freeze')
    score = _checked(root, prior.OBSERVED, SCORE_SHA)
    width = _checked(root, uncertainty.RESULT, UNCERTAINTY_SHA)
    materials = {HEIGHT: _height_inputs(root, width), **_selections(root, score)}
    base.mkdir()
    inputs = {'plan': PLAN, 'joint-score': prior.OBSERVED, 'matched-width': uncertainty.RESULT}
    for key, data in materials.items():
        name = base/(key+'.json')
        atomic(name, encoded(data))
        inputs[key] = name.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_esa_height_role.py'
    manifest = Definition.from_dict(dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[_task(key) for key in materials], sources=source_closure(root, (adapter, PLAN, test)),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def _terminal_inputs(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if (study.completion['state'] != 'terminal' or set(study.rows) != {HEIGHT, *CASES}
                or study.summary['bound_evaluations'] != 1 or not study.rows[HEIGHT]['passed']):
            raise ValueError('exact prior terminal run with one completed height calculation required')
        for key in CASES:
            envelope = study.envelope(key)
            if (any(envelope['charged'].values()) or envelope['artifacts'] or envelope['result']['passed']
                    or envelope['result']['reason'] != 'charge exactly one operation or a declared native block'):
                raise ValueError('only uncomputed scoring tasks with the verified accounting error qualify')
        height = study.artifact(HEIGHT, 'height-role.json')
        if dict(height, passed=True) != study.envelope(HEIGHT)['result']:
            raise ValueError('saved height audit differs from its sealed task')
        staged = {key: study.input(key, raw=True) for key in CASES}
        return study.completion, height, staged


def prepare_ranking(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    base = root/'data'/(RANKING_ID+'-inputs')
    if base.exists() or (root/'data'/RANKING_ID).exists():
        raise ValueError('reuse the existing ranking freeze')
    completion, height, prepared = _terminal_inputs(root)
    material = dict(prepared, terminal=encoded(completion), height=encoded(height))
    base.mkdir()
    inputs = {'plan': RANKING_PLAN, 'initial-plan': PLAN}
    for key, raw in material.items():
        name = base/(key+'.json')
        atomic(name, raw)
        inputs[key] = name.relative_to(root).as_posix()
    adapter = Path(__file__).relative_to(root).as_posix()
    test = 'analysis/tests/test_esa_height_role.py'
    manifest = Definition.from_dict(dict(id=RANKING_ID, scope=SCOPE, adapter=adapter, inputs=inputs,
        tasks=[_task(key) for key in CASES], sources=source_closure(root, (adapter, PLAN, RANKING_PLAN, test)),
        workers=1, threads=1, maximum_wall_s=90.), root).prepare(root)
    print(json.dumps(manifest['limits'], sort_keys=True))


def collect(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    completion, height, _ = _terminal_inputs(root)
    with closing(ClosedStudy(root, 'data/'+RANKING_ID)) as study:
        if (not study.summary['passed'] or set(study.rows) != set(CASES)
                or study.summary['bound_evaluations'] != 84 or study.input('terminal') != completion
                or study.input('height') != height):
            raise ValueError('all four scoring tasks and 84 calculations must be sealed')
        results = [height]
        for key in CASES:
            row = study.artifact(key, 'height-role.json')
            if dict(row, passed=True) != study.envelope(key)['result'] or row['identity'] != key:
                raise ValueError('archived result disagrees with its sealed task')
            results.append(row)
        raw = encoded(dict(results=results, **study.completion, initial_run=completion,
            scientific_decision='abstain'))
    _write_equal(root/RESULT, raw)
    print(digest(raw))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'prepare-ranking', 'collect'))
    {'prepare': prepare, 'prepare-ranking': prepare_ranking, 'collect': collect}[parser.parse_args().action](Path.cwd())
