# Current stretch analytics

**53 globe preferences, 0 flat preferences, 0 unresolved** among 53 preselected stretches.

The [stretch CSV](stretch-analytics.csv) contains all 53 stretches; the [fit and diagnostic history](fit-analytics.csv) retains all 791 records. It includes 712 earlier fitting attempts, 21 initial boundary-diagnostic identities, four adjacent-boundary identities, four clustered-boundary identities, six matched two-case identities, four representable-side identities, twelve focused calibration-correction identities and 28 final-stretch identities. An operation column separates full fits, boundary checks and conditional profiles. The interrupted identity retains its reserved allowance and has no asserted evaluation count. Repeats and controls never replace primary fits. Repeat-pair counts and failed identities preserve every required check, including stretches with several pairs. Raw gyro summaries, receiver trajectories and [paired-recorder differences](shared-leg-pairs.csv) are copied unchanged from the verified preceding snapshot. Only dispositions and saved numerical outcomes are updated.

The [column definitions and measurement limitations](../ilvis0-position-stability-trial-20261013/ANALYTICS.md) continue to apply. Group-1 attitude remains a context diagnostic, never independent shape evidence. No original recordings or numerical predictions were read or generated.

<!-- stretch-table:start -->

## All selected stretches

This abridged table comes from the [comprehensive CSV](stretch-analytics.csv). Course is GPS travel direction, not aircraft heading; negative latitude is south.

| Recording / stretch | UTC interval | IMU type | Minutes | Speed min / median (km/h) | Course | Mean latitude | Track (km) | Current disposition |
|---|---|---:|---:|---:|---:|---:|---:|---|
| `ILVIS0_applanix_55124_Ames_610-20Oct09_20Oct09.013`<br>`034547522e2d98947b598466` | 2009-10-20T13:23:57.047162Z<br>to 2009-10-20T13:34:45Z | 21 | 10.80 | 837.6 / 848.7 | 203.6° | -62.95° | 151.8 | Globe preferred |
| `ILVIS0_applanix_55124_Ames_510-20oct09_20Oct09.013`<br>`b365bdf39150ee6afc303ac1` | 2009-10-20T13:25:32.783556Z<br>to 2009-10-20T13:35:17.822442Z | 8 | 9.75 | 841.4 / 849.1 | 203.7° | -63.07° | 137.3 | Globe preferred |
| `ILVIS0_applanix_55128_Ames_510-24Oct09_24Oct09.013`<br>`3df34ea39a6cbdbe15bb0f36` | 2009-10-24T13:25:51.649791Z<br>to 2009-10-24T13:36:59.693758Z | 8 | 11.13 | 851.9 / 858.0 | 119.5° | -62.65° | 158.3 | Globe preferred |
| `ILVIS0_applanix_55128_Ames_610-24Oct09_24Oct09.013`<br>`233183f67270980491416678` | 2009-10-24T13:25:59.003646Z<br>to 2009-10-24T13:37:05.003101Z | 21 | 11.10 | 852.0 / 858.1 | 119.5° | -62.66° | 157.8 | Globe preferred |
| `ILVIS0_applanix_55129_610-25Oct09_25Oct09.013`<br>`c16df82d514fc69d11d941d2` | 2009-10-25T14:57:57.272991Z<br>to 2009-10-25T15:08:45.272659Z | 21 | 10.80 | 839.8 / 843.1 | 195.6° | -63.70° | 151.1 | Globe preferred |
| `ILVIS0_applanix_55131_610-27Oct09_27Oct09.013`<br>`fad74da3a09951b31e882472` | 2009-10-27T13:28:57.062636Z<br>to 2009-10-27T13:34:29.062525Z | 21 | 5.53 | 787.1 / 790.3 | 201.9° | -63.25° | 72.4 | Globe preferred |
| `ILVIS0_applanix_55133_610-29Oct09_29Oct09.013`<br>`0e73879f98c3b701fd7c42df` | 2009-10-29T13:26:58.932564Z<br>to 2009-10-29T13:38:07.931964Z | 21 | 11.15 | 836.1 / 837.7 | 191.7° | -63.96° | 154.8 | Globe preferred |
| `ILVIS0_applanix_55140_610-05Nov09_05Nov09.013`<br>`fd7b81e48a4122b149c4925b` | 2009-11-05T14:40:28.063157Z<br>to 2009-11-05T14:46:22.062864Z | 21 | 5.90 | 718.2 / 737.1 | 152.0° | -61.57° | 71.8 | Globe preferred |
| `ILVIS0_applanix_55277_20100322_610_AMES_08Dec09.013`<br>`7024120d59221e8eaf127084` | 2010-03-22T07:52:03.263559Z<br>to 2010-03-22T07:59:19.264160Z | 21 | 7.27 | 801.8 / 820.7 | 8.7° | 42.29° | 98.9 | Globe preferred |
| `ILVIS0_applanix_55284_20100329_610_AMES_29Mar100329_103936.013`<br>`b4ab6e128de963c2ce69aa51` | 2010-03-29T13:06:37.134207Z<br>to 2010-03-29T13:13:30.134487Z | 21 | 6.88 | 862.3 / 863.2 | 333.8° | 75.28° | 98.2 | Globe preferred |
| `ILVIS0_applanix_55295_20100409_610_LVIS_09Apr10.013`<br>`7df21c836bec5751f83c0cce` | 2010-04-09T12:56:16.115058Z<br>to 2010-04-09T13:00:20.115282Z | 21 | 4.07 | 834.3 / 841.7 | 86.4° | 71.89° | 56.5 | Globe preferred |
| `ILVIS0_applanix_55300_20100414_Ames610_14Apr10.013`<br>`bb8061a43b4f14b6262ceda1` | 2010-04-14T12:41:33.104523Z<br>to 2010-04-14T12:47:57.103723Z | 21 | 6.40 | 793.7 / 794.4 | 194.5° | 72.59° | 84.1 | Globe preferred |
| `ILVIS0_applanix_55842_610_LVIS.013`<br>`48c1bfe2f1aeb31c9386841d` | 2011-10-08T15:00:19Z<br>to 2011-10-08T15:07:25Z | 21 | 7.10 | 891.4 / 904.5 | 202.0° | -61.42° | 106.5 | Globe preferred |
| `ILVIS0_applanix_55844_610_LVIS.013`<br>`8bf60391909fe8988c23621a` | 2011-10-10T12:20:04.228661Z<br>to 2011-10-10T12:26:21Z | 21 | 6.28 | 788.1 / 796.4 | 199.6° | -57.07° | 82.8 | Globe preferred |
| `ILVIS0_applanix_55846_610_LVIS.013`<br>`2791235ca0b11b1ef4386e21` | 2011-10-12T12:05:40Z<br>to 2011-10-12T12:13:02Z | 21 | 7.37 | 809.3 / 822.5 | 177.7° | -56.66° | 100.7 | Globe preferred |
| `ILVIS0_applanix_57289_610_LVIS_38614965.013`<br>`d9d91c8edba5721931856fc9` | 2015-09-24T12:47:53Z<br>to 2015-09-24T12:55:12Z | 21 | 7.32 | 788.8 / 793.6 | 199.9° | -57.39° | 96.7 | Globe preferred |
| `ILVIS0_applanix_57289_610_loaner_24Sept15LVIS.013`<br>`da346f70a6661ee42cecea19` | 2015-09-24T13:06:34Z<br>to 2015-09-24T13:15:39Z | 21 | 9.08 | 769.8 / 784.8 | 201.2° | -59.55° | 118.2 | Globe preferred |
| `ILVIS0_applanix_57289_610_DMS_24Sept15DMS.013`<br>`2f7e37c48f3b4423c55662dd` | 2015-09-24T13:19:15.032273Z<br>to 2015-09-24T13:28:40Z | 21 | 9.42 | 741.4 / 755.6 | 202.2° | -60.91° | 117.6 | Globe preferred |
| `ILVIS0_applanix_57291_610_LVIS_38614965.013`<br>`f7677e15295077fd8cfd3089` | 2015-09-26T13:25:00Z<br>to 2015-09-26T13:32:19Z | 21 | 7.32 | 820.0 / 825.2 | 177.4° | -58.03° | 100.4 | Globe preferred |
| `ILVIS0_applanix_57291_610_loaner_26Sept15LVIS.013`<br>`abe881b5c87cc878226a9aef` | 2015-09-26T14:01:50Z<br>to 2015-09-26T14:10:47Z | 21 | 8.95 | 791.9 / 797.8 | 177.0° | -62.59° | 118.5 | Globe preferred |
| `ILVIS0_applanix_57291_610_DMS_26Sept15DMS.013`<br>`e6629f14d2e03e471a446e06` | 2015-09-26T14:02:21.171782Z<br>to 2015-09-26T14:11:32.973698Z | 21 | 9.20 | 791.9 / 798.3 | 177.0° | -62.67° | 121.6 | Globe preferred |
| `ILVIS0_applanix_57294_610_loaner_29Sept15LVIS.013`<br>`dac266ab5c198050d25b17f6` | 2015-09-29T12:47:39Z<br>to 2015-09-29T12:56:32Z | 21 | 8.88 | 884.6 / 887.9 | 172.9° | -59.13° | 131.0 | Globe preferred |
| `ILVIS0_applanix_57294_610_DMS_29Sept15DMS.013`<br>`01177d345ecb28bcfdcc6a4f` | 2015-09-29T12:48:57.087609Z<br>to 2015-09-29T12:57:28.988956Z | 21 | 8.53 | 884.6 / 888.0 | 172.8° | -59.28° | 125.4 | Globe preferred |
| `ILVIS0_applanix_57298_610_LVIS_38614965.013`<br>`4fad619380ea429cbf6cbcc9` | 2015-10-03T14:01:56.618753Z<br>to 2015-10-03T14:06:39Z | 21 | 4.71 | 905.5 / 915.8 | 166.3° | -61.61° | 71.4 | Globe preferred |
| `ILVIS0_applanix_57298_610_loaner_03Oct15LVIS.013`<br>`d4e793dd58b79bf4d95c692b` | 2015-10-03T14:18:15Z<br>to 2015-10-03T14:27:08Z | 21 | 8.88 | 881.4 / 895.6 | 165.1° | -64.01° | 131.6 | Globe preferred |
| `ILVIS0_applanix_57298_610_DMS_03Oct15DMS.013`<br>`f50ff54d2e6175d2e8277823` | 2015-10-03T14:18:43.047077Z<br>to 2015-10-03T14:27:51Z | 21 | 9.13 | 881.4 / 894.0 | 165.1° | -64.08° | 135.0 | Globe preferred |
| `ILVIS0_applanix_57300_610_LVIS_38614965.013`<br>`570b37d23af5e245dd461051` | 2015-10-05T12:45:50Z<br>to 2015-10-05T12:53:08Z | 21 | 7.30 | 859.5 / 878.1 | 210.0° | -58.88° | 106.6 | Globe preferred |
| `ILVIS0_applanix_57300_610_loaner_05Oct15LVIS.013`<br>`8dacbcf9f1e2774318723460` | 2015-10-05T13:08:08Z<br>to 2015-10-05T13:14:34.584286Z | 21 | 6.44 | 828.8 / 847.8 | 212.5° | -61.29° | 90.3 | Globe preferred |
| `ILVIS0_applanix_57302_610_LVIS_38614965.013`<br>`711e7aade97a54f71ac5d9c5` | 2015-10-07T12:54:45.006409Z<br>to 2015-10-07T13:00:18.054208Z | 21 | 5.55 | 755.1 / 772.6 | 172.9° | -58.97° | 70.8 | Globe preferred |
| `ILVIS0_applanix_57302_610_loaner_07Oct15LVIS.013`<br>`31d7e5019dfdc9e2e6387206` | 2015-10-07T13:27:38Z<br>to 2015-10-07T13:36:31Z | 21 | 8.88 | 837.7 / 854.2 | 131.9° | -62.25° | 125.7 | Globe preferred |
| `ILVIS0_applanix_57302_610_DMS_07Oct15DMS.013`<br>`a953c8ddf4fae255674de128` | 2015-10-07T13:27:51.097754Z<br>to 2015-10-07T13:36:56Z | 21 | 9.08 | 837.6 / 854.6 | 131.8° | -62.27° | 128.4 | Globe preferred |
| `ILVIS0_applanix_57305_610_LVIS_38614965.013`<br>`e543e7b6e878b96a1966dbb6` | 2015-10-10T13:51:59Z<br>to 2015-10-10T13:59:04Z | 21 | 7.08 | 816.6 / 823.4 | 172.8° | -59.41° | 96.8 | Globe preferred |
| `ILVIS0_applanix_57305_610_loaner_10Oct15LVIS.013`<br>`9f4d888995ab94bb8eff4df6` | 2015-10-10T14:12:28Z<br>to 2015-10-10T14:21:40Z | 21 | 9.20 | 900.7 / 914.2 | 147.7° | -61.94° | 139.4 | Globe preferred |
| `ILVIS0_applanix_57305_610_DMS_10Oct15DMS.013`<br>`f66ab49757292bc3c396aba2` | 2015-10-10T14:14:55Z<br>to 2015-10-10T14:24:15Z | 21 | 9.33 | 900.7 / 913.9 | 147.3° | -62.23° | 141.4 | Globe preferred |
| `ILVIS0_applanix_57307_610_loaner_12Oct15LVIS.013`<br>`74ec8f62cb621604ddcdde9c` | 2015-10-12T13:15:12Z<br>to 2015-10-12T13:23:47Z | 21 | 8.58 | 820.4 / 828.4 | 191.9° | -61.23° | 118.0 | Globe preferred |
| `ILVIS0_applanix_57307_610_DMS_12Oct15DMS.013`<br>`705de394963c8be15c580512` | 2015-10-12T13:26:58.778403Z<br>to 2015-10-12T13:30:59Z | 21 | 4.00 | 786.5 / 795.9 | 201.4° | -62.35° | 52.7 | Globe preferred |
| `ILVIS0_applanix_57312_610_LVIS_38614965.013`<br>`8f2a00e9f13b367202e4d46a` | 2015-10-17T12:54:03Z<br>to 2015-10-17T13:01:19Z | 21 | 7.27 | 748.9 / 755.5 | 195.1° | -58.81° | 91.2 | Globe preferred |
| `ILVIS0_applanix_57312_610_loaner_17Oct15LVIS.013`<br>`8cc288f5de7e88878c04b7f1` | 2015-10-17T13:17:05Z<br>to 2015-10-17T13:25:56Z | 21 | 8.85 | 775.6 / 779.1 | 196.4° | -61.45° | 114.5 | Globe preferred |
| `ILVIS0_applanix_57312_610_DMS_17Oct15DMS.013`<br>`a6e658d1550299e4eb9f00a3` | 2015-10-17T13:17:44Z<br>to 2015-10-17T13:26:46Z | 21 | 9.03 | 775.5 / 779.1 | 196.5° | -61.54° | 117.0 | Globe preferred |
| `ILVIS0_applanix_57315_610_LVIS_38614965.013`<br>`be1d75a0e47ff1c972865ba7` | 2015-10-20T12:54:29Z<br>to 2015-10-20T13:01:44Z | 21 | 7.25 | 752.0 / 761.1 | 199.0° | -58.65° | 91.8 | Globe preferred |
| `ILVIS0_applanix_57315_610_loaner_20Oct15LVIS.013`<br>`61e1b08da0912019eb521cd9` | 2015-10-20T13:15:17Z<br>to 2015-10-20T13:24:12Z | 21 | 8.92 | 746.7 / 754.1 | 200.5° | -60.95° | 111.5 | Globe preferred |
| `ILVIS0_applanix_57315_610_DMS_20Oct15DMS.013`<br>`50f24131843071ae9312c082` | 2015-10-20T13:17:24Z<br>to 2015-10-20T13:26:38Z | 21 | 9.23 | 749.7 / 753.8 | 200.6° | -61.19° | 115.5 | Globe preferred |
| `ILVIS0_applanix_57317_610_LVIS_38614965.013`<br>`c69d0a93113d86b5264f92eb` | 2015-10-22T12:53:27Z<br>to 2015-10-22T13:00:38Z | 21 | 7.18 | 712.0 / 726.5 | 172.9° | -58.78° | 86.7 | Globe preferred |
| `ILVIS0_applanix_57317_610_DMS_21Oct15DMS.013`<br>`ec6effbf9b2172b1389afc96` | 2015-10-22T13:14:24Z<br>to 2015-10-22T13:20:34.617838Z | 21 | 6.18 | 807.7 / 825.0 | 106.1° | -60.36° | 84.7 | Globe preferred |
| `ILVIS0_applanix_57320_610_LVIS_38614965.013`<br>`b4e44ddc0f130ecd45674c78` | 2015-10-25T12:52:41Z<br>to 2015-10-25T12:59:54Z | 21 | 7.22 | 822.0 / 824.9 | 207.5° | -58.97° | 98.8 | Globe preferred |
| `ILVIS0_applanix_57320_610_loaner_25Oct15LVIS.013`<br>`2eb8727803b318a39937e7ec` | 2015-10-25T13:09:19Z<br>to 2015-10-25T13:18:17Z | 21 | 8.97 | 811.8 / 823.6 | 209.2° | -60.87° | 122.2 | Globe preferred |
| `ILVIS0_applanix_57320_610_DMS_25Oct15DMS.013`<br>`370cec66878c4c1cf84b4ceb` | 2015-10-25T13:14:25Z<br>to 2015-10-25T13:23:38Z | 21 | 9.22 | 811.8 / 816.9 | 209.8° | -61.43° | 124.9 | Globe preferred |
| `ILVIS0_applanix_57322_610_LVIS_38614965.013`<br>`f5c1fca513b9b40dffba93eb` | 2015-10-27T14:02:23Z<br>to 2015-10-27T14:06:53.480000Z | 21 | 4.51 | 833.8 / 842.8 | 195.0° | -58.96° | 62.9 | Globe preferred |
| `ILVIS0_applanix_57322_610_loaner_27Oct15bLVIS.013`<br>`013fdb894ff28509889a8896` | 2015-10-27T14:25:35Z<br>to 2015-10-27T14:34:30Z | 21 | 8.92 | 829.9 / 834.5 | 196.6° | -62.02° | 123.5 | Globe preferred |
| `ILVIS0_applanix_57322_610_DMS_27Oct15bDMS.013`<br>`2a56eb8fa7d4e10c9a867bb0` | 2015-10-27T14:27:23Z<br>to 2015-10-27T14:36:31Z | 21 | 9.13 | 829.8 / 834.7 | 196.7° | -62.25° | 126.6 | Globe preferred |
| `ILVIS0_applanix_57324_610_LVIS_38614965.013`<br>`c028fde63f91c3f1067df4ad` | 2015-10-29T12:57:46Z<br>to 2015-10-29T13:03:39.531728Z | 21 | 5.89 | 828.3 / 835.0 | 176.3° | -58.81° | 81.6 | Globe preferred |
| `ILVIS0_applanix_57324_610_loaner_29Oct15LVIS.013`<br>`7ee5e21c025360c970124eeb` | 2015-10-29T13:11:09.888451Z<br>to 2015-10-29T13:20:04Z | 21 | 8.90 | 883.6 / 892.4 | 146.6° | -60.61° | 131.7 | Globe preferred |
| `ILVIS0_applanix_57324_610_DMS_29Oct15DMS.013`<br>`5a642167dfb523f6c9cc284c` | 2015-10-29T13:16:56Z<br>to 2015-10-29T13:26:08Z | 21 | 9.20 | 868.4 / 879.9 | 145.9° | -61.26° | 134.4 | Globe preferred |

<!-- stretch-table:end -->
