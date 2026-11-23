# Antenna calibrations for the ESA development flight

Published antenna corrections are available for the Nuuk Museum receiver
and all 11 GPS satellites used in the saved two-minute comparison. The
aircraft file identifies its Javad Delta receiver and leaves `ANT # / TYPE`
blank. The ground and satellite corrections can be tested separately from
the unidentified aircraft antenna. [IGS calibration archive](https://files.igs.org/pub/station/general/pcv_archive/) · [Antenna calibration guide](https://igs.org/wg/antenna/)

The Nuuk Museum observation header lists `SEPT POLARX5` and
`SEPPOLANT_X_MF  NONE`. The archived correction for that antenna type
includes GPS L1 and L2. It is a type calibration. The response of the
individual installed antenna and the effects of nearby reflectors still
need evidence. The ground header comes from the original
[EarthScope observation file](https://data.earthscope.org/archive/gnss/highrate/rinex/2023/187/nkar/nkar1870.23d.Z?type=file).
Its SHA-256 is recorded in the [ground score receipt](esa-nkar-ground-score-result.json).

The two checked IGS20 releases bracket the observation date. For each
GPS transmitter used, the selection requires a matching PRN and a
calibration validity interval covering July 6, 2023. The twelve selected
records are identical after excluding the changing `SINEX CODE` line.
Each contains GPS L1 and L2 corrections. [Earlier release](https://files.igs.org/pub/station/general/pcv_archive/igs20_2247.atx) · [Later release](https://files.igs.org/pub/station/general/pcv_archive/igs20_2270.atx)

| GPS PRN | Space vehicle |
| --- | --- |
| G01 | G063 |
| G02 | G061 |
| G03 | G069 |
| G08 | G072 |
| G10 | G073 |
| G14 | G077 |
| G19 | G059 |
| G21 | G045 |
| G24 | G065 |
| G30 | G064 |
| G32 | G070 |

The PRN list comes from `rows[].common_satellites` in the [saved carrier comparison](esa-nuuk-orbit-clock-result.json).
The source SHA-256 values are
`1fb7464228e0dcdb6bc129796f55c70e08cf68c7cacd01fb48335d41930690f6`
for `igs20_2247.atx` and
`11331130a9d5ed7dfc19e185eee2bf5545bad26fa86932a5e15367cbb4b6c7ef`
for `igs20_2270.atx`. Verification selects `START OF ANTENNA` through
`END OF ANTENNA` blocks, uses the fixed-column `TYPE / SERIAL NO` fields,
applies `VALID FROM` and `VALID UNTIL` to transmitter records, and requires
one record per PRN and one exact receiver antenna type.

CODE’s flight-day attitude file covers all 11 satellites at 30-second
intervals bracketing the exact transmit times. It uses GPS time, the IGS20
terrestrial frame, and scalar-first quaternions from the terrestrial frame
to the satellite body frame. The file SHA-256 is
`fdad4fb04be1f9706643132db6d7e2d458486cf9a27eb994a3acb1d33a8c77dd`.
[CODE attitude file](https://www.aiub.unibe.ch/download/CODE/2023/COD0OPSFIN_20231870000_01D_30S_ATT.OBX.gz) · [ORBEX specification](https://geodesy.noaa.gov/pub/ORBEX/ORBEX009.pdf) · [ANTEX specification](https://files.igs.org/pub/station/general/antex14.txt)

This inventory used no new fits and read no reserved flights.
[Completed antenna replay](ESA_NKAR_ANTENNA_RESULT.md) · [Aircraft error budget](ESA_NKAR_ERROR_BUDGET_RESULT.md)
