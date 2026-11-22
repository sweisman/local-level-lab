# Receiver-only GPS reconstruction pilot

Choose one IMU8 and one IMU21 recording from different flight groups.
Use the first eligible segment identifier in each class, ordered
lexicographically, with complete L1 and dual-frequency preflight
coverage. The choice uses only the saved decoder and satellite geometry
records. Freeze the exact segment and epoch identifiers before solving.
Use the earliest original report in each GPS second inside each selected
stretch. Missing reports stay missing.

For each epoch solve position and receiver clock independently under
both existing methods, L1 code and dual-frequency code. Seed each
calculation from the first onboard position in that recording. Use the
same fixed elevation, health and rank checks as the earlier receiver
reconstruction. Compare all later reconstructed positions with the
onboard receiver after the solve. Preserve failed solutions and record
one-second and longer-lag differences. Separate north, east and height
before estimating how the differences affect rates and accelerations.

Use two single-thread workers. Cap the study at 750 epochs per recording,
one solve per method per epoch, 12 iterations per solve, and zero
inertial or Earth-model fits. No ESA confirmation record enters the
study. A comparison between these methods measures processing
sensitivity under the GPS coordinate convention. Both methods can
share satellite, propagation and receiver errors.

[Available satellite coverage](GPS_RECONSTRUCTION_PREFLIGHT_RESULT.md).
