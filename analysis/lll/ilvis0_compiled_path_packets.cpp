/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Bounded packet-branch loop. Supplied raw constants are exact binary64 inputs.
 * Ideal-expression bounds; no complete clock partition or native FP proof.
 */
#include "ilvis0_path_step.cpp"
#include <chrono>

extern "C" int ilvis0_compiled_path_packets(int model,int profile,size_t n,
    const double *config,const double *theta,const double *dv,const double *dt,
    const double *parameters,double query,double maximum_seconds,
    double *coordinates,double *state_out,double *fraction_out,double *start_out){
    try{
        if(!runtime_ok())return 1;
        if(n<1||n>1000000||model<0||model>2||(profile!=0&&profile!=1)
            ||!std::isfinite(query)||!std::isfinite(maximum_seconds)||maximum_seconds<=0)return 2;
        using namespace path_arithmetic;check(config,44);check(theta,3*n);check(dv,3*n);check(dt,n);
        const auto began=std::chrono::steady_clock::now();
        auto budget=[&](){if(std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count()>=maximum_seconds)
            throw Unsupported{4};};
        std::array<Jet,27> p;
        for(int j=0;j<27;j++){
            Jet v=read(parameters+8*j);
            if(v.d[0].lo< -1||v.d[0].hi>1||config[15+j]<0)throw Unsupported{2};
            p[j]=constant(config[15+j])*v;
        }
        p[26]=profile?(p[26]+constant(1))/2:constant(0);
        Jet radius=constant(config[43]),gravity=constant(config[42])+p[24];
        State state;for(int i=0;i<3;i++){
            state.coordinates[i]=constant(config[i]);state.velocity[i]=constant(config[3+i])+p[3+i];
            for(int j=0;j<3;j++)state.attitude[i][j]=constant(config[6+3*i+j]);
        }
        Vector offset=rates(model,state.coordinates,{p[6],p[7],p[8]},radius);
        for(int i=0;i<3;i++)state.coordinates[i]=state.coordinates[i]+offset[i];
        state.attitude=mm(state.attitude,rotation({p[0],p[1],p[2]}));
        double start=0;Jet fraction=constant(1);
        for(size_t k=0;k<n;k++){
            budget();if(dt[k]<=0)throw Unsupported{2};
            if(k==n-1){
                fraction=(constant(query)+p[25]-constant(start))/constant(dt[k]);
                if(fraction.d[0].lo<0||fraction.d[0].hi>1)throw Unsupported{2};
            }
            Vector th,vel;
            for(int i=0;i<3;i++){
                Jet dg=constant(1)+p[15+i],da=constant(1)+p[18+i];
                if(dg.d[0].lo<=0||da.d[0].lo<=0)throw Unsupported{2};
                th[i]=(constant(theta[3*k+i])-constant(dt[k])*p[9+i])/dg*fraction;
                vel[i]=(constant(dv[3*k+i])-constant(dt[k])*p[12+i])/da*fraction;
            }
            state=step(model,state,th,vel,constant(dt[k])*fraction,gravity,radius,p[26]);
            if(k<n-1)start+=dt[k];
        }
        Vector lever=mv(state.attitude,{p[21],p[22],p[23]});
        offset=rates(model,state.coordinates,lever,radius);
        budget();for(int i=0;i<3;i++)write(state.coordinates[i]+offset[i],coordinates+8*i);
        write_state(state,state_out);write(fraction,fraction_out);*start_out=start;
        return 0;
    }catch(Unsupported e){return e.code;}
}
