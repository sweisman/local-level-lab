# SPDX-License-Identifier: AGPL-3.0-or-later
"""Hold out ESA forecast pairs while selecting temporal innovation persistence."""

import argparse
from contextlib import ExitStack, closing
from itertools import product
import json
import math
from pathlib import Path

from .esa_axis_innovation_scale import ID as PARENT, RESULT as PRIOR
from .esa_motion_innovation_scale import BASE, LAWS, InnovationScore, scorer
from .ilvis0_matched_observed_inputs import _write_equal
from .studies.artifacts import digest, encoded
from .studies.closed import ClosedStudy


ID = 'esa-innovation-persistence-v1'
SCOPE = 'Leave-one-pair-out temporal dependence of ESA 187 forecast innovations'
PLAN = BASE+'ESA_INNOVATION_PERSISTENCE_PLAN.md'
RESULT = BASE+'esa-innovation-persistence-result.json'
REQUEST = BASE+'esa-innovation-persistence-qualification.json'
REPORT = BASE+'esa-innovation-persistence-tests.xml'
PRIOR_SHA = '3a24ea4ef30ebdbe47170be87ba90557e49f90d577d3d9b152e40131412b42c4'
TEST = 'analysis/tests/test_esa_innovation_persistence.py'
TESTS = ('test_causal_transition_uses_elapsed_time_and_current_motion',
         'test_temporal_innovation_score_matches_independent_dense_covariance',
         'test_zero_memory_reproduces_the_saved_diagonal_correction',
         'test_memory_search_charges_each_setting_and_selects_only_on_donors')
MEMORY_S = (0., .25, .5, 1., 2., 4., 8., 16., 32., 64.)
CANDIDATES = len(MEMORY_S)**2
MODES = ('diagonal', 'common', 'motion')
LIMITS = dict(native_calls=0, packet_visits=0, bound_calls=8+CANDIDATES+6,
              bound_steps=16+6*CANDIDATES+6)


def transitions(times, response, quiet, motion):
    import numpy as np

    times, weight = (np.asarray(x, float) for x in (times, response))
    if (times.ndim != 1 or len(times) < 2 or weight.shape != times.shape
            or not np.isfinite(times).all() or not np.isfinite(weight).all()
            or np.any(np.diff(times) <= 0.) or np.any((weight < 0.) | (weight > 1.))
            or not all(math.isfinite(v) and v >= 0. for v in (quiet, motion))):
        raise ValueError('ordered forecasts, causal motion and finite memory required')
    dt = np.diff(times)
    quiet_phi = np.exp(-dt/quiet) if quiet > 0. else np.zeros_like(dt)
    motion_phi = np.exp(-dt/motion) if motion > 0. else np.zeros_like(dt)
    return (1.-weight[1:])*quiet_phi+weight[1:]*motion_phi


class PersistenceScore:
    """Normalize temporal innovations before scoring the unchanged added roots."""

    def __init__(self, baseline, times, log_scales):
        import numpy as np

        logs = np.asarray(log_scales, float)
        weight = baseline.weight.reshape(-1, 3)
        if (logs.shape != (4,) or not np.isfinite(logs).all() or len(weight) != len(times)
                or not np.array_equal(weight, np.broadcast_to(weight[:, :1], weight.shape))):
            raise ValueError('exact saved axis-quiet scales and coincident motion slots required')
        self.times, self.response = times, weight[:, 0]
        scales = np.exp(logs)
        variance = (scales[:3]+scales[3]*weight).ravel()
        if not np.isfinite(variance).all() or np.any(variance <= 0.):
            raise ValueError('finite positive native variances required')
        data = np.column_stack((baseline.y, baseline.root))/np.sqrt(variance)[:, None]
        self.data = data.reshape(len(times), 3, -1)
        self.log_normalization = (baseline.normalization-.5*len(baseline.y)*math.log(2.*math.pi)
                                  +.5*float(np.log(variance).sum()))

    def score(self, quiet, motion):
        import numpy as np

        phi = transitions(self.times, self.response, quiet, motion)
        sigma = np.sqrt((1.-phi)*(1.+phi))
        if np.any(sigma <= 0.):
            raise ValueError('strictly positive innovation variance required')
        innovations = self.data.copy()
        innovations[1:] = (self.data[1:]-phi[:, None, None]*self.data[:-1])/sigma[:, None, None]
        flat = innovations.reshape(-1, innovations.shape[-1])
        normalization = self.log_normalization+3.*float(np.log(sigma).sum())
        return InnovationScore(flat[:, 0], flat[:, 1:], np.zeros(len(flat)), normalization).score(1., 0.)


def select_memory(donors, *, reserve):
    if len(donors) != 6:
        raise ValueError('exact six donor windows required')
    scores = []
    for quiet, motion in product(MEMORY_S, repeat=2):
        reserve()
        loss = math.fsum(case.score(quiet, motion)['negative_log_score'] for case in donors)
        if not math.isfinite(loss):
            raise ValueError('finite donor score required')
        scores.append((loss, quiet, motion))
    choices = dict(common=min(row for row in scores if row[1] == row[2]), motion=min(scores))
    return {key: dict(seconds=[quiet, motion], donor_log_score=loss)
            for key, (loss, quiet, motion) in choices.items()}


def task_for(pair, law):
    return dict(identity=f'{pair[0]}-{law}', input_key='design', payload=dict(pair=pair, law=law), limits=LIMITS)


def qualification(root, *, check):
    from .ilvis0_control_shards import runtime_environment
    from .studies.dependencies import source_closure
    from .studies.qualification import checked, request

    sources = source_closure(root, (Path(__file__).relative_to(root).as_posix(), PLAN, TEST))
    environment = runtime_environment()
    if not check:
        return request(root, sources=sources, environment=environment, output=REQUEST, report=REPORT)
    checked(root, REQUEST, sources=sources, environment=environment, required_tests=TESTS, minimum_tests=len(TESTS))
    return sources


def prepare(root):
    from .ilvis0_control_shards import runtime_environment
    from .ilvis0_gps_reconstruction_extension import RECOVERY, RECOVERY_POLICY
    from .studies.qualification import checked
    from .studies.runtime import Definition
    from .studies.task_resume import REQUIRED_TESTS, qualification_sources

    if (root/'data'/ID/'manifest.json').exists():
        raise ValueError('retain the existing persistence study')
    prior_raw = (root/PRIOR).read_bytes()
    if digest(prior_raw) != PRIOR_SHA:
        raise ValueError('exact earlier axis-scale study report required')
    prior = json.loads(prior_raw)
    sources = qualification(root, check=True)
    recovery, tests = checked(root, RECOVERY, sources=qualification_sources(root), environment=runtime_environment(),
                              required_tests=REQUIRED_TESTS, minimum_tests=len(REQUIRED_TESTS))
    with closing(ClosedStudy(root, 'data/'+PARENT)) as parent:
        if (not parent.summary['passed'] or len(parent.rows) != 8
                or any(prior[key] != value for key, value in parent.completion.items())):
            raise ValueError('eight verified donor-only scale selections required')
        design = parent.input('design')
        windows = [i for pair in design['pairs'] for i in pair]
        if len(design['pairs']) != 4 or len(windows) != 8 or len(set(windows)) != 8:
            raise ValueError('exact four nonoverlapping forecast pairs required')
        tasks = [task_for(pair, law) for pair in design['pairs'] for law in LAWS]
        known = {f'{row["pair"][0]}-{row["law"]}': row for row in prior['folds']}
        keys = ['design', *(f'observed-{i}' for i in windows)]
        keys.extend(f'forecast-{i}-{law}' for i in windows for law in LAWS)
        materials = {key: parent.input(key, raw=True) for key in keys}
        for task in tasks:
            identity = task['identity']
            row = parent.artifact(identity, 'axis-scale.json')
            if row != known[identity] or row != parent.envelope(identity)['result']:
                raise ValueError('archived diagonal comparator differs from its seal')
            materials[identity] = encoded(row)
    materials.update(recovery=recovery, recovery_tests=tests, recovery_policy=encoded(RECOVERY_POLICY))
    inputs = dict(plan=PLAN, prior=PRIOR, qualification=REQUEST, qualification_tests=REPORT)
    for key, value in materials.items():
        name = f'data/{ID}-inputs/{key}'
        _write_equal(root/name, value)
        inputs[key] = name
    definition = dict(id=ID, scope=SCOPE, adapter=Path(__file__).relative_to(root).as_posix(), inputs=inputs,
                         sources=sources, tasks=tasks, workers=2, threads=1, maximum_wall_s=180.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    law, pair = (task['payload'][key] for key in ('law', 'pair'))
    design = json.loads(context.input_path('design').read_bytes())
    declared = {key: value for key, value in task.items() if key not in ('index', 'shard')}
    if (context.manifest['scope'] != SCOPE or pair not in design['pairs'] or law not in LAWS
            or declared != task_for(pair, law)):
        raise ValueError('exact frozen persistence fold required')
    original = json.loads(context.input_path(task['identity']).read_bytes())
    donors = [index for other in design['pairs'] for index in other if index not in pair]
    if original['pair'] != pair or original['law'] != law or original['fitting'] != donors:
        raise ValueError('same six donor windows required for variance and memory selection')
    scales = original['selected']['axis_quiet']['log_scales']

    def read(index):
        saved = scorer(context, index, law, design['scores'][f'{index}-{law}'])
        forecast = json.loads(context.input_path(f'forecast-{index}-{law}').read_bytes())
        return PersistenceScore(saved, forecast['times_s'], scales)

    choices = select_memory([read(index) for index in donors], reserve=lambda: context.charge(bound_calls=1, bound_steps=6))
    context.save('donor-memory.json', dict(choices=choices, donors=donors, law=law, held_out=pair))
    held = []
    for index, previous in zip(pair, original['heldout'], strict=True):
        if index != previous['index']:
            raise ValueError('exact omitted scoring pair required')
        saved = read(index)
        scores = {}
        for key, seconds in [('diagonal', (0., 0.)), *((key, choices[key]['seconds']) for key in ('common', 'motion'))]:
            context.charge(bound_calls=1, bound_steps=1)
            scores[key] = saved.score(*seconds)
        if any(not math.isclose(scores['diagonal'][key], previous['scores']['axis_quiet'][key], rel_tol=1e-8, abs_tol=1e-8)
               for key in ('quadratic', 'negative_log_score')):
            raise ValueError('zero memory must reproduce the frozen diagonal score')
        held.append(dict(index=index, scores=scores))
    result = dict(law=law, pair=pair, donors=donors, choices=choices, heldout=held,
                  passed=True, new_fits=0, protected_reads=0, scientific_decision='abstain')
    context.save('persistence.json', result)
    return result


def report(root):
    from .studies.task_resume import resume_campaign
    from .studies.validation_resume import _stage_paths

    prefix = 'data/'+ID
    with ExitStack() as stack:
        parent = stack.enter_context(closing(ClosedStudy(root, prefix)))
        studies = [parent]
        if len(parent.rows) != len(parent.tasks) or any(parent.envelope(key)['status'] == 'interrupted' for key in parent.rows):
            continuation = root/(prefix+'-recovery')
            if resume_campaign(root, continuation, launch=False)['state'] != 'all_tasks_finished':
                raise ValueError('verified persistence continuation required')
            studies.extend(stack.enter_context(closing(ClosedStudy(root, path.relative_to(root).as_posix(),
                store=parent.store))) for path in _stage_paths(continuation))
        folds = {}
        for study in studies:
            for identity in study.rows:
                envelope = study.envelope(identity)
                if envelope['status'] == 'interrupted':
                    continue
                if identity in folds or identity not in parent.tasks or envelope['status'] != 'complete':
                    raise ValueError('one terminal result required per fit-free scoring task')
                row = envelope['result']
                if row['passed'] and (envelope['charged'] != LIMITS or row != study.artifact(identity, 'persistence.json')):
                    raise ValueError('scoring evidence differs from its source or charge limit')
                folds[identity] = row
        if len(folds) != 8 or parent.manifest['scope'] != SCOPE:
            raise ValueError('all eight frozen outcomes required')
        closures = {study.prefix: study.completion for study in studies}
    groups = {}
    for law in LAWS:
        held = [row for fold in folds.values() if fold['passed'] and fold['law'] == law for row in fold['heldout']]
        if len(held) != len({row['index'] for row in held}):
            raise ValueError('each window can be scored once per law')
        groups[law] = dict(windows=len(held), scores={name: dict(
            within_reference=sum(row['scores'][name]['within_reference'] for row in held),
            negative_log_score=math.fsum(row['scores'][name]['negative_log_score'] for row in held)) for name in MODES})
    gates = {name: all(group['windows'] == 8 and group['scores'][name]['within_reference'] == 8
        and group['scores'][name]['negative_log_score'] < group['scores']['diagonal']['negative_log_score']
        for group in groups.values()) for name in ('common', 'motion')}
    result = dict(groups=groups, gates=gates, folds=folds, closures=closures, new_fits=0, protected_reads=0,
                  scientific_decision='abstain')
    _write_equal(root/RESULT, encoded(result))
    return dict(groups=groups, gates=gates)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('request', 'prepare', 'report'))
    action = parser.parse_args().action
    root = Path.cwd()
    result = qualification(root, check=False) if action == 'request' else {'prepare': prepare, 'report': report}[action](root)
    print(json.dumps(result, sort_keys=True))
