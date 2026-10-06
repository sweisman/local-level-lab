# Resolving the airborne gyro format

The supplied Applanix log is preserved with timing and GPS. The unresolved issue is the
physical meaning of its 24-byte IMU8 payload: scales, field order, axes, increments versus
rates, integration interval and applied corrections. Public documentation inspected so far
has not supplied a definition matched to this AV-510 VER5/firmware04.60/ICD15.00 recording.

The [public Applanix interface document](https://asapdata.arc.nasa.gov/share/ASF_Applanix/POSv6_User_ICD.pdf)
establishes the packet container and directs IMU data to POSPac processing. It does not
provide the needed physical payload definition. The inspected processing instructions describe
navigation processing; a smoothed trajectory export would not supply independent gyro data.

There is a documented format for preserving decoded IMU observations:
[Waypoint IMR](https://docs.novatel.com/Waypoint/Content/Data_Formats/IMR_File.htm).
Its header records byte order, rate/increment conventions, scale factors, sampling rate and
time basis. The [raw converter documentation](https://docs.novatel.com/Waypoint/Content/Inertial_Utilities/Raw_IMU_Data_Converter.htm)
does not establish that this exact Applanix log is supported. A compatible export would still
need its source conversions and corrections documented. No software purchase, installation,
conversion or invented IMR header has been performed.

Instrument type numbers belong to their respective manufacturers' formats. For example,
the [NovAtel type table](https://docs.novatel.com/OEM7/Content/SPAN_Commands/CONNECTIMU.htm)
assigns number 8 to LN200; that does not establish the identity or scaling of Applanix IMU8.
An unrelated type table must not determine this decoder.

The next concrete external step is requesting the instrument-specific definition or an
independent physical export. The exact request is drafted in
[AIRBORNE_DATA.md](AIRBORNE_DATA.md). The verified manufacturer
[support page](https://applanix.trimble.com/en/support) lists `techsupport@applanix.com`.
The dataset's [NSIDC page](https://nsidc.org/data/ilvis0/versions/1) is the archive contact
starting point. No inquiry has been sent. Sending one requires explicit user instruction.

Keep the original stream immutable. When a definition or understood export is supplied,
implement the decoder with independent signed-scaling/axis/time checks, establish corrections
and instrument-to-aircraft orientation, and only then assess informative flight windows.
Existing fused navigation may describe maneuvers but must not replace independent gyro
measurements. More files with the same unknown payload do not resolve this issue.
