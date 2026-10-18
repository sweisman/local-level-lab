// SPDX-License-Identifier: AGPL-3.0-or-later
// Clock-only reference: no IMU integration, motion model or archival observations.
#include <cstddef>
#include <cstdint>
extern "C" int clock_indices(size_t n,size_t m,const double *times,double u,double scale,int64_t *out) {
    double start=0.;size_t j=0;double offset=u*scale;
    for(size_t k=0;k<n;k++) {
        double end=start+.005;
        while(j<m && times[j]+offset<=end) {out[j]=static_cast<int64_t>(k);j++;}
        start=end;
    }
    return j==m?0:1;
}
