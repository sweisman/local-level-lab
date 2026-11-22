# SPDX-License-Identifier: AGPL-3.0-or-later
"""Separate the terms already counted in the position remainder recurrence."""

import math


PARTS = ('initial', 'velocity', 'geographic_metric', 'clock', 'arithmetic')


class PositionBudget:
    def __init__(self, previous=None, *, initial=(0., 0., 0.)):
        self.totals = [[value, 0., 0., 0., 0.] for value in initial] if previous is None else [row.copy() for row in previous.totals]

    def append(self, rate_parts, rates, duration, before, after):
        dt = duration.value
        for totals, (velocity, metric), rate, old, new in zip(self.totals, rate_parts, rates, before, after, strict=True):
            velocity_remainder = abs(duration.center)*velocity.value.remainder
            metric_remainder = abs(duration.center)*metric.value.remainder
            clock = abs(rate.center)*dt.remainder + rate.value.change*dt.change
            step = new.value.remainder-old.value.remainder
            terms = (velocity_remainder, metric_remainder, clock)
            terms += (step-math.fsum(terms),)
            for i, value in enumerate(terms, start=1):
                totals[i] += value

    def report(self):
        return {name: [row[i] for row in self.totals] for i, name in enumerate(PARTS)}
