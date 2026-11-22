# SPDX-License-Identifier: AGPL-3.0-or-later
import pytest

from lll.ilvis0_portable_forecast import forecast_task
from lll.ilvis0_portable_refit import IDENTITY


def test_portable_forecast_freezes_one_call_at_the_original_queries():
    segment = IDENTITY.rsplit('-', 1)[0]
    task = dict(identity=IDENTITY, model='sphere_rotating', segment_id=segment,
                input_key=segment+'-packets', full_packets=101, training_epochs=20,
                scoring_epochs=10, limits={'native_calls': 61}, native_kind='mixed')
    result, keys = forecast_task({IDENTITY: task}, 'a'*64)
    assert result['limits'] == dict(native_calls=1, packet_visits=3030,
                                    bound_calls=0, bound_steps=0)
    assert result['native_kind'] == 'tangent'
    assert result['forecast_sha256'] == 'a'*64
    assert set(keys) == {'recipe', segment+'-packets', segment+'-training', segment+'-queries'}
    with pytest.raises(ValueError, match='digest'):
        forecast_task({IDENTITY: task}, 'forecast.json')
