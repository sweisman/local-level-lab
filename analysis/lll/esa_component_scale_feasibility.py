# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check whether a common covariance fits all saved ESA windows."""

from collections import deque
from contextlib import closing
import json
import math
from pathlib import Path
import sys

from .esa_component_scale_transfer import LAWS, LOG_BOUNDS, read_case, score_case
from .esa_scored_path_shape import BASE
from .esa_whitened_scale_transfer import ID as PARENT, RESULT as PARENT_REPORT, whiten
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-component-scale-feasibility-v1'
PLAN = BASE+'ESA_COMPONENT_SCALE_FEASIBILITY_PLAN.md'
RESULT = BASE+'esa-component-scale-feasibility-result.json'
SCOPE = 'ESA 187 joint retrospective compatibility of the three covariance components'
PARENT_MANIFEST = '785870325e05b84a37ebb8c1811c45852edc4f292751343448eadb29182cda05'
PARENT_REPORT_SHA = 'd94bc8a992c3db333ec73bf6179b97a9fea30d891100ee5c7d871c05aefdf6b0'
MAXIMUM = 256
SOLVES_PER_BOX = 24


class Quadratic:
    def __init__(self, case):
        import numpy as np

        self.y = case.error
        self.identity = np.eye(len(self.y))
        self.roots = tuple(case.roots[name] for name in ('persistent', 'maneuver'))
        self.components = case.component_covariance[1:]
        self.root_norm_squared = np.array([np.linalg.norm(r)**2 for r in self.roots])
        self.margin = 256*np.finfo(float).eps*len(self.y)
        self.cache = {}

    def bounds(self, ratios):
        import numpy as np
        from scipy.linalg import cho_factor, cho_solve

        if ratios in self.cache:
            return self.cache[ratios]
        a = self.identity + ratios[0]*self.components[0] + ratios[1]*self.components[1]
        x = cho_solve(cho_factor(a, lower=True, check_finite=False), self.y, check_finite=False)
        projections = [root.T @ x for root in self.roots]
        product = x + sum(ratio*(root @ u) for ratio, root, u in zip(
            ratios, self.roots, projections, strict=True))
        residual = np.linalg.norm(self.y-product)
        dual = 2*float(self.y @ x) - float(x @ x) - sum(
            ratio*float(u @ u) for ratio, u in zip(ratios, projections, strict=True))

        # The exact correction to the dual is r^T A^-1 r, at most ||r||²
        # because the two additions are positive semidefinite and A >= I.
        y_norm, x_norm = np.linalg.norm(self.y), np.linalg.norm(x)
        size = y_norm + x_norm*(1.+np.dot(ratios, self.root_norm_squared))
        err = self.margin*max(1., size)
        delta = 2*err*max(1., x_norm)
        lo, hi = max(0., dual-delta), dual+delta+(residual+err)**2
        if not math.isfinite(hi) or not lo <= hi:
            raise ValueError('nonfinite or inconsistent quadratic bracket')
        self.cache[ratios] = (lo, hi)
        return self.cache[ratios]


def inspect_box(at_low, at_high, *, ratio_box, scale_bounds, reference, inner=False):
    variance_min, variance_max = scale_bounds
    ref_min, ref_max = reference
    lower = [(variance_min, 'native')]
    upper = [(variance_max, 'native')]
    for key, (left, right) in zip(('persistent', 'maneuver'), ratio_box, strict=True):
        lower.append((variance_min/math.exp(right), key))
        upper.append((variance_max/math.exp(left), key))
    for index, (small, large) in enumerate(zip(at_high, at_low, strict=True)):
        lower.append((small[1 if inner else 0]/ref_max, index))
        upper.append((large[0 if inner else 1]/ref_min, index))
    lo, lower_source = max(lower, key=lambda row: row[0])
    hi, upper_source = min(upper, key=lambda row: row[0])
    direction = 1. if inner else -1.
    return ((lo+direction*1e-12*max(1., abs(lo)), hi-direction*1e-12*max(1., abs(hi))),
            (lower_source, upper_source))


def search(curves, *, reference, maximum, reserve=lambda: None):
    lo, hi = LOG_BOUNDS
    scale_bounds = (math.exp(lo), math.exp(hi))
    original = ((lo-hi, hi-lo),)*2
    pending, excluded, checked, witness = deque([original]), [], 0, None
    while pending and checked < maximum:
        box = pending.popleft()
        reserve()
        checked += 1
        low, high = (tuple(math.exp(side[endpoint]) for side in box) for endpoint in (0, 1))
        bounds = dict(ratio_box=box, scale_bounds=scale_bounds, reference=reference)
        feasible, sources = inspect_box([curve.bounds(low) for curve in curves],
                                        [curve.bounds(high) for curve in curves], **bounds)
        if feasible[0] > feasible[1]:
            excluded.append(dict(box=box, native_interval=feasible, active_limits=sources))
            continue
        midpoint = tuple((left+right)/2 for left, right in box)
        ratios = tuple(map(math.exp, midpoint))
        at_midpoint = [curve.bounds(ratios) for curve in curves]
        interval, _ = inspect_box(at_midpoint, at_midpoint, ratio_box=tuple((m, m) for m in midpoint),
                                  scale_bounds=scale_bounds, reference=reference, inner=True)
        if interval[0] <= interval[1]:
            native = math.sqrt(interval[0]*interval[1])
            witness = dict(native=native, persistent=native*ratios[0], maneuver=native*ratios[1])
            pending.appendleft(box)
            break
        axis = max(range(2), key=lambda index: box[index][1]-box[index][0])
        a, b = box[axis]
        for half in ((a, midpoint[axis]), (midpoint[axis], b)):
            pending.append(tuple(half if index == axis else side for index, side in enumerate(box)))
    status = 'witness' if witness is not None else 'unresolved' if pending else 'incompatible'
    return dict(status=status, root=original, scale_bounds=scale_bounds, reference=reference,
                checked=checked, excluded=excluded, open=list(pending), witness=witness,
                unique_solves=sum(len(curve.cache) for curve in curves))


def task_for(law):
    return dict(identity=law, input_key='design', payload=dict(law=law),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=MAXIMUM,
                            bound_steps=SOLVES_PER_BOX*MAXIMUM))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('existing feasibility study must be preserved')
    if digest((root/PARENT_REPORT).read_bytes()) != PARENT_REPORT_SHA:
        raise ValueError('exact sealed whitening report required')
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']:
            raise ValueError('the closed input archive must match the verified study')
        design = parent.input('design')
        indices = [index for pair in design['pairs'] for index in pair]
        keys = ['design', *(f'observed-{index}' for index in indices)]
        keys.extend(f'forecast-{index}-{law}' for index in indices for law in LAWS)
        materials = {key: parent.input(key, raw=True) for key in keys}
    inputs = dict(plan=PLAN, prior_report=PARENT_REPORT)
    for name, raw in materials.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[task_for(law) for law in LAWS], workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_component_scale_feasibility.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def evaluate(task, context):
    from scipy.stats import chi2

    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    law = task['payload']['law']
    if context.manifest['scope'] != SCOPE or law not in LAWS or declared != task_for(law):
        raise ValueError('the exact stored component feasibility task is required')
    design = json.loads(context.input_path('design').read_bytes())
    indices = [index for pair in design['pairs'] for index in pair]
    if len(indices) != 8 or len(set(indices)) != 8:
        raise ValueError('eight distinct frozen comparison windows required')
    original = [read_case(context, i, law, design['scores'][f'{i}-{law}']) for i in indices]
    curves = [Quadratic(whiten(case)[0]) for case in original]
    reference = tuple(chi2.ppf([.05/16, 1-.05/16], 360).tolist())
    outcome = search(curves, reference=reference, maximum=MAXIMUM,
                     reserve=lambda: context.charge(bound_calls=1, bound_steps=SOLVES_PER_BOX))
    witness = outcome['witness']
    if witness is not None:
        scores = {case.index: score_case(case, witness) for case in original}
        if not all(row['within_reference'] for row in scores.values()):
            raise ValueError('compatibility witness did not reproduce in metres')
        outcome['witness_scores'] = scores
    result = dict(outcome, windows=indices, law=law, passed=True, scientific_decision='abstain')
    context.save_bytes('compatibility.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or len(study.rows) != len(LAWS):
            raise ValueError('both complete feasibility tasks are required')
        settings = [study.artifact(law, 'compatibility.json') for law in LAWS]
        if study.summary['charged']['bound_calls'] != sum(row['checked'] for row in settings):
            raise ValueError('the searched boxes differ from the sealed charge')
        raw = encoded(dict(manifest_sha256=study.completion['manifest_sha256'],
                           settings=settings, scientific_decision='abstain'))
    out = root/RESULT
    if not out.exists():
        atomic(out, raw)
    if out.read_bytes() != raw:
        raise ValueError('saved compatibility report differs')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.esa_component_scale_feasibility {prepare,report}')
    command(Path.cwd())
