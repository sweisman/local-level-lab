# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util
from pathlib import Path

from lll.prediction_known_answer_identification_study import recipe, tasks
from lll.prediction_known_answer_identification_v2 import (
    evaluate, require_first_failure)


def test_v2_preserves_exact_trial_and_declares_scientific_abstention(tmp_path):
    from lll.studies.artifacts import encoded
    path = tmp_path/'recipe.json'
    path.write_bytes(encoded(recipe()))

    class Context:
        manifest = dict(scope='generated linearized IMU and receiver error only; '
                              'earlier-only law selection, later receiver coverage '
                              'diagnostic; no aircraft data')
        charges = []
        saved = {}

        def input_path(self, name):
            assert name == 'recipe'
            return path

        def charge(self, **counts):
            self.charges.append(counts)

        def save(self, name, value):
            self.saved[name] = value

    context = Context()
    result = evaluate(tasks()[0], context)
    assert result['passed'] is True
    assert result['scientific_decision'] == 'abstain'
    assert result['histories'] == 100
    assert len(context.charges) == 101


def test_v2_adapter_loads_directly():
    from lll import prediction_known_answer_identification_v2 as source
    spec = importlib.util.spec_from_file_location('frozen_trial_v2', Path(source.__file__))
    frozen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(frozen)
    assert frozen.recipe() == recipe()
    assert frozen.tasks() == tasks()


def test_prior_failure_must_be_exact_and_charged():
    from pytest import raises
    base = dict(state='terminal', completed=4, passed=0,
                charged=dict(bound_calls=404, bound_steps=1624,
                             native_calls=0, packet_visits=0))
    require_first_failure(base)
    with raises(ValueError):
        require_first_failure(dict(base, passed=1))
    with raises(ValueError):
        require_first_failure(dict(base, charged=dict(base['charged'], bound_calls=403)))
