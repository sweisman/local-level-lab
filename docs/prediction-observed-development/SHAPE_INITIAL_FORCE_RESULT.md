# The zero-centred history now passes

The original four generated histories passed with the outward-rounded
initial-force bound. All 16 reference positions agreed with the compiled
forecasts within 1.5 nm. Each reported remainder contained the three
prescribed calibration probes within the frozen comparison tolerance.

| Model | Packet size | Largest remainder at the final query |
| --- | ---: | ---: |
| Zero-field globe | 5 ms | 0.573 µm at 0.7975 s |
| Zero-field disc | 5 ms | 0.439 µm at 0.7975 s |
| Zero-field globe | 250 ms | 0.305 mm at 39.875 s |
| Zero-field disc | 250 ms | 0.240 mm at 39.875 s |

The policy computes the bias, gain and rotation contributions from the
exact stored coefficients and rounds the resulting limit outward. It
gives the reference a distinct identity while preserving its centre
and all 27 physical derivative columns. The earlier reference policy
still reproduces the initial-force rejection. The new policy rebuilt
successfully from its saved reference report.

The shared force calculation reduced each case to 160 force-profile
packet visits for four reports. The [frozen plan](SHAPE_GRAVITY_HISTORY_V4_PLAN.md)
charged four bound calls and 16 native forecasts. It read no flight
recordings and performed no fits. The
[first archived-packet check](ESA_SHAPE_PREFIX_PREFLIGHT_RESULT.md) then
matched both disc positions. Its globe bound reached the time limit.

[Sealed evidence](shape-gravity-history-v4-evidence/README.md) ·
[Earlier results](SHAPE_GRAVITY_HISTORY_RESULT.md).
