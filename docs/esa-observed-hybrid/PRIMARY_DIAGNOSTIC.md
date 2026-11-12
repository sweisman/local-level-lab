# ESA primary-start sensitivity

The verified 24-case substitution study did not qualify. In three
complete groups, the wide and faster methods chose different starts
by training cost. This post-run check compares their saved forecasts;
it does not refit or change the failed gate.

| Model | Processing | Error policy | Wide cost gap | Faster cost gap | Maximum forecast difference |
|---|---|---|---:|---:|---:|
| sphere_rotating | 0 | reported-short-v1 | 1.37371e-08 | 1.00574e-07 | 1.15007e-07 m |
| sphere_still | 0 | reported-short-v1 | 0.000328541 | 0.000229836 | 7.91329e-05 m |
| sphere_still | 1 | reported-persistent-v1 | 4.63799e-07 | 1.67638e-08 | 1.34585e-05 m |

These are numerical sensitivity measurements, not a new
Earth-model comparison or a basis for changing the 0.01 m gate.

[Verified paired report](combined/README.md) · [Machine-readable diagnostic](PRIMARY_DIAGNOSTIC.json).
