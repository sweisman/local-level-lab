# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check the continuous range of separate ESA innovation scales."""

import argparse
from collections import deque
from contextlib import closing
from functools import lru_cache
import json
import math
from pathlib import Path

from .esa_axis_innovation_scale import ID as PARENT, RESULT as PRIOR, axis_score
from .esa_motion_innovation_scale import BASE, LAWS, scorer
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-axis-scale-compatibility-v1'
SCOPE = 'Continuous compatibility of separate quiet and motion scales on ESA 187'
PLAN = BASE+'ESA_AXIS_SCALE_COMPATIBILITY_PLAN.md'
RESULT = BASE+'esa-axis-scale-compatibility-result.json'
REQUEST = BASE+'esa-axis-scale-compatibility-qualification.json'
TEST_REPORT = BASE+'esa-axis-scale-compatibility-tests.xml'
PRIOR_SHA = '3a24ea4ef30ebdbe47170be87ba90557e49f90d577d3d9b152e40131412b42c4'
TEST = 'analysis/tests/test_esa_axis_scale_compatibility.py'
TESTS = ('test_quadratic_interval_includes_dense_correlated_error',
         'test_search_saves_compatible_and_completely_excluded_boxes',
         'test_search_preserves_open_boxes_at_the_work_limit')
MAX_STEADY = 512
MAX_ALL = 1024
SCALE_RANGE = (-5., 5.)
WINDOWS = 8
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=WINDOWS+MAX_STEADY+MAX_ALL+2,
              bound_steps=2*WINDOWS+12*MAX_STEADY+24*MAX_ALL+12)


def quadratic_interval(score, logs):
    """Enclose the quadratic using a solve residual and a positive diagonal floor."""
    import numpy as np
    from scipy.linalg import cho_factor, cho_solve

    y, root = score.y, score.root
    if len(logs) not in (3, 6) or len(y) % 3 or any(not SCALE_RANGE[0] <= v <= SCALE_RANGE[1] for v in logs):
        raise ValueError('three or six finite log scales within the working law required')
    n = len(y)//3
    d = np.tile([math.exp(v) for v in logs[:3]], n)
    if len(logs) == 6:
        d += score.weight*np.tile([math.exp(v) for v in logs[3:]], n)
    u = root / np.sqrt(d[:, None])
    scaled = y / np.sqrt(d)
    if root.shape[1]:
        factor = cho_factor(score.identity+u.T@u, lower=True, check_finite=False)
        scaled -= u@cho_solve(factor, u.T@scaled, check_finite=False)
    point = scaled / np.sqrt(d)
    projected = root.T@point
    product = d*point + root@projected
    dual = 2.*float(y@point)-float(point@(d*point))-float(projected@projected)
    yn, xn = np.linalg.norm(y), np.linalg.norm(point)
    operator = float(d.max())+float(np.linalg.norm(root)**2)
    margin = 256*np.finfo(float).eps*(len(y)+root.shape[1])
    residual = np.linalg.norm(y-product)+margin*max(1., yn+operator*xn)
    numerical = margin*max(1., 2.*yn*xn+operator*xn*xn)
    lo = max(0., math.nextafter(dual-numerical, -math.inf))
    hi = math.nextafter(dual+numerical+residual**2/float(d.min()), math.inf)
    if not math.isfinite(hi) or hi < lo:
        raise ValueError('finite ordered covariance score enclosure required')
    return lo, hi


def check_cover(paths):
    """A complete split tree reduces to its root by joining sibling leaves."""
    remaining = set(paths)
    if len(remaining) != len(paths) or any(set(path)-{'0', '1'} for path in remaining):
        raise ValueError('unique binary split paths required')
    depth = max(map(len, remaining))
    for level in range(depth, 0, -1):
        for path in sorted(p for p in remaining if len(p) == level and p.endswith('0')):
            sibling = path[:-1]+'1'
            if sibling not in remaining or path[:-1] in remaining:
                raise ValueError('overlapping or incomplete search cover')
            remaining.difference_update((path, sibling))
            remaining.add(path[:-1])
    if remaining != {''}:
        raise ValueError('search leaves do not cover the original scale range')


def search(curves, *, bounds, reference, maximum, reserve=lambda: None):
    if (not curves or maximum < 1 or not bounds or any(not lo < hi for lo, hi in bounds)
            or not 0. < reference[0] < reference[1]):
        raise ValueError('finite search, ordered scale box and positive reference required')
    curves = [lru_cache(maxsize=None)(curve) for curve in curves]
    pending = deque([('', tuple(bounds))])
    excluded, witness = [], None
    checked = 0
    while pending and checked < maximum:
        path, box = pending.popleft()
        reserve()
        checked += 1
        lo, hi = zip(*box, strict=True)
        failures = []
        for index, curve in enumerate(curves):
            smallest, largest = curve(hi)[0], curve(lo)[1]
            if smallest > reference[1] or largest < reference[0]:
                failures.append(dict(window_slot=index, score_interval=[smallest, largest]))
        if failures:
            excluded.append(dict(path=path, box=box, failures=failures))
            continue
        mid = tuple(a+(b-a)/2. for a,b in box)
        if all(reference[0] <= q[0] <= q[1] <= reference[1] for q in (curve(mid) for curve in curves)):
            witness = mid
            pending.appendleft((path, box))
            break
        axis = max(range(len(box)), key=lambda i: box[i][1]-box[i][0])
        left, right = box[axis]
        for side, narrowed in zip(('0', '1'), ((left, mid[axis]), (mid[axis], right)), strict=True):
            pending.append((path+side, box[:axis]+(narrowed,)+box[axis+1:]))
    check_cover([row['path'] for row in excluded]+[path for path, _ in pending])
    return dict(status='witness' if witness is not None else 'unresolved' if pending else 'incompatible',
                checked=checked, excluded=excluded, open=list(pending), witness=witness)


def task_for(law):
    return dict(identity=law, input_key='design', payload=dict(law=law), limits=LIMITS)


def sources(root):
    from .studies.dependencies import source_closure

    return source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))


def request(root):
    from .ilvis0_control_shards import runtime_environment
    from .studies.qualification import request as qualify

    return qualify(root, sources=sources(root), environment=runtime_environment(),
                   output=REQUEST, report=TEST_REPORT)


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .ilvis0_matched_observed_inputs import _write_equal
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID).exists():
        raise ValueError('retain the original scale compatibility study')
    saved = (root/PRIOR).read_bytes()
    if digest(saved) != PRIOR_SHA:
        raise ValueError('exact axis scale results required')
    parent_report = json.loads(saved)
    deps, environment = sources(root), runtime_environment()
    qualification, tests = checked(root, REQUEST, sources=deps, environment=environment,
                                   required_tests=TESTS, minimum_tests=len(TESTS))
    recovery, recovery_tests = checked(root, RECOVERY, sources=qualification_sources(root),
        environment=environment, required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    materials = dict(qualification=qualification, qualification_tests=tests, recovery=recovery,
        recovery_tests=recovery_tests, recovery_policy=encoded(dict(RECOVERY_POLICY, maximum_wall_s=240)))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (any(parent_report[key] != value for key, value in parent.completion.items())
                or not parent.summary['passed'] or len(parent.rows) != 8):
            raise ValueError('all verified closed axis scale folds required')
        design = parent.input('design')
        windows = [i for pair in design['pairs'] for i in pair]
        names = ['design', *(f'observed-{i}' for i in windows)]
        names.extend(f'forecast-{i}-{law}' for law in LAWS for i in windows)
        materials.update({name: parent.input(name, raw=True) for name in names})
    inputs = dict(plan=PLAN, prior=PRIOR)
    for key, value in materials.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(),
        inputs=inputs, tasks=[task_for(law) for law in LAWS], sources=deps,
        workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    from functools import partial

    law = task['payload']['law']
    design = json.loads(context.input_path('design').read_bytes())
    windows = [i for pair in design['pairs'] for i in pair]
    steady = [i for _,i in design['pairs']]
    declared = {k: v for k,v in task.items() if k not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or law not in LAWS or declared != task_for(law)
            or len(windows) != WINDOWS or len(set(windows)) != WINDOWS):
        raise ValueError('exact frozen covariance family and windows required')
    evidence = {i: scorer(context, i, law, design['scores'][f'{i}-{law}']) for i in windows}
    if any(evidence[i].weight.any() for i in steady):
        raise ValueError('the frozen steady windows must have zero motion response')
    reference = tuple(evidence[windows[0]].reference)

    def check(indices, dimensions, maximum):
        score = search([partial(quadratic_interval, evidence[i]) for i in indices],
            bounds=[SCALE_RANGE]*dimensions, reference=reference, maximum=maximum,
            reserve=lambda: context.charge(bound_calls=1, bound_steps=3*len(indices)))
        witness = score['witness']
        if witness is not None:
            context.charge(bound_calls=1, bound_steps=len(indices))
            logs = witness if len(witness) == 6 else (*witness, 0.)
            checked = {str(i): axis_score(evidence[i], logs) for i in indices}
            if any(not row['within_reference'] for row in checked.values()):
                raise ValueError('direct likelihood does not verify the compatibility witness')
            score['witness_scores'] = checked
        return dict(score, windows=indices, reference=list(reference))

    quiet = check(steady, 3, MAX_STEADY)
    full = dict(status='excluded_by_steady', checked=0) if quiet['status'] == 'incompatible' else check(windows, 6, MAX_ALL)
    result = dict(law=law, quiet=quiet, full=full, passed=True, scientific_decision='abstain')
    context.save('compatibility.json', result)
    return result


def report(root):
    from .ilvis0_matched_observed_inputs import _write_equal

    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if set(study.rows) != set(LAWS) or study.manifest['scope'] != SCOPE:
            raise ValueError('both compatibility tasks must seal')
        laws = []
        for identity in study.rows:
            envelope = study.envelope(identity)
            result = envelope['result']
            if result['passed']:
                stages = result['quiet'], result['full']
                calls = WINDOWS+sum(x['checked']+int('witness_scores' in x) for x in stages)
                if (result != study.artifact(identity, 'compatibility.json')
                        or envelope['charged']['bound_calls'] != calls):
                    raise ValueError('closed scale compatibility work differs')
            laws.append(result)
        value = dict(study.completion, laws=laws, charged=study.summary['charged'],
                     new_fits=0, scientific_decision='abstain')
    raw = encoded(value)
    _write_equal(root/RESULT, raw)
    return dict(result_sha256=digest(raw), laws=[dict(law=row.get('law'), passed=row['passed'],
        quiet=row.get('quiet', {}).get('status'), full=row.get('full', {}).get('status')) for row in laws])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    print(json.dumps({'request': request, 'prepare': prepare, 'report': report}[action](Path.cwd()), sort_keys=True))


if __name__ == '__main__':
    main()
