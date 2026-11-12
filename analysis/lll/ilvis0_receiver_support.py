# SPDX-License-Identifier: AGPL-3.0-or-later
"""Select a common receiver-only support for descriptive force diagnostics.

This uses supplied motion metadata, never gyro data or model-fit outcomes.
Thresholds are research policy inputs, not calibrated flight acceptance limits.
"""
from bisect import bisect_left, bisect_right
from dataclasses import asdict, dataclass
import math

from .models import WGS84_A, WGS84_E2


VERSION='receiver-motion-support-v1'
GGA_MOTION_VERSION='receiver-gga-motion-v2'


def _finite(value):
    try:
        return not isinstance(value,bool) and math.isfinite(value)
    except (TypeError,ValueError):
        return False


@dataclass(frozen=True)
class SupportPolicy:
    half_windows_s: tuple[float,...]
    maximum_gap_s: float
    minimum_samples: int
    minimum_speed_mps: float
    maximum_speed_mps: float
    maximum_course_span_deg: float
    maximum_speed_span_mps: float
    maximum_vertical_rate_span_mps: float

    def __post_init__(self):
        widths=self.half_windows_s
        if (not isinstance(widths,tuple) or not widths
                or any(not _finite(value) or value<=0 for value in widths)
                or tuple(sorted(set(widths)))!=widths
                or type(self.minimum_samples) is not int or self.minimum_samples<5):
            raise ValueError('ordered positive supports and at least five samples required')
        positive=(self.maximum_gap_s,)
        nonnegative=(self.minimum_speed_mps,self.maximum_speed_mps,
                     self.maximum_course_span_deg,
                     self.maximum_speed_span_mps,self.maximum_vertical_rate_span_mps)
        if (any(not _finite(value) or value<=0 for value in positive)
                or any(not _finite(value) or value<0 for value in nonnegative)
                or self.maximum_speed_mps<self.minimum_speed_mps
                or self.maximum_course_span_deg>=180):
            raise ValueError('finite motion and sampling limits required')


def _course_span(course):
    unwrapped=[course[0]]
    for previous,current in zip(course,course[1:]):
        change=(current-previous+180.)%360.-180.
        unwrapped.append(unwrapped[-1]+change)
    return max(unwrapped)-min(unwrapped)


def motion_from_gga_fixes(fixes,*,maximum_gap_s):
    """Estimate screening motion from timestamped primary-receiver positions.

    The WGS84 chart interprets reported coordinates only for motion screening;
    these derivatives are not independent evidence for an Earth model. Each
    estimate uses each fix's ZDA-mapped GGA measurement time (``utc_week_s``),
    not its enclosing packet's ``time1_s``. No VTG association or interpolation
    is made. Endpoint estimates use one interval; interior estimates use the
    two surrounding fixes.
    """
    if not _finite(maximum_gap_s) or maximum_gap_s<=0.:
        raise ValueError('positive receiver fix gap limit required')
    try:
        rows=tuple(fixes)
        values=tuple((float(row['utc_week_s']),float(row['latitude_deg']),
                      float(row['longitude_deg']),
                      float(row['orthometric_height_m'])+float(row['geoid_separation_m']),
                      float(row['fix_quality'])) for row in rows)
    except (KeyError,TypeError,ValueError,OverflowError) as error:
        raise ValueError('finite ordered primary-receiver fixes required') from error
    if (len(values)<3 or any(not all(_finite(value) for value in row)
                             for row in values)
            or any(abs(row[1])>=90. or abs(row[2])>180. or row[4]<=0.
                   or math.cos(math.radians(row[1]))<1e-3 for row in values)
            or any(not 0.<right[0]-left[0]<=maximum_gap_s
                   for left,right in zip(values,values[1:]))):
        raise ValueError('finite ordered primary-receiver fixes required')
    speed=[];course=[];vertical=[]
    for index,(time,latitude,_,height,_) in enumerate(values):
        left=values[max(0,index-1)]
        right=values[min(len(values)-1,index+1)]
        elapsed=right[0]-left[0]
        delta_lon=(right[2]-left[2]+180.)%360.-180.
        if abs(right[2]-left[2])>=180. and abs(delta_lon)<1e-9:
            raise ValueError('ambiguous receiver longitude displacement')
        phi=math.radians(latitude)
        sine=math.sin(phi)
        base=1.-WGS84_E2*sine*sine
        meridian=WGS84_A*(1.-WGS84_E2)/base**1.5
        prime=WGS84_A/math.sqrt(base)
        north=math.radians(right[1]-left[1])*(meridian+height)/elapsed
        east=math.radians(delta_lon)*(prime+height)*math.cos(phi)/elapsed
        speed.append(math.hypot(north,east))
        course.append(math.degrees(math.atan2(east,north))%360.)
        vertical.append((right[3]-left[3])/elapsed)
    return dict(version=GGA_MOTION_VERSION,source='primary_receiver_gga',
                coordinate_metric='WGS84 receiver-coordinate interpretation',
                height_convention='GGA orthometric_height_m + geoid_separation_m',
                maximum_gap_s=float(maximum_gap_s),
                times_s=tuple(row[0] for row in values),
                ellipsoidal_height_m=tuple(row[3] for row in values),
                speed_mps=tuple(speed),course_deg=tuple(course),
                vertical_rate_mps=tuple(vertical),
                scientific_decision='abstain')


def select_support(times_s,ground_speed_mps,course_deg,vertical_rate_mps,
                   *,target_s,policy):
    """Return every candidate and the longest motion-qualified symmetric one."""
    if not isinstance(policy,SupportPolicy) or not _finite(target_s):
        raise ValueError('explicit support policy and finite target required')
    try:
        series=tuple(tuple(values) for values in
                     (times_s,ground_speed_mps,course_deg,vertical_rate_mps))
    except TypeError as error:
        raise ValueError('finite ordered receiver motion samples required') from error
    times,speed,course,vertical=series
    if (len(times)<2 or any(len(values)!=len(times) for values in series)
            or any(not _finite(value) for values in series for value in values)
            or any(later<=earlier for earlier,later in zip(times,times[1:]))
            or any(value<0 for value in speed)
            or any(value<0 or value>360 for value in course)):
        raise ValueError('finite ordered receiver motion samples required')
    if not times[0]<=target_s<=times[-1]:
        raise ValueError('target outside receiver samples')
    windows=[]
    for half in policy.half_windows_s:
        left=bisect_left(times,target_s-half)
        right=bisect_right(times,target_s+half)
        samples=right-left
        row=dict(half_window_s=half,first_index=left,last_index=right-1,
                 sample_count=samples,accepted=False,reason=None,
                 course_span_deg=None,speed_span_mps=None,
                 vertical_rate_span_mps=None)
        if (times[0]>target_s-half or times[-1]<target_s+half
                or not samples or times[left]-(target_s-half)>policy.maximum_gap_s
                or (target_s+half)-times[right-1]>policy.maximum_gap_s):
            row['reason']='incomplete_support'
        elif samples<policy.minimum_samples:
            row['reason']='sample_count'
        elif any(times[index+1]-times[index]>policy.maximum_gap_s
                 for index in range(left,right-1)):
            row['reason']='gap'
        else:
            subset_speed=speed[left:right];subset_course=course[left:right]
            subset_vertical=vertical[left:right]
            row['course_span_deg']=_course_span(subset_course)
            row['speed_span_mps']=max(subset_speed)-min(subset_speed)
            row['vertical_rate_span_mps']=max(subset_vertical)-min(subset_vertical)
            if min(subset_speed)<policy.minimum_speed_mps:
                row['reason']='low_speed'
            elif max(subset_speed)>policy.maximum_speed_mps:
                row['reason']='high_speed'
            elif row['course_span_deg']>policy.maximum_course_span_deg:
                row['reason']='course_span'
            elif row['speed_span_mps']>policy.maximum_speed_span_mps:
                row['reason']='speed_span'
            elif row['vertical_rate_span_mps']>policy.maximum_vertical_rate_span_mps:
                row['reason']='vertical_rate_span'
            else:
                row['accepted']=True
        windows.append(row)
    chosen=next((row for row in reversed(windows) if row['accepted']),None)
    return dict(version=VERSION,policy=asdict(policy),target_s=float(target_s),
                windows=windows,
                selected_half_window_s=None if chosen is None else chosen['half_window_s'],
                selected_indices=None if chosen is None else
                    (chosen['first_index'],chosen['last_index']),
                scientific_decision='abstain')
