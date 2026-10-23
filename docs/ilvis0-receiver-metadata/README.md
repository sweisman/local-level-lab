# What receiver-error information is already recorded?

The 53 selected stretches come from 53 recording files. Saved primary-receiver metadata is available for **53 files**. This is an availability audit, not a count of independent flights.

**0 files** list GST or GBS error-statistics sentences. Presence alone does not establish their interpretation or a usable covariance.

Of 157,070,543 receiver-stream bytes, 151,620,785 were not parsed as NMEA text. Their contents are not identified by this audit; the count does not mean those bytes are raw GNSS measurements or independent accuracy estimates.

| Recording task | Primary-receiver type code | GGA sentences | Listed error-statistics sentences |
|---|---|---:|---|
| 05b6350e07c1b6ff24ad | 17 | 573 | None listed |
| 12fbcbce3c7f52a3eae7 | 16 | 463 | None listed |
| 151ef3a56cffa6acc330 | 17 | 556 | None listed |
| 187a21019bce7b34a04c | 16 | 455 | None listed |
| 1c071fb7315904ebaad9 | 17 | 575 | None listed |
| 25e8081705aa69d3cd6f | 17 | 586 | None listed |
| 26677dfea3fbb0fb60fe | 16 | 670 | None listed |
| 28efd95656987f7d215a | 16 | 692 | None listed |
| 2cde8478531840037384 | 16 | 475 | None listed |
| 30b98b4d421c7e9d0292 | 16 | 447 | None listed |
| 3223697e5fe287b1d443 | 16 | 461 | None listed |
| 397f6c3a7f6f34592195 | 16 | 681 | None listed |
| 41cf7c4dcca04dce0678 | 16 | 446 | None listed |
| 439cd3a0feb0625b60ac | 17 | 569 | None listed |
| 448e008466fda5ad79ea | 16 | 457 | None listed |
| 4849e6ea97a36558b5ac | 17 | 556 | None listed |
| 4876a722de50db44fd7a | 16 | 460 | None listed |
| 60b015c2680f835a1882 | 16 | 686 | None listed |
| 64e033ebd4066f692c7d | 16 | 452 | None listed |
| 65bd45977b48b7d8272a | 17 | 559 | None listed |
| 67027d0caf3ed8e14c5f | 17 | 582 | None listed |
| 683ac516120685564714 | 16 | 691 | None listed |
| 739867a871b2c6dc77f4 | 16 | 650 | None listed |
| 81c18746e768f992c6e7 | 17 | 543 | None listed |
| 8fb44931da423fbde3ef | 17 | 573 | None listed |
| 95a01583566d1a9e080b | 17 | 558 | None listed |
| 9641dfee9ad7cc1aa89e | 17 | 556 | None listed |
| 9b7d1be2c57168d942d1 | 17 | 566 | None listed |
| a0534d9c30195543709c | 16 | 459 | None listed |
| a39b228a8a59800afdfd | 17 | 563 | None listed |
| a4d367c39b7334fa38b8 | 17 | 554 | None listed |
| a5c9a343b38c34d42251 | 17 | 536 | None listed |
| a869222776a6ad61940f | 16 | 456 | None listed |
| aa95315f0205d7f900d9 | 17 | 581 | None listed |
| ad2d5717b2c1c2ed3589 | 16 | 689 | None listed |
| adfd80e2038861ee52fa | 16 | 457 | None listed |
| b2e4d9044f4718247f16 | 16 | 457 | None listed |
| b5b356504236479c028d | 17 | 554 | None listed |
| b763a84552420e8c1d8d | 17 | 566 | None listed |
| b78faf2349870ed2ddb8 | 16 | 672 | None listed |
| b8a39f615741686e805a | 16 | 454 | None listed |
| b97d0866606fd64f4e2e | 16 | 661 | None listed |
| c1ef32dccf7f02f2fba6 | 17 | 554 | None listed |
| c2e72777d4aa69a7f197 | 16 | 680 | None listed |
| cc3e726ffb0436c0f9d8 | 17 | 581 | None listed |
| cd8e05202eb41b83eb26 | 16 | 454 | None listed |
| d2a076353a8123f2d047 | 17 | 552 | None listed |
| e107412e6b64dace9bc0 | 17 | 569 | None listed |
| e8ef81c896d08e296383 | 16 | 652 | None listed |
| ea628c825891d2237361 | 17 | 574 | None listed |
| ed4db68c327edbb1e892 | 17 | 564 | None listed |
| f50467521369a9e0579e | 17 | 573 | None listed |
| ff36ab86ea03f8c2c49b | 16 | 691 | None listed |

NMEA is a receiver text-message format. GGA provides positions and quality fields; its presence does not supply an independently measured noise covariance. The type codes above are recorded identifiers, not manufacturer or physical-unit identifications.

The audit reads saved inspection records only. It reads no original IMU file, uses no model residuals or fused-navigation covariance, and performs no predictions or fits. Missing or unparsed information remains unknown. **The aircraft prediction error law remains unqualified.**

[Frozen scope](PLAN.md) · [Error assumptions](../PREDICTION_ERROR_ASSUMPTIONS.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
