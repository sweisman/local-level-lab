# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate ranking and accuracy margins for the four saved NASA forecasts."""

from contextlib import ExitStack, closing
import json
from pathlib import Path

from . import ilvis0_matched_four_group_audit as audit
from . import ilvis0_matched_imu21_receiver_hull as shared
from .ilvis0_matched_observed_inputs import _write_equal
from .ilvis0_prediction_observed import accuracy_screen
from .studies.artifacts import digest, encoded


ID = 'ilvis0-matched-common-error-margin-v1'
SCOPE = 'Additional common receiver error for the four exact retrospective NASA forecast groups'
PLAN = audit.FOLDER+'MATCHED_COMMON_ERROR_MARGIN_PLAN.md'
AUDIT_HASH = '62dab24f92303c047315e4015420c30f604e921219a18bcd1ecd6fb6e26639c9'
NEEDED_RANKINGS = ('shape_zero_field', 'shape_specified_field', 'field_globe')
PREFERRED = 'sphere_rotating'


def rms_margin(distances, limit):
    """Positive radius that brings RMS of outward-displaced errors to the limit."""
    import math

    import numpy as np

    squared_room = limit**2-float(np.mean(distances**2))
    if squared_room <= 0.:
        return 0.
    mean = float(np.mean(distances))
    return squared_room/(mean+math.sqrt(mean**2+squared_room))


def accuracy_margin(path, hull):
    import numpy as np

    from .ilvis0_matched_extension_receiver_hull import worst_accuracy

    check = worst_accuracy(path, hull)
    differences = path[:, None, :]-hull
    horizontal = np.linalg.norm(differences[:, :, :2], axis=2).max(axis=1)
    height = np.abs(differences[:, :, 2]).max(axis=1)
    limits = check['accuracy']['limits']
    margins = dict(horizontal_rms_m=rms_margin(horizontal, limits['horizontal_rms_m']),
        vertical_rms_m=rms_margin(height, limits['vertical_rms_m']),
        maximum_horizontal_m=max(0., limits['maximum_horizontal_m']-float(horizontal.max())),
        maximum_absolute_up_m=max(0., limits['maximum_absolute_up_m']-float(height.max())))
    first = min(margins, key=margins.get)
    return dict(all_limits_hold_at_zero=check['accuracy']['passed'], limits_m=limits,
                limiting_metric=first, margins_m=margins, additional_radius_m=margins[first],
                zero_radius_scores={metric: check['worst_'+metric] for metric in limits})


def prepare(root):
    from . import ilvis0_matched_extension_forecast as extension
    from . import ilvis0_matched_unstarted_report as recovered
    from .studies.closed import ClosedStudy
    from .studies.dependencies import source_closure
    from .studies.runtime import Definition

    if (root/'data'/ID).exists():
        raise ValueError('preserve the existing common-error study')
    raw = (root/audit.RESULT).read_bytes()
    selection_raw = (root/audit.SELECTION).read_bytes()
    if digest(raw) != AUDIT_HASH or digest(selection_raw) != audit.SELECTION_SHA:
        raise ValueError('exact matched audit and metadata-only selection required')
    prior = json.loads(raw)
    selected = {r['group_id']: r for r in json.loads(selection_raw)['candidates']}
    inputs, tasks = dict(audit=audit.RESULT, selection=audit.SELECTION), []
    with ExitStack() as stack:
        original = stack.enter_context(closing(ClosedStudy(root, recovered.ARCHIVE)))
        extra = stack.enter_context(closing(ClosedStudy(root, audit.RECOVERED, store=original.store)))
        added = stack.enter_context(closing(ClosedStudy(root, 'data/'+extension.ID, store=original.store)))
        if [study.completion for study in (original, extra, added)] != prior['source_completions']:
            raise ValueError('the exact audited study closures are required')
        for group in prior['groups']:
            segment = group['segment_id']
            metadata = selected[group['group_id']]
            if metadata['segment_id'] != segment:
                raise ValueError('changed four-group selection')
            base = original if metadata['prior_preflight_group'] else added
            material = {key: base.input(segment+'-'+key) for key in ('queries', 'scoring')}
            forecasts, dispositions = {}, {}
            for model in shared.MODELS:
                identity = segment+'-'+model
                study = extra if identity == recovered.IDENTITY else base
                envelope = study.envelope(identity) if identity in study.rows else None
                status = audit.disposition(envelope['result'] if envelope else None)
                if status != group['attempts'][model]['status']:
                    raise ValueError('a numerical disposition changed: '+identity)
                dispositions[model] = status
                if status == 'scorable':
                    forecasts[model] = study.artifact(identity, 'forecast.json')
            material.update(forecasts=forecasts, statuses=dispositions, group_id=group['group_id'],
                            segment_id=segment, imu_type=group['imu_type'])
            name = f'data/{ID}-inputs/{segment}.json'
            _write_equal(root/name, encoded(material))
            inputs[segment] = name
            budget = len(forecasts)+sum(a in forecasts and b in forecasts for _, a, b in shared.PAIRS)
            tasks.append(dict(identity=segment, input_key=segment, payload=dict(group_id=group['group_id']),
                limits=dict(native_calls=0, packet_visits=0, bound_calls=budget, bound_steps=budget)))
    if len(tasks) != 4 or len(selected) != 4 or sum(t['limits']['bound_calls'] for t in tasks) != 29:
        raise ValueError('four audited groups and 29 existing calculations are required')
    adapter = Path(__file__).relative_to(root).as_posix()
    sources = source_closure(root, [adapter, PLAN, 'analysis/tests/test_ilvis0_matched_common_error_margin.py'])
    definition = dict(id=ID, scope=SCOPE, adapter=adapter, inputs=inputs, sources=sources,
                      tasks=tasks, workers=1, threads=1, maximum_wall_s=60.)
    return Definition.from_dict(definition, root).prepare(root)['limits']


def evaluate(task, context):
    import numpy as np

    from .ilvis0_solver_position import physical_metric

    if context.manifest['scope'] != SCOPE:
        raise ValueError('only the matched common-error study is allowed')
    data = json.loads(context.input_path().read_bytes())
    scoring, queries = data['scoring'], data['queries']
    times, cut = queries['query_times_s'], queries['training_epochs']
    if (data['segment_id'] != task['identity'] or data['group_id'] != task['payload']['group_id']
            or times[cut:] != scoring['query_times_s'] or set(scoring['coordinates']) != set(shared.TRACKS)):
        raise ValueError('unchanged held-out support required')
    reference = np.asarray(scoring['coordinates']['onboard'], float)
    metric = physical_metric(reference)
    hull = np.stack([shared._local(scoring['coordinates'][track], reference, metric)
                     for track in shared.TRACKS], axis=1)
    predictions, margins = {}, {}
    for model, forecast in data['forecasts'].items():
        if forecast['training_epochs'] != cut or forecast['query_times_s'] != times or forecast['later_positions_used']:
            raise ValueError('the forecast used different support or observations')
        context.charge(bound_calls=1, bound_steps=1)
        path = shared._local(forecast['coordinates'][cut:], reference, metric)
        predictions[model] = path
        margins[model] = accuracy_margin(path, hull)
    rankings = {}
    for label, a, b in shared.PAIRS:
        if a in predictions and b in predictions:
            context.charge(bound_calls=1, bound_steps=1)
            rankings[label] = shared.paired_range(predictions[a], predictions[b], hull)
        else:
            rankings[label] = None
    shape_and_field = [rankings[name] for name in NEEDED_RANKINGS]
    ordered = all(rank is not None and rank['ordering'] == 'first' for rank in shape_and_field)
    joint = (min(margins[PREFERRED]['additional_radius_m'],
                 *(rank['additional_radius_for_tie_m'] for rank in shape_and_field)) if ordered else None)
    result = dict(group_id=data['group_id'], segment_id=data['segment_id'], imu_type=data['imu_type'],
        epochs=len(reference), fit_dispositions=data['statuses'], absolute_accuracy=margins,
        paired_rankings=rankings, joint_additional_radius_m=joint, new_fits=0, new_propagations=0,
        actual_receiver_error_estimated=False, scientific_decision='abstain')
    context.save_bytes('common-error-margin.json', encoded(result))
    return dict(passed=True, scientific_decision='abstain')
