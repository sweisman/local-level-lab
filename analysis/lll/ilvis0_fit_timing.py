# SPDX-License-Identifier: AGPL-3.0-or-later
"""Observe complete generated fit CPU time without altering the fit path."""

import time


def measure_variant(calculate, spec, recipe, *, kernel_factory, reserve,
                    reserve_construction, save, check_continue, tick=None):
    """Return the unchanged calculation and ordered CPU/wall timing markers."""
    if tick is None:
        tick = lambda: (time.process_time_ns(), time.perf_counter_ns())
    start = tick()
    ready = None
    fitted = None

    def build(anchor):
        nonlocal ready
        if ready is not None:
            raise ValueError('fit timing has repeated kernel construction')
        kernel = kernel_factory(anchor)
        ready = tick()
        return kernel

    def saving(name, value):
        nonlocal fitted
        if name == 'fit.json':
            if ready is None or fitted is not None:
                raise ValueError('fit timing markers are missing or misordered')
            fitted = tick()
        save(name, value)

    result = calculate(spec, recipe, kernel_factory=build, reserve=reserve,
                       reserve_construction=reserve_construction, save=saving,
                       check_continue=check_continue)
    end = tick()
    if ready is None or fitted is None:
        raise ValueError('fit timing markers are missing or misordered')
    points = (start, ready, fitted, end)
    if any(not isinstance(point, tuple) or len(point) != 2 or
           any(type(value) is not int or value < 0 for value in point)
           for point in points):
        raise ValueError('fit timing requires nonnegative integer clock ticks')
    complete_cpu = end[0] - start[0]
    complete_wall = end[1] - start[1]
    fit_cpu = fitted[0] - ready[0]
    fit_wall = fitted[1] - ready[1]
    if (min(complete_cpu, complete_wall, fit_cpu, fit_wall) <= 0
            or fit_cpu > complete_cpu or fit_wall > complete_wall):
        raise ValueError('fit timing requires positive ordered durations')
    return result, dict(complete_cpu_ns=complete_cpu,
                        complete_wall_ns=complete_wall,
                        fit_cpu_ns=fit_cpu, fit_wall_ns=fit_wall)


def timed_pair(spec, recipe, *, calculate, factories, reserve,
               reserve_construction, save, check_continue):
    """Call the shared paired fit and save one timer record per variant."""
    from lll.ilvis0_hybrid_fit_study import pair

    names = {id(factory): name for name, factory in factories.items()}
    if len(names) != 2:
        raise ValueError('fit timing requires distinct wide and hybrid factories')
    timings = {}

    def measured(spec, recipe, *, kernel_factory, reserve,
                 reserve_construction, save, check_continue):
        name = names.get(id(kernel_factory))
        if name is None or name in timings:
            raise ValueError('fit timing requires one call per declared variant')
        result, timing = measure_variant(
            calculate, spec, recipe, kernel_factory=kernel_factory,
            reserve=reserve, reserve_construction=reserve_construction,
            save=save, check_continue=check_continue)
        timings[name] = timing
        return result

    result = pair(spec, recipe, calculate=measured, factories=factories,
                  reserve=reserve, reserve_construction=reserve_construction,
                  save=save, check_continue=check_continue)
    if set(timings) != {'wide', 'hybrid'}:
        raise ValueError('fit timing requires both completed variants')
    save('whole-fit-timing.json', timings)
    return dict(result, timing=timings)
