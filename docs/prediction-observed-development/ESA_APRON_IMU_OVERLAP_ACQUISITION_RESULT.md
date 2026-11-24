# GPS observations during the Nuuk stop

The download is complete for the selected two-minute window on ESA flight 187. The archive excerpt contains 241 half-second receiver records, each with GPS observations on two frequencies from 13 satellites. The window overlaps the aircraft's iMAR inertial recording. It was selected from the timing of the stop and the inertial recording before examining any range residuals. [Acquisition plan](ESA_APRON_IMU_OVERLAP_ACQUISITION_PLAN.md)

The two bounded reads delivered every requested byte and agreed across their 128-byte overlap. The server reported FTP status 426 when each partial transfer ended. The saved excerpt passed the record and timestamp checks, including a separate marker immediately after the final selected epoch. The receipt records the source and hashes for the original ranges and the extracted records. [Acquisition receipt](esa-apron-imu-overlap-acquisition.json)

The earlier comparison with Nuuk Museum used 18 seconds before the inertial recording began. The two-minute check uses this excerpt and describes the aircraft's concurrent inertial observations. Both intervals come from a ground stop. The aircraft antenna's error in flight remains open. [Earlier comparison](ESA_APRON_NKAR_RESULT.md) · [Two-minute comparison](ESA_APRON_IMU_OVERLAP_RESULT.md)
