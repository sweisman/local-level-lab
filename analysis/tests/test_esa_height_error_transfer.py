# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import pytest


def test_height_error_is_frozen_before_later_scores_and_keeps_horizontal(tmp_path):
    from lll.esa_height_error_transfer import SCOPE, evaluate, task_for

    identity = '200-to-400-increment'
    times = list(range(1, 121))
    early = dict(identity=identity, elapsed=times, later_elapsed=times,
                 first_later_time=401, last_earlier_time=320,
                 errors=[[3, 4, t + 1] for t in times])
    late = dict(identity=identity, errors=[[3, 4, t + 2] for t in times])

    class Context:
        manifest = {'scope': SCOPE}
        saved = {}

        def input_path(self, key=None):
            if key is not None:
                assert 'earlier-only-error-model.json' in self.saved
            target = tmp_path / ('earlier.json' if key is None else 'later.json')
            target.write_text(json.dumps(early if key is None else late))
            return target

        def save(self, name, payload):
            self.saved[name] = payload

        def charge(self, **limits):
            assert limits == dict(bound_calls=1, bound_steps=0)

    result = evaluate(task_for(identity), Context())
    assert result['raw']['horizontal_rms_m'] == result['corrected']['horizontal_rms_m'] == 5.
    assert result['corrected']['vertical_rms_m'] == pytest.approx(1.)
    assert result['scientific_decision'] == 'abstain'
    early['last_earlier_time'] = 401
    with pytest.raises(ValueError, match='chronological'):
        evaluate(task_for(identity), Context())
