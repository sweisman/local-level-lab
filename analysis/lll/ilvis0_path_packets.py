# SPDX-License-Identifier: AGPL-3.0-or-later
"""Complete parameter-to-receiver path on one declared packet branch.

This adapter cannot qualify a complete clock partition or native execution
error. Frozen native engines and their inputs are never modified.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import time as clock
from .ilvis0_path_jets import Jet3 as J
from .ilvis0_path_motion import State,step,exponential,_product,_mv,_q
from .ilvis0_path_geometry import rates


@dataclass(frozen=True)
class Prediction:
    coordinates:tuple
    state:State
    packet_index:int
    fraction:J
    start:float

    def report(self):
        return dict(version='ilvis0-third-order-packet-branch-v1',
            coordinates=[v.report() for v in self.coordinates],state=self.state.report(),
            packet_index=self.packet_index,packet_steps=self.packet_index+1,
            fraction=self.fraction.report(),native_cumulative_start_s=self.start,
            physical_columns=27,packet_branch_domain_verified=True,
            clock_partition_verified=False,floating_point_execution_covered=False,
            native_history_qualified=False,observational_coverage_qualified=False,scientific_decision='abstain')


def predict_branch(configuration,theta,dv,dt,parameters,*,time,packet_index,
        maximum_packets=1024,maximum_seconds=30.):
    """Integrate every preceding packet and a range-checked partial final one.

Input jets describe a common declared path in normalized physical parameters.
The caller must establish that common-path interpretation. The cumulative
packet start follows the native binary64 timestamp convention. Input raw
increments and periods remain unchanged rational representations of supplied
values; ordinary float inputs are therefore represented exactly.
"""
    started=clock.monotonic()
    if (len(parameters)!=27 or not all(isinstance(p,J) for p in parameters)
            or any(not -1<=p.exact[0][0]<=p.exact[0][1]<=1 for p in parameters)
            or type(packet_index) is not int or not 0<=packet_index<len(dt)
            or len(theta)!=len(dt) or len(dv)!=len(dt)
            or type(maximum_packets) is not int or not 1<=maximum_packets<=1000000
            or packet_index+1>maximum_packets or not math.isfinite(maximum_seconds) or maximum_seconds<=0):
        raise ValueError('all27 normalized path columns, supported packet and finite execution limits required')
    periods=[F(t) for t in dt[:packet_index+1]]
    if any(t<=0 for t in periods):raise ValueError('positive packet periods required')
    config=configuration;limits=config['limits']
    if (len(limits)!=27 or len(config['initial_c'])!=3 or len(config['initial_v'])!=3
            or type(config['profile']) is not bool):
        raise ValueError('complete initial configuration and processing convention required')
    p=[_q(value*F(limit)) for value,limit in zip(parameters,limits)]
    p[26]=_q((p[26]+1)/2) if config['profile'] else J.constant(0)
    radius=J.constant(config['radius']);gravity=_q(J.constant(config['gravity'])+p[24])
    coordinates=tuple(J.constant(v) for v in config['initial_c'])
    offset=rates(config['model'],coordinates,p[6:9],radius)
    coordinates=tuple(_q(c+d) for c,d in zip(coordinates,offset))
    initial_r=tuple(tuple(J.constant(v) for v in row) for row in config['initial_r'])
    attitude=_product(initial_r,exponential(p[:3]))
    velocity=tuple(_q(J.constant(v)+d) for v,d in zip(config['initial_v'],p[3:6]))
    state=State(coordinates,velocity,attitude);start=0.
    for k,t in enumerate(periods):
        if clock.monotonic()-started>=maximum_seconds:
            raise ValueError('packet derivative execution allowance exhausted')
        if len(theta[k])!=3 or len(dv[k])!=3:raise ValueError('three-axis raw increments required')
        th=[];vel=[]
        for i in range(3):
            if (1+p[15+i]).exact[0][0]<=0 or (1+p[18+i]).exact[0][0]<=0:
                raise ValueError('positive physical calibration denominators required')
            th.append(_q((J.constant(theta[k][i])-p[9+i]*t)/(1+p[15+i])))
            vel.append(_q((J.constant(dv[k][i])-p[12+i]*t)/(1+p[18+i])))
        fraction=_q((J.constant(time)+p[25]-F(start))/t) if k==packet_index else J.constant(1)
        if not 0<=fraction.exact[0][0]<=fraction.exact[0][1]<=1:
            raise ValueError('query range crosses declared packet branch')
        period=_q(J.constant(t)*fraction)
        state=step(config['model'],state,[_q(v*fraction) for v in th],
            [_q(v*fraction) for v in vel],period,gravity,radius,p[26])
        if k==packet_index:
            local_lever=_mv(state.attitude,p[21:24]);offset=rates(config['model'],state.coordinates,local_lever,radius)
            output=tuple(_q(c+d) for c,d in zip(state.coordinates,offset))
            if clock.monotonic()-started>=maximum_seconds:
                raise ValueError('packet derivative execution allowance exhausted')
            return Prediction(output,state,k,fraction,start)
        start+=float(t)
    raise ValueError('missing declared packet branch')
