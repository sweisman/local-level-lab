# SPDX-License-Identifier: AGPL-3.0-or-later
"""Locate error that remains after allowing the saved covariance components."""

from contextlib import closing
import json
import math
from pathlib import Path
import sys

from .esa_component_scale_feasibility import ID as PARENT, RESULT as PARENT_REPORT
from .esa_component_scale_transfer import COMPONENTS, LAWS, REPORTS, make_case, read_case
from .esa_scored_path_shape import BASE
from .esa_whitened_scale_transfer import whiten
from .studies.artifacts import atomic, digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-forecast-error-localization-v1'
PLAN = BASE+'ESA_FORECAST_ERROR_LOCALIZATION_PLAN.md'
RESULT = BASE+'esa-forecast-error-localization-result.json'
SCOPE = 'localization of covariance-incompatible errors in eight saved ESA 187 forecasts'
PARENT_MANIFEST = 'b9bd7501227cbd48b4b7d260c2aa951a301af3af7cbb8131387cdd10fd510c95'
PARENT_REPORT_SHA = '2fbab18fc6139fafd16e8de17bc0d979de4e7fe16b867e7ea7884fc7098804c2'
AXES = ('north', 'east', 'up')
BLOCK = 30
COUNT = 8*5*4


def marginal(case, indices):
    import numpy as np

    covariance = case.component_covariance[0][np.ix_(indices, indices)]
    selected = {key: case.roots[key][indices] for key in COMPONENTS[1:]}
    selected['native'] = np.linalg.cholesky(covariance)
    return make_case(case.index, selected, case.error[indices])


def contrast(case, *, maximum_ratio):
    import numpy as np

    roots = [case.roots[key] for key in COMPONENTS[1:]]
    y = case.error
    left, s, _ = np.linalg.svd(np.column_stack(roots), full_matrices=False)
    # Rank determines only the witness direction. The bound still includes
    # all covariance columns, including any omitted from the projection.
    rank = int(np.count_nonzero(s > s[0]*1e-12)) if len(s) else 0
    supported = left[:, :rank]
    residual = y - supported @ (supported.T @ y)
    norm = float(np.linalg.norm(residual))
    y_norm = float(np.linalg.norm(y))
    pad = 128*np.finfo(float).eps*len(y)
    lower = 0.
    if norm > pad*max(1., y_norm):
        u = residual/norm
        numerator = max(0., abs(float(u @ y)) - pad*max(1., y_norm))
        effect = sum((np.linalg.norm(root.T @ u) + pad*np.linalg.norm(root))**2
                     for root in roots)
        denominator = float(u @ u)*(1.+pad) + maximum_ratio*effect
        lower = max(0., math.nextafter(numerator**2/denominator, -math.inf))
    return dict(lower_bound=lower, native_only_energy=y_norm**2, added_root_rank=rank,
                residual_projection_energy=norm**2, coordinates=len(y))


def task_for(law):
    return dict(identity=law, input_key='design', payload=dict(law=law),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=COUNT, bound_steps=COUNT))


def prepare(root):
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('retain the first localization study')
    if digest((root/PARENT_REPORT).read_bytes()) != PARENT_REPORT_SHA:
        raise ValueError('the frozen variance-range report is required')
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if parent.completion['manifest_sha256'] != PARENT_MANIFEST or not parent.summary['passed']:
            raise ValueError('the verified variance-range archive is required')
        design = parent.input('design')
        windows = [index for pair in design['pairs'] for index in pair]
        keys = ['design', *(f'observed-{index}' for index in windows)]
        keys.extend(f'forecast-{index}-{law}' for index in windows for law in LAWS)
        materials = {key: parent.input(key, raw=True) for key in keys}
    inputs = dict(plan=PLAN, compatibility=PARENT_REPORT)
    for name, raw in materials.items():
        path = 'data/'+ID+'-inputs/'+name
        atomic(root/path, raw)
        inputs[name] = path
    adapter = Path(__file__).relative_to(root).as_posix()
    definition = dict(id=ID, scope=SCOPE, inputs=inputs, adapter=adapter,
        tasks=[task_for(law) for law in LAWS], workers=1, threads=1, maximum_wall_s=120.,
        sources=source_closure(root, [adapter, PLAN, 'analysis/tests/test_esa_forecast_error_localization.py']))
    print(encoded(Definition.from_dict(definition, root).prepare(root)['limits']).decode(), end='')


def slices(case, context, *, maximum_ratio, variance_upper):
    import numpy as np

    selectors = dict(all=(0, 1, 2), **{axis: (i,) for i, axis in enumerate(AXES)})
    blocks = [(0, REPORTS), *((i, i+BLOCK) for i in range(0, REPORTS, BLOCK))]
    result = []
    for first, last in blocks:
        for name, axes in selectors.items():
            context.charge(bound_calls=1, bound_steps=1)
            indices = (3*np.arange(first, last)[:, None] + np.array(axes)).ravel()
            part, _ = whiten(marginal(case, indices))
            bounds = contrast(part, maximum_ratio=maximum_ratio)
            result.append(dict(first=first, stop=last, axis=name, **bounds,
                               joint_score_lower=bounds['lower_bound']/variance_upper))
    return result


def evaluate(task, context):
    def load(key):
        return json.loads(context.input_path(key).read_bytes())

    law = task['payload']['law']
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if context.manifest['scope'] != SCOPE or law not in LAWS or declared != task_for(law):
        raise ValueError('exact variance localization task required')
    design = load('design')
    windows = [i for pair in design['pairs'] for i in pair]
    previous = load('compatibility')
    reference = next(row for row in previous['settings'] if row['law'] == law)
    if (reference['status'] != 'incompatible' or reference['open'] or reference['windows'] != windows
            or len(reference['excluded']) != 1 or reference['excluded'][0]['box'] != reference['root']):
        raise ValueError('exact full-range exclusion required')
    excluded = reference['excluded'][0]
    variance_upper = excluded['native_interval'][1]
    hard, quiet = (windows[index] for index in excluded['active_limits'])
    maximum_ratio = math.exp(max(side[1] for side in reference['root']))
    contributions = []
    for index in windows:
        case = read_case(context, index, law, design['scores'][f'{index}-{law}'])
        contributions.append(dict(index=index, slices=slices(case, context,
                    maximum_ratio=maximum_ratio, variance_upper=variance_upper)))
    result = dict(law=law, windows=contributions, native_variance_upper=variance_upper,
        hard_window=hard, quiet_window=quiet, joint_reference_upper=reference['reference'][1],
        maximum_ratio=maximum_ratio, passed=True, scientific_decision='abstain')
    context.save_bytes('localization.json', encoded(result))
    return result


def report(root):
    with closing(ClosedStudy(root, 'data/'+ID)) as study:
        if not study.summary['passed'] or study.summary['charged']['bound_calls'] != COUNT*len(LAWS):
            raise ValueError('all planned localization contrasts must have completed')
        raw = encoded(dict(manifest_sha256=study.completion['manifest_sha256'],
            settings=[study.artifact(law, 'localization.json') for law in LAWS],
            scientific_decision='abstain'))
    path = root/RESULT
    if not path.exists():
        atomic(path, raw)
    if path.read_bytes() != raw:
        raise ValueError('the localization summary differs from the saved report')
    print(digest(raw))


if __name__ == '__main__':
    command = {'prepare': prepare, 'report': report}.get(sys.argv[1] if len(sys.argv) == 2 else '')
    if command is None:
        raise SystemExit('usage: python -m lll.esa_forecast_error_localization {prepare,report}')
    command(Path.cwd())
