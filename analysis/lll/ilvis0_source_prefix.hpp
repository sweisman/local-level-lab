/* SPDX-License-Identifier: AGPL-3.0-or-later */
#pragma once
#include <cmath>
#include <cstdint>
#include <cstring>
#include <limits>
#include <type_traits>

template<class Parent,std::uint64_t Tag> struct SourcePrefix {
    std::uint64_t magic=Tag;
    Parent state{};
    bool reusable=true;
    std::size_t packets=0;
    double physical_upper=0.;
};

template<class H> bool source_prefix_read(H&h,const void*buffer,std::size_t bytes,std::uint64_t tag){
    static_assert(std::is_trivially_copyable<H>::value,"typed prefix must be copyable");
    if(!buffer||bytes!=sizeof(H))return false;
    std::memcpy(&h,buffer,sizeof h);return h.magic==tag;
}
template<class H> bool source_prefix_advance(H&h,double dt,bool full){
    if(!(dt>0.)||!std::isfinite(dt))return false;
    double end=std::nextafter(h.physical_upper+dt,std::numeric_limits<double>::infinity());
    if(!std::isfinite(end))return false;
    h.physical_upper=end;h.reusable=h.reusable&&full;++h.packets;return true;
}
template<class H> bool source_prefix_target(const H&h,double elapsed,double minimum_query){
    return h.reusable&&std::isfinite(minimum_query)&&minimum_query>=0.
        &&(!h.packets||(minimum_query>elapsed&&minimum_query>h.physical_upper));
}
