# Compiled multi-packet adapter qualification

Compare the compiled third-order interval adapter with the unchanged native
tangent kernel. Preserve the first 64 packets, bit for bit, from each of the
six qualified generated histories: three physical candidates and two processing
assumptions. Preserve initial conditions, calibration scales and processing.
Use normalized parameter value zero, with a query halfway through packet 64.

For each case, save one native position and all 27 first-derivative columns.
Then integrate all 64 packets in each of the 27 unit parameter directions.
Compare values and the corresponding first derivative using the original
one-micrometre software-comparison tolerance and fixed coordinate scales.
No column, including clock or removal, can be omitted. Higher derivatives retain
their separate rational-reference and known-answer checks.

| Resource | Per case | Total maximum |
|---|---:|---:|
| Started identities | 1 | 6 |
| Native calls / conservative packet visits | 1 / 64 | 6 / 384 |
| Interval calls / packet steps | 27 / 1,728 | 162 / 10,368 |
| Value / first-derivative comparisons | 81 / 81 | 486 / 486 |

One worker uses one numerical thread, reserving two for the existing long-record
study. The cooperative ceiling is 30 seconds per interval call and ten minutes
overall. Freeze all sources, inputs, compiler and environment before launch.
Charge before execution. Preserve failed starts; no retries, signals, allowance
increases, aircraft-original reads or optimizer starts.

This is a short adapter comparison on stable packet/rotation branches, not
uncertainty over the full calibration or clock domain. Passing does not qualify
recording-length ranges, native execution-error bounds, complete branch coverage
or an observational error law. Publication reads sealed results without reruns.
