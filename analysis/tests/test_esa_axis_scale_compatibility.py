import math

import numpy as np

from lll.esa_axis_scale_compatibility import quadratic_interval, search
from lll.esa_motion_innovation_scale import InnovationScore


def test_quadratic_interval_includes_dense_correlated_error():
    rng = np.random.default_rng(102)
    y, root = rng.normal(size=12), rng.normal(size=(12, 3))
    weight = np.repeat([0., .1, .4, 1.], 3)
    scorer = InnovationScore(y, root, weight, 0.)
    logs = [-5., 2.2, 4., -.1, 1.5, 4.8]
    variance = np.tile(np.exp(logs[:3]), 4)+weight*np.tile(np.exp(logs[3:]), 4)
    expected = y @ np.linalg.solve(np.diag(variance)+root@root.T, y)
    lower, upper = quadratic_interval(scorer, logs)
    assert lower <= expected <= upper
    assert upper-lower < 1e-5


def test_search_saves_compatible_and_completely_excluded_boxes():
    def inverse(scale):
        return lambda logs: (scale*math.exp(-logs[0]),)*2

    compatible = search([inverse(1.), inverse(1.1)], bounds=[(-2., 2.)], reference=(.75, 1.25), maximum=8)
    assert compatible['status'] == 'witness' and compatible['witness'] == (0.,)
    excluded = search([inverse(1.), inverse(4.)], bounds=[(-2., 2.)], reference=(.75, 1.25), maximum=16)
    assert excluded['status'] == 'incompatible'
    assert excluded['excluded'] and not excluded['open']


def test_search_preserves_open_boxes_at_the_work_limit():
    def inverse(logs):
        return (2.*math.exp(-logs[0]),)*2

    record = search([inverse], bounds=[(-2., 2.)], reference=(.9, 1.1), maximum=1)
    assert record['status'] == 'unresolved'
    assert record['checked'] == 1 and len(record['open']) == 2
