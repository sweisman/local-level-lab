// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording

import java.io.File
import java.io.RandomAccessFile

/** Truncate only an incomplete final record after process death. Complete bytes remain exact. */
object Journal {
    fun repair(file: File, binary: Boolean): Long {
        if (!file.exists()) return 0
        RandomAccessFile(file, "rw").use { f ->
            val size = f.length()
            var end = 0L
            if (binary) {
                while (f.filePointer + 10 <= size) {
                    f.skipBytes(8)
                    val n = f.readUnsignedByte() or (f.readUnsignedByte() shl 8)
                    if (n == 0 || f.filePointer + n > size) break
                    f.seek(f.filePointer + n)
                    end = f.filePointer
                }
            } else {
                var pos = size
                while (pos > 0) {
                    f.seek(--pos)
                    if (f.read() == 10) { end = pos + 1; break }
                }
            }
            f.setLength(end)
            return size - end
        }
    }
}
