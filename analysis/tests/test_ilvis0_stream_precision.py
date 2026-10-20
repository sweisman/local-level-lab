# SPDX-License-Identifier: AGPL-3.0-or-later
from lll import ilvis0_stream_precision as precision


def test_trial_has_six_distinct_controls_and_same_precision_limits():
    tasks=precision.tasks()
    assert len(tasks)==6 and len({t['identity'] for t in tasks})==6
    assert [t['packets'] for t in tasks[:4]]==[120000,120000,480000,480000]
    assert precision.POSITION_LIMIT==1e-6 and precision.DERIVATIVE_LIMIT==1e-7


def test_real_comparison_and_exact_arithmetic_control(tmp_path):
    for task in (precision.tasks()[0],precision.tasks()[-1]):
        task=dict(task,packets=1200);calls=[]
        result=precision.evaluate(task,tmp_path,lambda **c:calls.append(c))
        assert result['passed']
        assert sum(c['packet_visits'] for c in calls)==(1200 if task['kind']=='exact-pose' else 2400)
        assert result['maximum_position_difference_m']<=1e-6
        if task['kind']=='exact-pose':assert result['maximum_exact_pose_error_m']==0.
