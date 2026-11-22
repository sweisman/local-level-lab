# Receiver-supported flight candidates

The separately fixed scan checked 232 retained recordings. 232 passed strict parsing; 0 were recorded as unsupported or invalid.

It found **29 candidate trajectories** totaling 314.6 minutes on **26 conservative recorded-date groups**. Same-day and overlapping recorders count together. These are not established independent flights.

Each candidate has at least 10 continuous minutes, 50 km of sampled receiver path, receiver speed at least 180 km/h, and complete supported raw IMU timing. Selection does not use fused-navigation alignment, roll, climb or course-rate flags. **Level flight has not been established**: turns and climbs may remain. No gyro model residual or Earth-model fit was used.

The [candidate table](candidates.csv) shows time, distance, speed, receiver endpoints, recorder and date group. The [file ledger](files.csv) includes empty and invalid sources.

The next gate is a separately fixed receiver-geometry and motion check, then an information test under the full nuisance space. These candidates cannot enter a coverage or Earth-model claim from this inventory alone. The original 53-stretch study and seven reserved ESA groups remain unchanged.

