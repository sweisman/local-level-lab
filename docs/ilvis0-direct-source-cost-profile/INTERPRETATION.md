# The physical source certificates are the main source-stream cost

All six profiles completed in 73.99 seconds. Each reached all 1,471 prefixes
required by its original query. No earlier study was restarted and no new
aircraft fit or full prediction bound was calculated.

In the globe cases, the physical-value stream took about 25–26 seconds per
case, the derivative interval stream about 2.6 seconds, and the direct
remainder stream about 12.6–13.0 seconds. The flat cases were faster in this
run. These measurements include profiler overhead and concurrent worker load;
they are not a benchmark of complete prediction runtime.

The physical-value stream calculates a force certificate at both the midpoint
and endpoint of every packet. The current integrator consumes only the midpoint
certificate. It still needs the endpoint rotation state for the next packet.
Avoiding the unused certificate is therefore a focused optimization candidate.

The candidate passes 12 focused comparisons of midpoint values, intervals,
auxiliary derivatives and subsequent state, plus seven native wrapper/report
checks. The subsequent [24-case qualification](../ilvis0-midpoint-native-controls/INTERPRETATION.md)
also passes, preserving all 348 reports exactly. A separate matched timing
study is still required before generating replacement future bounds. A
speedup has not yet been demonstrated.

The six-case prediction-width target still passes in four cases. Useful
recording-length bounds and an observation-error assessment remain unfinished.

[Timing table and verified evidence](README.md) ·
[Candidate qualification scope](../ilvis0-midpoint-native-controls/PLAN.md) ·
[Remaining width](../ilvis0-east-width-audit/INTERPRETATION.md).
