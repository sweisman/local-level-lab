# SPDX-License-Identifier: AGPL-3.0-or-later
import importlib.util


def test_transport_profiler_exists():
    assert importlib.util.find_spec('lll.ilvis0_transport_profile') is not None


def test_profile_output_retains_costs_without_absolute_paths():
    import cProfile
    from lll.ilvis0_transport_profile import profile_statistics
    profiler=cProfile.Profile();profiler.enable();sum(i*i for i in range(20));profiler.disable()
    result=profile_statistics(profiler)
    assert result['total_calls']>0 and result['total_time_s']>=0
    assert result['functions'] and all('/' not in r['file'] for r in result['functions'])
