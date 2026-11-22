# SPDX-License-Identifier: AGPL-3.0-or-later
"""Known-answer checks for a group-level two-stage prediction decision."""

import hashlib
import json
from pathlib import Path

import pytest


MODELS = ('flat_still', 'sphere_still', 'sphere_rotating')
PLAN = 'a'*64
SETTINGS = ('nominal', 'sensitivity')


def group(identity, values, *, true_model=None, adequate=True):
    outcome = dict(group_id=identity, protocol_sha256=PLAN, settings={
        setting: {model: dict(score=score, adequate=adequate)
                  for model, score in zip(MODELS, scores)}
        for setting, scores in zip(SETTINGS, values, strict=True)})
    if true_model is not None:
        outcome['true_model'] = true_model
    return outcome


def baseline():
    return [group(f'{model}-{i}', [(0, 0, 0)]*2, true_model=model)
            for model in MODELS for i in range(4)]


def reference_design(calibration):
    return {model: {'fixed': [r['group_id'] for r in calibration if r['true_model'] == model]}
            for model in MODELS}


def assess(query, calibration, alpha=.2, *, planned_draws=None):
    from lll.prediction_group_decision import compare_group

    return compare_group(query, calibration, protocol_sha256=PLAN,
                         settings=SETTINGS, alpha=alpha,
                         planned_draws=reference_design(calibration) if planned_draws is None else planned_draws)


@pytest.mark.parametrize(('scores', 'shape', 'field'), [
    ((8, 7, 0), 'globe', 'specified'),
    ((8, 0, 7), 'globe', 'zero'),
    ((8, 0, 0), 'globe', 'abstain'),
    ((0, 8, 7), 'disc', 'abstain'),
    ((0, 8, 0), 'abstain', 'abstain'),
])
def test_hierarchy_requires_shape_before_field(scores, shape, field):
    result = assess(group('query', [scores]*2), baseline())
    assert (result['shape'], result['field']) == (shape, field)
    assert result['scientific_decision'] == 'abstain'


def test_decisions_retain_a_candidate_that_wins_one_setting():
    result = assess(group('query', [(8, 4, 0), (0, 4, 8)]), baseline())
    assert result['p_values'] == dict(flat_still=1., sphere_still=.2, sphere_rotating=1.)
    assert result['shape'] == 'abstain'


def test_inadequacy_abstains_without_excluding_the_only_survivor():
    result = assess(group('query', [(9, 8, 0)]*2, adequate=False), baseline())
    assert result['retained_models'] == ['sphere_rotating']
    assert result['shape'] == result['field'] == 'abstain'


def test_unavailable_calibration_is_counted_in_the_tail():
    calibration = baseline()
    planned = reference_design(calibration)
    calibration[0]['settings'].pop('nominal')
    query = group('query', [(9, 8, 0)]*2)
    result = assess(query, calibration, planned_draws=planned)
    assert result == assess(query, calibration[1:], planned_draws=planned)
    assert result['p_values']['flat_still'] == .4
    assert result['shape'] == 'abstain'


def test_incomplete_query_or_absent_truth_stratum_abstains():
    query = group('query', [(9, 8, 0)]*2)
    assert assess(query, baseline()[:-4])['shape'] == 'abstain'
    query['settings']['nominal']['flat_still'] = None
    result = assess(query, baseline())
    assert result['shape'] == result['field'] == 'abstain'
    assert result['p_values'] == dict.fromkeys(MODELS)


def test_small_cohort_cannot_exclude_a_candidate_at_five_percent():
    result = assess(group('query', [(9, 8, 0)]*2), baseline(), .05)
    assert result['retained_models'] == list(MODELS)


def test_incomplete_reference_scenario_vetoes_rejection_in_other_scenarios():
    calibration = baseline()
    planned = reference_design(calibration)
    planned['flat_still']['other'] = ['missing-disc-reference']
    result = assess(group('query', [(9, 8, 0)]*2), calibration, planned_draws=planned)
    rank = result['ranks']['flat_still']
    assert rank['by_scenario']['fixed']['p_value'] == .2
    assert rank['by_scenario']['other']['p_value'] == result['p_values']['flat_still'] == 1.
    assert result['shape'] == 'abstain'


def test_group_score_records_feed_the_existing_cohort_rule():
    from lll.flight_group_decision import assess as cohort_decision

    calibration = baseline()
    groups = ['first', 'second']
    rows = {name: assess(group(name, [(9, 8, 0)]*2), calibration)['cohort_row']
            for name in groups}
    result = cohort_decision(groups, rows, minimum_groups=2, alpha=.2)
    assert (result['shape'], result['field']) == ('globe', 'specified')
    result = cohort_decision(groups, {'first': rows['first']}, minimum_groups=2, alpha=.2)
    assert result['shape'] == result['field'] == 'abstain'


@pytest.mark.parametrize('truth', MODELS)
def test_absolute_null_rank_protects_truth_under_every_query_assignment(truth):
    from lll.prediction_group_decision import compare_group

    # Losses are identical across the two settings. The closest competitor has
    # loss 1, so the truth's query gaps are 0, 1, 2, 3 and 4. Reference losses
    # keep that shared error, making exclusion harder than a matched gap rank.
    rows = [group(f'draw-{loss}', [tuple(loss if model == truth else 1 for model in MODELS)]*2,
                  true_model=truth) for loss in range(1, 6)]
    other_references = [record for record in baseline() if record['true_model'] != truth]
    ranks = []
    for index, row in enumerate(rows):
        query = {key: value for key, value in row.items() if key != 'true_model'}
        references = [*other_references, *rows[:index], *rows[index+1:]]
        references = [dict(record, settings={key: {record['true_model']: values[record['true_model']]}
                                            for key, values in record['settings'].items()}) for record in references]
        result = compare_group(query, references, protocol_sha256=PLAN, settings=SETTINGS,
                               planned_draws=reference_design(references), alpha=.2,
                               absolute_null=True)
        ranks.append(result['p_values'][truth])
        assert result['scientific_decision'] == 'abstain'
    assert ranks == [1., 1., .8, .6, .4]


def test_absolute_null_retains_failed_references_and_vetoes_incomplete_queries():
    from lll.prediction_group_decision import compare_group

    calibration = baseline()
    planned = reference_design(calibration)
    for record in calibration:
        for values in record['settings'].values():
            own = values[record['true_model']]
            values.clear()
            values[record['true_model']] = own
    calibration[0]['settings'].pop('nominal')
    query = group('query', [(9, 8, 0)]*2)
    options = dict(protocol_sha256=PLAN, settings=SETTINGS, planned_draws=planned,
                   alpha=.2, absolute_null=True)
    result = compare_group(query, calibration, **options)
    assert result['p_values'] == dict(flat_still=.4, sphere_still=.2, sphere_rotating=1.)
    assert result['shape'] == result['field'] == 'abstain'
    query['settings']['nominal']['flat_still'] = None
    assert compare_group(query, calibration, **options)['status'] == 'incomplete_query'
    calibration[0]['settings']['sensitivity']['sphere_still'] = dict(score=0, adequate=True)
    with pytest.raises(ValueError, match='declared model scores'):
        compare_group(query, calibration, **options)


def test_absolute_null_uses_minimum_reference_loss_and_minimum_query_gap():
    from lll.prediction_group_decision import compare_group

    references = [dict(group_id=record['group_id'], true_model=record['true_model'],
                       protocol_sha256=PLAN, settings={setting: {
                           record['true_model']: dict(score=loss, adequate=True)}
                           for setting, loss in zip(SETTINGS, losses, strict=True)})
                  for record, losses in zip(baseline(), [(9, 2), (4, 4)] + [(0, 0)]*10, strict=True)]
    result = compare_group(group('query', [(10, 2, 2), (5, 2, 2)]), references,
                           protocol_sha256=PLAN, settings=SETTINGS,
                           planned_draws=reference_design(references), alpha=.2, absolute_null=True)
    assert result['scores']['flat_still'] == 3
    assert result['p_values']['flat_still'] == .4


def test_matched_group_work_preserves_missing_and_pending_reference_status():
    from lll.group_cohort_work import cohort_rank_work
    from lll.prediction_group_decision import compare_group_work

    calibration = baseline()
    planned = reference_design(calibration)
    calibration[0]['settings'].pop('nominal')  # A sealed failure.
    calibration.pop(1)  # A planned but unfinished draw.
    queries = [group(name, [(9, 8, 0)]*2) for name in ('first', 'second')]
    options = dict(protocol_sha256=PLAN, settings=SETTINGS, planned_draws=planned,
                   group_count=2, minimum_groups=2, alpha=.6)
    rows = {query['group_id']: compare_group_work(query, calibration, **options) for query in queries}
    audit = cohort_rank_work(rows, rows, minimum_groups=2, alpha=.6)
    assert audit['decision_fixed'] and audit['pending_draw_slots'] == 2
    assert audit['possible_decisions'] == [dict(shape='globe', field='specified')]
    disc = rows['first']['ranks']['flat_still']
    assert (disc['p_value_min'], disc['p_value_max']) == (.4, .6)
    assert audit['conservative']['tests']['globe']['p_value'] == .6

    queries[0]['settings'].pop('nominal')
    with pytest.raises(ValueError, match='sealed target'):
        compare_group_work(queries[0], calibration, **options)


@pytest.mark.parametrize('problem', ['duplicate', 'leakage', 'protocol', 'setting', 'score'])
def test_invalid_contract_is_rejected(problem):
    query, calibration = group('query', [(9, 8, 0)]*2), baseline()
    if problem == 'duplicate':
        calibration.append(calibration[0])
    elif problem == 'leakage':
        calibration[0]['group_id'] = 'query'
    elif problem == 'protocol':
        calibration[0]['protocol_sha256'] = 'b'*64
    elif problem == 'setting':
        query['settings']['unplanned'] = query['settings']['nominal']
    else:
        query['settings']['nominal']['flat_still']['score'] = float('nan')
    with pytest.raises(ValueError):
        assess(query, calibration)


@pytest.mark.parametrize('truth', MODELS)
def test_rank_bound_under_all_query_assignments(truth):
    rival = 'sphere_still' if truth == 'sphere_rotating' else 'sphere_rotating'
    values = []
    for gap in range(5):
        scores = [0 if model == rival else gap if model == truth else 9 for model in MODELS]
        values.append(group(f'known-{gap}', [scores, [3*v for v in scores]], true_model=truth))
    controls = [record for record in baseline() if record['true_model'] != truth]
    results = []
    for i, row in enumerate(values):
        query = {key: value for key, value in row.items() if key != 'true_model'}
        results.append(assess(query, [*controls, *values[:i], *values[i+1:]]))
    assert [r['p_values'][truth] for r in results] == [1., .8, .6, .4, .2]
    assert sum(truth not in r['retained_models'] for r in results) == 1
    if truth == 'flat_still':
        errors = [r for r in results if r['shape'] == 'globe']
    elif truth == 'sphere_still':
        errors = [r for r in results if r['field'] == 'specified']
    else:
        errors = [r for r in results if r['field'] == 'zero']
    assert errors == results[-1:]


@pytest.mark.parametrize('absolute_null', [False, True])
def test_saved_three_candidate_control_has_insufficient_calibration_rank(absolute_null):
    from lll.prediction_group_decision import compare_group

    root = Path(__file__).resolve().parents[2]
    raw = (root/'docs/prediction-observed-development/matched-candidates-full-result.json').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == '7abafc8681b4f53ae59769f4d69f09fea407d3701f48aafefce96f791d192b35'
    report = json.loads(raw)
    protocol = report['manifest_sha256']
    settings = ('saved-generated-comparison',)
    records = []
    for identity, row in report['cases'].items():
        truth, _, _ = identity.rsplit('-', 2)
        assert truth in MODELS and row['technical_passed']
        scores = {model: dict(score=row['receiver_horizontal_rms_m'][model],
                              adequate=row['receiver_covered'][model])
                  if row['numerical_converged'][model] else None for model in MODELS}
        records.append(dict(group_id=identity, true_model=truth, protocol_sha256=protocol,
                            settings={settings[0]: scores}))
    assert len(records) == 12
    for row in records:
        query = {key: value for key, value in row.items() if key != 'true_model'}
        calibration = []
        for record in records:
            if record is row:
                continue
            if absolute_null:
                truth = record['true_model']
                record = dict(record, settings={key: {truth: values[truth]} for key, values in record['settings'].items()})
            calibration.append(record)
        outcome = compare_group(query, calibration, protocol_sha256=protocol, settings=settings,
                                planned_draws=reference_design(calibration), alpha=.05,
                                absolute_null=absolute_null)
        assert outcome['status'] == 'scored'
        assert sorted(outcome['calibration_counts'].values()) == [3, 4, 4]
        assert min(outcome['p_values'].values()) >= .2
        assert outcome['shape'] == outcome['field'] == 'abstain'
