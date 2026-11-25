# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import pytest

from lll.esa_confirmation_preflight import audit_plan, cohort_binding
from lll.studies.artifacts import digest


def metadata():
    return {
        'esa-group-a': dict(case='178a', training={'400': 'a400', '800': 'a800'}, withheld='afuture'),
        'esa-group-b': dict(case='179', training={'400': 'b400', '800': 'b800'}, withheld='bfuture'),
    }


def example_plan(root, evidence):
    (root/'docs').mkdir()
    references = {}
    for key in ('forecast_method', 'aircraft_error_model', 'physical_adequacy', 'decision_rule'):
        name = f'docs/{key}.md'
        raw = key.encode()
        (root/name).write_bytes(raw)
        references[key] = dict(path=name, sha256=digest(raw))
    return dict(version='esa-confirmation-preflight-v1',
                cohort_sha256=cohort_binding(evidence), groups=sorted(evidence), training_reports=[400],
                references=references)


def test_confirmation_preflight_binds_documents_without_authorizing_observed_fits(tmp_path):
    evidence = metadata()
    plan = example_plan(tmp_path, evidence)
    result = audit_plan(tmp_path, evidence, plan)
    assert result['binding_status'] == 'verified'
    assert result['observed_fits_authorized'] is False
    assert result['protected_outcome_reads'] == 0
    assert result['training_reports'] == [400]
    (tmp_path/plan['references']['aircraft_error_model']['path']).write_text('changed')
    with pytest.raises(ValueError, match='aircraft_error_model'):
        audit_plan(tmp_path, evidence, plan)


def test_confirmation_preflight_refuses_changed_cohort_even_with_same_group_count(tmp_path):
    evidence = metadata()
    plan = example_plan(tmp_path, evidence)
    revised = json.loads(json.dumps(evidence))
    revised['esa-group-b']['withheld'] = 'replacement-time-digest'
    assert cohort_binding(revised) != cohort_binding(evidence)
    with pytest.raises(ValueError, match='cohort'):
        audit_plan(tmp_path, revised, plan)
    plan['groups'] = ['esa-group-a', 'esa-group-c']
    with pytest.raises(ValueError, match='cohort'):
        audit_plan(tmp_path, evidence, plan)


def test_confirmation_preflight_checks_prerequisites_and_keeps_protected_paths_unread(tmp_path):
    evidence = metadata()
    plan = example_plan(tmp_path, evidence)
    plan['training_reports'] = [500]
    with pytest.raises(ValueError, match='training'):
        audit_plan(tmp_path, evidence, plan)
    plan['training_reports'] = [400, 800]
    plan['references']['aircraft_error_model']['path'] = 'data/protected-imu.txt'
    with pytest.raises(ValueError, match='repository documentation'):
        audit_plan(tmp_path, evidence, plan)
    del plan['references']['aircraft_error_model']
    with pytest.raises(ValueError, match='aircraft_error_model'):
        audit_plan(tmp_path, evidence, plan)
