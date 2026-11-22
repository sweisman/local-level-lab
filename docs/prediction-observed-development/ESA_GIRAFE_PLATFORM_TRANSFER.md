# Bounded GIRAFE transfers and local analysis

Run the FTPS transfer separately from the Python study worker. Check the
source size with an authenticated `curl --head` using the trusted
certificate. For the first GIRAFE platform log, the verified size is
1,860,304,779 bytes. Use an explicit restart command for a nonzero file
offset and a separate limit on how much `curl` reads from that point.

This example obtains 9,856 bytes at offset 465,076,150. Place the output
in an empty, designated local evidence directory. The standard private
credentials are read by `curl`.

```sh
curl --fail --silent --show-error --connect-timeout 8 --max-time 20 \
  --proto '=ftps' \
  --cacert data/external-imu-survey-20261018/esa-sample/ftps-peer.pem \
  --netrc-file "$HOME/.esa-ftps.netrc" \
  --ignore-content-length --quote '+REST 465076150' \
  --range 0-9855 --max-filesize 9856 --output range-465076150.asc \
  'ftps://tpm-if.eo.esa.int/lvl0/187/girafe/LOGXIO_06_07_2023%20_01.Asc'
```

The bytes matched the [verified probe](ESA_GIRAFE_PLATFORM_PROBE_RESULT.md)
exactly. Its SHA-256 is
`9fb281fe462ff2ceb93467ea94f0ce989dd8a94abcf6d17aa881208e23daffb6`.
The ordinary nonzero `--range` request returned the file prefix on this
server. Check the length and a verified overlap before accepting any new
range. Record the source, byte offset, receipt and hash. Seal the checked
local inputs before starting the analysis worker. The worker can then run
with the default sandbox and without an active connection to the archive.
