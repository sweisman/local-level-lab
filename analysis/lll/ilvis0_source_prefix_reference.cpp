/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Typed source-prefix entry points; original source arithmetic is included.
 */
#include "ilvis0_source_stream.cpp"
#include "ilvis0_source_prefix.hpp"
namespace {
constexpr std::uint64_t tag=0x4c4c4c5052454631ULL;
using Header=SourcePrefix<SourceState,tag>;
}
extern "C" std::size_t ilvis0_prefix_reference_bytes(){return sizeof(Header);}
extern "C" int ilvis0_prefix_reference_init(void*buffer,std::size_t bytes,const double*initial,
    const double*limits,const double*z,const double*dv,double dt,double time){
    if(!buffer||bytes!=sizeof(Header))return 2;Header h;
    int code=ilvis0_source_stream_init(&h.state,sizeof h.state,initial,limits,z,dv,dt,time);
    if(!code)std::memcpy(buffer,&h,sizeof h);return code;
}
extern "C" int ilvis0_prefix_reference_append(void*buffer,std::size_t bytes,const double*raw,
    double dt,double*values,double*jac,double*timing){
    Header h;if(!source_prefix_read(h,buffer,bytes,tag))return 2;
    bool full=(h.state.time+h.state.p[25]).v>h.state.elapsed+dt;
    if(!source_prefix_advance(h,dt,full))return 2;
    int code=ilvis0_source_stream_append(&h.state,sizeof h.state,raw,dt,values,jac,timing);
    if(!code)std::memcpy(buffer,&h,sizeof h);return code;
}
extern "C" int ilvis0_prefix_reference_fork(void*target,std::size_t bytes,const void*source,
    std::size_t source_bytes,double time,double minimum_query){
    Header h;if(!target||bytes!=sizeof(Header)||!source_prefix_read(h,source,source_bytes,tag)
        ||!std::isfinite(time)||!source_prefix_target(h,h.state.elapsed,minimum_query))return 2;
    if(h.packets&&!((time+h.state.p[25]).v>h.state.elapsed))return 2;
    h.state.time=time;std::memcpy(target,&h,sizeof h);return 0;
}
extern "C" int ilvis0_prefix_reference_query_lower(const void*source,std::size_t bytes,
    double time,double minimum_query,double*out){
    Header h;if(!out||!source_prefix_read(h,source,bytes,tag)
        ||!std::isfinite(time)||!std::isfinite(minimum_query))return 2;
    *out=std::min(minimum_query,(time+h.state.p[25]).v);return std::isfinite(*out)?0:2;
}
