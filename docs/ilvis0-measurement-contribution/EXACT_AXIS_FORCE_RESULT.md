# Exact calibration updates reduced every training force gap

All **32 cases** improved on their saved training calibrations. The method
accepted **78 of 192** charged trials after checking the exact packet
intervals. The later gap improved in **28 of 32** cases at the fixed
training correction. All 32 cases still had nonoverlapping intervals
somewhere in training and later data.

| Calibration box | GPS trajectory | Range of final training gaps | Range of final later gaps |
|---|---|---:|---:|
| Narrow | Quadratic | 0.0442–0.0508 m/s² | 0.0420–0.0528 m/s² |
| Wide | Quadratic | 0.0437–0.0498 m/s² | 0.0416–0.0535 m/s² |
| Narrow | Fourth-degree | 0.00652–0.0168 m/s² | 0.00391–0.00570 m/s² |
| Wide | Fourth-degree | 0.00640–0.0161 m/s² | 0.00288–0.00551 m/s² |

The wider box now yields smaller training gaps than the narrow box in
every matched case. The [earlier linear proposals](AXIS_FORCE_PILOT_RESULT.md)
had shown the opposite pattern. Checking the nonlinear gap therefore
changed what the wider calibration allowance achieved in practice.

The [frozen study](EXACT_AXIS_FORCE_PLAN.md) checks the same 991 windows,
both clocks and both GPS motions. The final training correction was saved
before reading the later force intervals. All cases used their six-trial
allowance. The residual gaps are outcomes from those finite local searches.
They do not exclude other calibrations or characterize error shared by
the GPS paths. The packet intervals also leave continuous force direction
unresolved. No Earth-shape decision follows from these diagnostics.

[Trial and result receipt](exact-axis-force-receipt.json) ·
[Archived work and replay](../ilvis0-exact-axis-force-runtime/README.md).
