/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Copy/retarget source interval states without duplicating their arithmetic.
 */
#include "ilvis0_source_point_derivatives.cpp"
#include "ilvis0_source_prefix.hpp"
namespace {
constexpr std::uint64_t interval_tag=0x4c4c4c50494e5431ULL,point_tag=0x4c4c4c50504f4931ULL;
using Intervals=SourcePrefix<source_derivatives::State,interval_tag>;
using Point=SourcePrefix<source_point::State,point_tag>;
bool one(const source_derivatives::Jet&v){
    if(v.v.lo!=1.||v.v.hi!=1.)return false;
    for(const auto&d:v.d)if(d.lo!=0.||d.hi!=0.)return false;
    return true;
}
}
extern "C" std::size_t ilvis0_prefix_interval_bytes(){return sizeof(Intervals);}
extern "C" std::size_t ilvis0_prefix_point_bytes(){return sizeof(Point);}
extern "C" int ilvis0_prefix_interval_init(void*buffer,std::size_t bytes,const double*initial,
    const double*limits,const double*z,const double*lo,const double*hi,const double*dv,double dt,double time){
    if(!buffer||bytes!=sizeof(Intervals))return 2;Intervals h;
    int code=ilvis0_source_intervals_init(&h.state,sizeof h.state,initial,limits,z,lo,hi,dv,dt,time);
    if(!code)std::memcpy(buffer,&h,sizeof h);return code;
}
extern "C" int ilvis0_prefix_point_init(void*buffer,std::size_t bytes,const double*initial,
    const double*limits,const double*z,const double*dv,double dt,double time){
    if(!buffer||bytes!=sizeof(Point))return 2;Point h;
    int code=ilvis0_source_point_init(&h.state,sizeof h.state,initial,limits,z,dv,dt,time);
    if(!code)std::memcpy(buffer,&h,sizeof h);return code;
}
extern "C" int ilvis0_prefix_interval_append(void*buffer,std::size_t bytes,const double*raw,
    double dt,double*point,double*values,double*jac){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;
        Intervals h;if(!source_prefix_read(h,buffer,bytes,interval_tag))return 2;
        if(!(dt>0.)||!std::isfinite(dt))return 2;
        bool full=one(clip_fraction(h.state.point.query,h.state.elapsed,dt))
            &&one(clip_fraction(h.state.domain.query,h.state.elapsed,dt));
        if(!source_prefix_advance(h,dt,full))return 2;
        int code=ilvis0_source_intervals_append(&h.state,sizeof h.state,raw,dt,point,values,jac);
        if(!code)std::memcpy(buffer,&h,sizeof h);return code;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_prefix_point_append(void*buffer,std::size_t bytes,const double*raw,
    double dt,double*values,double*jac){
    using namespace source_derivatives;
    try{
        if(!runtime_ok())return 1;
        Point h;if(!source_prefix_read(h,buffer,bytes,point_tag))return 2;
        if(!(dt>0.)||!std::isfinite(dt))return 2;
        bool full=one(source_point::fraction(h.state.point.query,h.state.elapsed,dt));
        if(!source_prefix_advance(h,dt,full))return 2;
        int code=ilvis0_source_point_append(&h.state,sizeof h.state,raw,dt,values,jac);
        if(!code)std::memcpy(buffer,&h,sizeof h);return code;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_prefix_interval_fork(void*target,std::size_t bytes,const void*source,
    std::size_t source_bytes,double time,double minimum_query){
    using namespace source_derivatives;
    try{
        Intervals h;if(!runtime_ok()||!target||bytes!=sizeof(Intervals)
            ||!source_prefix_read(h,source,source_bytes,interval_tag)||!std::isfinite(time)
            ||!source_prefix_target(h,h.state.elapsed,minimum_query))return 2;
        Jet point_query=Jet(time)+h.state.point.p[25],domain_query=Jet(time)+h.state.domain.p[25];
        if(h.packets&&(point_query.v.lo<=h.state.elapsed||domain_query.v.lo<=h.state.elapsed))return 2;
        h.state.point.query=point_query;h.state.domain.query=domain_query;
        std::memcpy(target,&h,sizeof h);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_prefix_point_fork(void*target,std::size_t bytes,const void*source,
    std::size_t source_bytes,double time,double minimum_query){
    using namespace source_derivatives;
    try{
        Point h;if(!runtime_ok()||!target||bytes!=sizeof(Point)
            ||!source_prefix_read(h,source,source_bytes,point_tag)||!std::isfinite(time)
            ||!source_prefix_target(h,h.state.elapsed,minimum_query))return 2;
        Jet query=Jet(time)+h.state.point.p[25];
        if(h.packets&&query.v.lo<=h.state.elapsed)return 2;
        h.state.point.query=query;std::memcpy(target,&h,sizeof h);return 0;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_prefix_interval_query_lower(const void*source,std::size_t bytes,
    double time,double minimum_query,double*out){
    using namespace source_derivatives;
    try{
        Intervals h;if(!runtime_ok()||!out||!source_prefix_read(h,source,bytes,interval_tag)
            ||!std::isfinite(time)||!std::isfinite(minimum_query))return 2;
        Jet p=Jet(time)+h.state.point.p[25],d=Jet(time)+h.state.domain.p[25];
        *out=std::min({minimum_query,p.v.lo,d.v.lo});return std::isfinite(*out)?0:2;
    }catch(Unsupported e){return e.code;}
}
extern "C" int ilvis0_prefix_point_query_lower(const void*source,std::size_t bytes,
    double time,double minimum_query,double*out){
    using namespace source_derivatives;
    try{
        Point h;if(!runtime_ok()||!out||!source_prefix_read(h,source,bytes,point_tag)
            ||!std::isfinite(time)||!std::isfinite(minimum_query))return 2;
        Jet p=Jet(time)+h.state.point.p[25];
        *out=std::min(minimum_query,p.v.lo);return std::isfinite(*out)?0:2;
    }catch(Unsupported e){return e.code;}
}
