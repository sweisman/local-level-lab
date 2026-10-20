# SPDX-License-Identifier: AGPL-3.0-or-later
"""Seal version one's charged serializer failure; never evaluate observations."""
import fcntl
import time

import ilvis0_gyro_companion_worker as original


def main():
    data=original.DATA
    with (data/'worker.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (data/'completion.json').exists():raise ValueError('interrupted study already sealed')
        manifest=original.verify();digest=original.sha(data/'manifest.json');start=original.load(data/'start.json')
        if start['manifest_sha256']!=digest:raise ValueError('interrupted start source identity changed')
        first=manifest['tasks'][0];identity=first['identity'];charge=original.load(data/'charges'/(identity+'.json'))
        if charge['manifest_sha256']!=digest or charge['kind']!='control':raise ValueError('interrupted charge changed')
        if any((data/'charges'/(t['identity']+'.json')).exists() for t in manifest['tasks'][1:]):raise ValueError('unexpected additional charged work')
        artifact='results/'+identity+'.json';reason='result serialization raised TypeError for duplicate identity/kind fields; no observed stage executed'
        original.write(data/artifact,dict(identity=identity,kind='control',passed=False,status='error',error=reason,
            mathematical_control_result_persisted=False,scientific_decision='abstain'))
        original.write(data/'summary.json',dict(state='terminal',passed=False,terminal_reason=reason,results=[dict(identity=identity,kind='control',
            passed=False,status='error',artifact=artifact,artifact_sha256=original.sha(data/artifact))],
            charged=dict(controls=1,observed=0,scenarios=0,bin_scenario_projections=0),elapsed_s=None,sealed_at=time.time(),
            native_evaluations=0,original_reads=0,optimizer_starts=0,scientific_decision='abstain'))
        original.write(data/'completion.json',dict(state='terminal',manifest_sha256=digest,summary_sha256=original.sha(data/'summary.json')))
        original.write(data/'status.json',dict(state='terminal',total=101,numerical_threads=0),replace=True)
    original.publish()
    print('Preserved one charged technical failure, zero observed comparisons; no numerical evaluation.')


if __name__=='__main__':main()
