# SPDX-License-Identifier: AGPL-3.0-or-later
"""Bounded development replays, preserving watchdog inputs for inexpensive diagnosis."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import signal
import tempfile
import time

from conftest import geometric_truth
from lll import fit, slip
from lll.analyze import analyze, _clean
from lll.policy import heading_diversity
from lll.research_design import implementation_hash, simulator_options
from lll.runtime import numerical_environment
from lll.synth import synthesize


class TimeLimit(BaseException):
    pass


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(_clean(value), indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def bin_geometry(bins):
    return dict(n_bins=len(bins['t']), segments=sorted(set(map(int, bins['seg']))),
                heading_diversity=heading_diversity(bins))


def diagnostic(original, case):
    design = deepcopy(original['design'])
    design['simulator']['mount_slip_deg_per_h'] = [case['mount_yaw_creep_dph'], case['mount_tilt_creep_dph']]
    settings = {**original['fit_options'], **design['analysis_options'], 'n_boot': 0,
                'design_only': True, 'seed': design['streams']['bootstrap']}
    captured, fits = {}, []
    original_watchdog, original_fit = slip.watchdog, fit.fit

    def watchdog(bins, hard_iron, year, max_slip_dph):
        captured.update(bins={key: bins[key].copy() for key in
            ('t', 'dt', 'lat', 'lon', 'h', 'psi', 'up', 'mag', 'epoch', 'seg')},
            hard_iron=hard_iron, year=year, max_slip_dph=max_slip_dph)
        return original_watchdog(bins, hard_iron, year, max_slip_dph)

    def fitting(bins, *args, **kwargs):
        result = original_fit(bins, *args, **kwargs)
        fits.append({**bin_geometry(bins), 'design_identifiability': result.get('design_identifiability')})
        return result

    started = time.monotonic()
    slip.watchdog, fit.fit = watchdog, fitting
    try:
        with tempfile.TemporaryDirectory(prefix='lll-watchdog-') as directory:
            path = Path(directory)/'flight.zip'
            synthesize(path, case['truth'], omega_in_fn=geometric_truth(case['truth']), **simulator_options(design))
            result = analyze(path, fit_options=settings)
        return _clean(dict(case=case, partition='development', replay=True, elapsed_s=time.monotonic()-started,
            design=design, fit_options=settings, slip=result.get('slip'), flags=result.get('flags'),
            pre_exclusion_geometry=bin_geometry(captured['bins']), fits=fits,
            watchdog_inputs=captured, forward_axis=result.get('forward_axis')))
    finally:
        slip.watchdog, fit.fit = original_watchdog, original_fit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--campaign', type=Path, default=Path('docs/development-1000-20261005/campaign.json.gz'))
    parser.add_argument('-o', type=Path, required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    if args.o.exists():
        raise ValueError('output already exists; do not silently rerun completed development cases')
    if hashlib.sha256(args.campaign.read_bytes()).hexdigest() != plan['source_archive_sha256']:
        raise ValueError('source archive differs from diagnostic plan')
    if implementation_hash() != plan['source_implementation_hash']:
        raise ValueError('scientific source differs from diagnostic plan')
    with gzip.open(args.campaign, 'rt') as source:
        campaign = json.load(source)
    if campaign['numerical_environment'] != numerical_environment():
        raise ValueError('runtime differs from archived campaign')
    report = dict(partition='development', replay=True, plan=plan, cases=[], state='running',
                  numerical_environment=numerical_environment(), implementation_hash=implementation_hash(),
                  runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    started = time.monotonic()
    def timeout(*unused):
        raise TimeLimit()
    previous = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, plan['maximum_wall_seconds'])
    try:
        for case in plan['cases']:
            original = next(row for row in campaign['records'] if all(row[key] == case[key]
                            for key in ('truth', 'scenario', 'seed')))
            try:
                row = diagnostic(original, case)
            except Exception as error:
                row = dict(case=case, error=repr(error))
            report['cases'].append(row)
            report['elapsed_s'] = time.monotonic()-started
            atomic_json(args.o, report)
            print(json.dumps(dict(case=case, error=row.get('error'), elapsed_s=row.get('elapsed_s'),
                  excluded=row.get('slip', {}).get('exclude_segments'))), flush=True)
        report['state'] = 'complete'
    except TimeLimit:
        report.update(state='time_limit', interrupted_case=case)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        report['elapsed_s'] = time.monotonic()-started
        report['incomplete_cases'] = plan['cases'][len(report['cases']):]
        atomic_json(args.o, report)


if __name__ == '__main__':
    main()
