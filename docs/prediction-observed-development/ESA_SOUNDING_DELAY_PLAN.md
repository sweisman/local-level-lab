# Same-day atmospheric delay check

Use the two closest active Greenland NOAA IGRA sounding stations on opposite
sides of the ESA 187 development area. Select each station's nominal 12 UTC
sounding on 6 July 2023, the nearest standard observation time to the
opened 520-report sequence. Preserve the complete selected records and
the archive and excerpt hashes. Read the opened receiver parent only.

Use the reported station height for a surface row with missing geopotential
height. Interpolate log pressure between measured heights and interpolate
temperature and dew point against log pressure. Use the same zenith-delay
equation as the saved carrier replay with pressure, temperature and vapour
pressure from each sounding. Evaluate the two soundings separately. Compare
against the original standard-atmosphere model at the same height and
latitude. Record zenith differences and changes over the two-minute forecast
interval. Repeat at heights shifted by ±50 m as a sensitivity check on the
height convention. Do not extrapolate outside the measured profile.

This is a regional-weather sensitivity calculation. Neither sounding is
co-located with the aircraft or measures spatial variation along individual
satellite paths. Treat the two soundings as alternatives and do not assert
that they bound the flight delay. Keep the reconstructions and model scores
unchanged. This report uses at most 520 receiver reports and six profile
settings, with zero new trajectory fits and zero reserved-group reads.

[NOAA sounding format](https://www.ncei.noaa.gov/pub/data/igra/data/igra2-data-format.txt)
