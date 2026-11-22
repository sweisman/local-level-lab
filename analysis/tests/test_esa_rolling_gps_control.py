# SPDX-License-Identifier: AGPL-3.0-or-later
import json

import numpy as np


def test_receiver_forecasts_are_saved_before_scoring(tmp_path):
    from lll.esa_rolling_gps_control import SCOPE, evaluate, task_for

    cut = 200
    times = list(range(60))
    future = list(range(60, 180))
    positions = [[0.5, 0.1, 1000.]] * len(future)
    earlier = tmp_path / 'earlier.json'
    later = tmp_path / 'later.json'
    earlier.write_text(json.dumps(dict(cut=cut, training_times=times, future_times=future,
        training_velocity=[[0., 90., 0.]] * len(times), last_coordinate=positions[0])))
    later.write_text(json.dumps(dict(cut=cut, times=future, coordinates=positions)))

    class Context:
        manifest = {'scope': SCOPE}
        saved = {}
        charged = 0

        def input_path(self, key=None):
            if key is None:
                return earlier
            assert key == '200-scoring'
            assert set(self.saved) == {'fixed-forecast.json', 'turn-forecast.json'}
            assert self.charged == 2
            return later

        def save(self, name, value):
            self.saved[name] = value

        def charge(self, **limits):
            assert limits == {'bound_calls': 1, 'bound_steps': 0}
            self.charged += 1

    actual = evaluate(task_for(cut), Context())
    a, b = (actual[name]['metrics'] for name in ('fixed', 'turn'))
    # The turn rule advances in steps of at most one second.
    np.testing.assert_allclose(a['horizontal_rms_m'], b['horizontal_rms_m'], rtol=0., atol=0.001)
    assert a['vertical_rms_m'] == b['vertical_rms_m'] == 0.
    assert actual['scientific_decision'] == 'abstain'
