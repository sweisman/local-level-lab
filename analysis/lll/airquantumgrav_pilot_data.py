# SPDX-License-Identifier: AGPL-3.0-or-later
"""Outcome-free interval and sample extraction for the first ESA pilot."""
import math


def choose(selection):
    if selection.get('version')!='esa-receiver-full-motion-v2' or not selection.get('eligible'):
        raise ValueError('nonempty frozen full-motion inventory required')
    prior=-1
    for row in selection['eligible']:
        first,last=row['first_index'],row['last_index']
        if (type(first) is not int or type(last) is not int or first<=prior or last-first<2400
                or not all(math.isfinite(row[k]) for k in ('duration_s','distance_m'))
                or row['duration_s']<1200 or row['distance_m']<60000 or row['rejection_reasons']
                or not math.isfinite(row['first_time_s']) or not math.isfinite(row['last_time_s'])
                or row['last_time_s']<=row['first_time_s']):
            raise ValueError('chronological disjoint complete eligible runs required')
        prior=last
    row=selection['eligible'][0]
    return dict(version='esa-first-20-minute-index-window-v1',first_index=row['first_index'],
        last_index=row['first_index']+2400,first_time_s=row['first_time_s'],
        parent_last_index=row['last_index'],parent_last_time_s=row['last_time_s'])


def receiver_layout(rows,chosen):
    if len(rows)!=2401 or chosen['last_index']-chosen['first_index']!=2400:
        raise ValueError('complete fixed 2401-epoch receiver support required')
    if rows[0]['time_s']!=chosen['first_time_s']:raise ValueError('frozen first epoch differs')
    for i,row in enumerate(rows):
        if (not math.isfinite(row['time_s']) or row['gps_week']!=rows[0]['gps_week']
                or (i and (not 0<row['time_s']-rows[i-1]['time_s']<=.75
                    or row['sequence']!=rows[i-1]['sequence']+1))):
            raise ValueError('ordered supported complete single-week receiver window required')
    duration=rows[-1]['time_s']-rows[0]['time_s']
    if abs(duration-1200)>.5:raise ValueError('fixed receiver window does not span nominal twenty minutes')
    query=rows[1:2400:2];cut=2*len(query)//3
    return dict(training_rows=query[:cut],scoring_rows=query,
        query_source_indices=list(range(chosen['first_index']+1,chosen['last_index'],2)),
        training_epochs=cut,prediction_epochs=len(query)-cut,duration_s=duration,
        first_time_s=rows[0]['time_s'],last_time_s=rows[-1]['time_s'],later_positions_used_for_training=False)


class RawWindow:
    """Keep the exact predecessor and successor around a declared time window."""
    def __init__(self,first,last,*,maximum_points):
        import numpy as np
        if (not all(math.isfinite(v) for v in (first,last)) or not 0<=first<last<604800
                or type(maximum_points) is not int or not 2<=maximum_points<=1000000):
            raise ValueError('finite single-week time window and point cap required')
        self.first=first;self.last=last;self.count=0;self.previous=None;self.closed=False
        self.values=np.empty((maximum_points,8));self.lines=np.empty(maximum_points,dtype=np.int64)

    def _append(self,row):
        import numpy as np
        if self.count>=len(self.values):raise ValueError('retained raw point allowance exceeded')
        value=[row['gps_time_s'],*row['acceleration_mps2'],*row['angular_rate_rads'],row['temperature_c']]
        if len(value)!=8 or not np.all(np.isfinite(value)):raise ValueError('complete finite raw channels required')
        self.values[self.count]=value;self.lines[self.count]=row['line_number'];self.count+=1

    def accept(self,row):
        time=row['gps_time_s']
        if (not math.isfinite(time) or row['gap_above_1p5_nominal_periods']
                or (self.previous is not None and not 0<time-self.previous['gps_time_s']<=1.5/300)):
            raise ValueError('unsupported original IMU timing; no repair')
        if not self.closed and time>=self.first:
            if not self.count:
                if self.previous is None:raise ValueError('missing raw left support')
                self._append(self.previous)
            self._append(row)
            if time>=self.last:self.closed=True
        self.previous=row

    def finish(self):
        if not self.closed or self.count<2:raise ValueError('missing raw right support')
        v=self.values[:self.count]
        return dict(raw_time_s=v[:,0].copy(),acceleration_mps2=v[:,1:4].copy(),
            angular_rate_rads=v[:,4:7].copy(),temperature_c=v[:,7].copy(),line_number=self.lines[:self.count].copy())
