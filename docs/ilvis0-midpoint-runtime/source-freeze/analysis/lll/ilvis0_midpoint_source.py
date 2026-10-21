# SPDX-License-Identifier: AGPL-3.0-or-later
"""Preserve midpoint certificates and endpoint state; omit unused endpoint force.

This candidate intentionally supplies phase zero only. It retains the original
derivative and direct-remainder streams, including their complete phase data.
The source stream's own endpoint rotation is still propagated every packet.
Native installation and runtime usefulness require separate qualification.
"""
from fractions import Fraction as F
import math
import numpy as np
from .ilvis0_direct_source_taylor import SourceDirectStream,DirectSourceBox
from .ilvis0_batched_source_values import _box_value,_rotation
from .ilvis0_batched_transport import scalar_product,scale,matrix_vector
from .ilvis0_batched_relative import Delta,multiply,plus


class SourceMidpointStream(SourceDirectStream):
    def append(self):
        if self.closed:raise ValueError('source stream is closed')
        if self.visits>=self.maximum_packets:raise ValueError('source packet allowance exhausted')
        index=self.visits;self.visits+=1;start=self.elapsed;period=float(self.dt[index]);end=start+period
        if not math.isfinite(end) or end<=start:raise ValueError('nonincreasing source packet clock')
        clip=lambda value:max(F(0),min(F(1),value))
        low=clip((self.query_lower-F(start))/F(period));high=clip((self.query_upper-F(start))/F(period))
        nominal=max(0.,min(1.,(self.nominal_query-start)/period))
        fraction=_box_value(nominal,[low],[high])
        corrected,_=self._correct(self.theta[index],period,9,15)
        angle=scalar_product(fraction,corrected)
        middle=multiply(self.body,_rotation(scale(angle,.5)))
        departure=plus(middle,Delta(-np.eye(3)))
        b=matrix_vector(multiply(self.mount,departure),self.force)
        # This exact endpoint state is required by the next packet. Only its
        # unused departure/force certificate is omitted.
        self.body=multiply(self.body,_rotation(scale(angle,1.)))
        self.elapsed=end
        derivative=self.derivatives.append();direct=self.direct.append()
        if derivative['packet_index']!=index or direct.packet_index!=index:
            raise ValueError('midpoint and auxiliary source prefixes differ')
        proof=DirectSourceBox(self.a,b,self.reference.binding,self.reference.parent.source_id,
            self.lower,self.upper,self.time_s,index,start,end,0,self.norm_error,
            derivative_frame=derivative,direct_frame=direct)
        return dict(packet_index=index,phases=(proof,),reserved_source_steps=2,
            physical_value_intervals=True,whole_native_rounding_qualified=False,
            source_derivative_steps=self.derivatives.visits,source_direct_steps=self.direct.visits,
            midpoint_only=True)
