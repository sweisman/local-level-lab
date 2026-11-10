# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded lifecycle pulses for the shared runner; no numerical observations."""
import math
import time

from lll.ilvis0_control_shards import _check_continue


def evaluate(task,context):
    if task!=context.task:raise ValueError('unchanged frozen task required')
    p=task['payload'];count=p.get('intervals');interval=p.get('interval_s')
    if (type(count) is not int or not 1<=count<=60 or type(interval) not in (int,float)
            or not math.isfinite(interval) or interval<=0 or count*interval>60):
        raise ValueError('finite positive pulse schedule, at most sixty seconds, required')
    started=time.time();monotonic=time.monotonic()
    for index in range(count):
        _check_continue(context.root,context.manifest)
        time.sleep(interval)
        _check_continue(context.root,context.manifest)
        context.save(f'pulse-{index+1:03d}.json',dict(interval=index+1,
            unix_s=time.time(),monotonic_s=time.monotonic()))
    return dict(passed=True,scientific_decision='abstain',intervals=count,
        started_unix_s=started,finished_unix_s=time.time(),elapsed_s=time.monotonic()-monotonic,
        native_calls=0,host_reset_survival_demonstrated=False)
