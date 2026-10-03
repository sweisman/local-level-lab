// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.recording.imu

import android.annotation.SuppressLint
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothGatt
import android.bluetooth.BluetoothGattCallback
import android.bluetooth.BluetoothGattCharacteristic
import android.bluetooth.BluetoothGattDescriptor
import android.bluetooth.BluetoothManager
import android.bluetooth.BluetoothProfile
import android.bluetooth.BluetoothSocket
import android.content.Context
import android.os.Build
import android.os.Handler
import android.os.HandlerThread
import android.os.SystemClock
import java.io.IOException
import java.util.UUID

/**
 * A live byte stream from the IMU. Every read is handed over verbatim with the phone's
 * elapsedRealtimeNanos at arrival, the clock the session uses for everything.
 *
 * The link reconnects on its own until close(). Callbacks arrive on the link's own thread.
 */
interface ImuLink {
    interface Listener {
        fun onBytes(arrivalNs: Long, data: ByteArray)
        fun onState(connected: Boolean, detail: String)
    }

    fun open()
    fun write(cmds: List<ByteArray>)
    fun close()

    companion object {
        fun create(ctx: Context, variant: Variant, address: String, l: Listener): ImuLink = when (variant) {
            Variant.SPP -> SppLink(ctx, address, l)
            Variant.BLE -> BleLink(ctx, address, l)
        }
    }
}

private fun backoffMs(attempt: Int) = minOf(15_000L, 1000L shl minOf(attempt, 4))

/** Variant A: HC-06 serial port profile (RFCOMM). The stream is reliable while connected. */
@SuppressLint("MissingPermission")  // callers check BLUETOOTH_CONNECT before opening a link
class SppLink(ctx: Context, private val address: String, private val l: ImuLink.Listener) : ImuLink {
    private val adapter: BluetoothAdapter? = ctx.getSystemService(BluetoothManager::class.java)?.adapter
    @Volatile private var closed = false
    @Volatile private var socket: BluetoothSocket? = null
    private var thread: Thread? = null

    override fun open() {
        closed = false
        thread = Thread({ loop() }, "lll-imu-spp").apply { priority = Thread.MAX_PRIORITY; start() }
    }

    private fun loop() {
        var attempt = 0
        val buf = ByteArray(4096)
        while (!closed) {
            try {
                val dev: BluetoothDevice = adapter?.getRemoteDevice(address) ?: throw IOException("Bluetooth is off")
                adapter.cancelDiscovery()
                val s = dev.createRfcommSocketToServiceRecord(SPP_UUID)
                socket = s
                s.connect()
                attempt = 0
                l.onState(true, "connected")
                val input = s.inputStream
                while (!closed) {
                    val n = input.read(buf)
                    if (n < 0) throw IOException("stream ended")
                    if (n > 0) l.onBytes(SystemClock.elapsedRealtimeNanos(), buf.copyOf(n))
                }
            } catch (e: IOException) {
                runCatching { socket?.close() }
                socket = null
                if (closed) break
                l.onState(false, e.message ?: "disconnected")
                try { Thread.sleep(backoffMs(attempt++)) } catch (_: InterruptedException) { break }
            } catch (e: SecurityException) {
                l.onState(false, "Bluetooth permission missing")
                break
            }
        }
    }

    override fun write(cmds: List<ByteArray>) {
        Thread({
            val out = socket?.outputStream ?: return@Thread
            for (c in cmds) {
                runCatching { synchronized(this) { out.write(c); out.flush() } }
                Thread.sleep(120)  // the device needs time between config writes
            }
        }, "lll-imu-spp-write").start()
    }

    override fun close() {
        closed = true
        runCatching { socket?.close() }
        thread?.interrupt()
    }

    companion object {
        val SPP_UUID: UUID = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
    }
}

/**
 * Variant B: BLE GATT notifications. Writes are spaced out on the link's thread because the
 * stack allows only one outstanding operation at a time. UUIDs are WitMotion's published ones,
 * unverified until the bench test.
 */
@SuppressLint("MissingPermission")
class BleLink(private val ctx: Context, private val address: String, private val l: ImuLink.Listener) : ImuLink {
    private val adapter: BluetoothAdapter? = ctx.getSystemService(BluetoothManager::class.java)?.adapter
    private val ht = HandlerThread("lll-imu-ble").apply { start() }
    private val h = Handler(ht.looper)
    @Volatile private var closed = false
    private var gatt: BluetoothGatt? = null
    private var writeCh: BluetoothGattCharacteristic? = null
    private var attempt = 0
    private var nextWriteAt = 0L

    override fun open() { closed = false; h.post { connect() } }

    private fun connect() {
        if (closed) return
        val dev = adapter?.getRemoteDevice(address) ?: run { retry("Bluetooth is off"); return }
        gatt = dev.connectGatt(ctx, false, cb, BluetoothDevice.TRANSPORT_LE, BluetoothDevice.PHY_LE_1M_MASK, h)
    }

    private fun retry(why: String) {
        gatt?.close(); gatt = null; writeCh = null
        h.removeCallbacks(poll)
        if (closed) return
        l.onState(false, why)
        h.postDelayed({ connect() }, backoffMs(attempt++))
    }

    private val poll = object : Runnable {
        override fun run() { send(WitConfig.POLL_MAG_TEMP); h.postDelayed(this, 1000) }
    }

    private val cb = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(g: BluetoothGatt, status: Int, state: Int) {
            h.post {
                if (state == BluetoothProfile.STATE_CONNECTED) { g.requestConnectionPriority(BluetoothGatt.CONNECTION_PRIORITY_HIGH); g.discoverServices() }
                else retry("disconnected (status $status)")
            }
        }

        override fun onServicesDiscovered(g: BluetoothGatt, status: Int) {
            h.post {
                val svc = g.getService(SERVICE) ?: run { retry("WitMotion service not found"); return@post }
                val notify = svc.getCharacteristic(NOTIFY) ?: run { retry("notify characteristic not found"); return@post }
                writeCh = svc.getCharacteristic(WRITE)
                g.setCharacteristicNotification(notify, true)
                val d = notify.getDescriptor(CCCD)
                if (d != null) {
                    if (Build.VERSION.SDK_INT >= 33) g.writeDescriptor(d, BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE)
                    else @Suppress("DEPRECATION") { d.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE; g.writeDescriptor(d) }
                }
                attempt = 0
                nextWriteAt = SystemClock.uptimeMillis() + 300
                l.onState(true, "connected")
                h.postDelayed(poll, 1000)
            }
        }

        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic, value: ByteArray) {
            l.onBytes(SystemClock.elapsedRealtimeNanos(), value.copyOf())
        }

        @Deprecated("Deprecated in Java")
        override fun onCharacteristicChanged(g: BluetoothGatt, c: BluetoothGattCharacteristic) {
            if (Build.VERSION.SDK_INT < 33) @Suppress("DEPRECATION") l.onBytes(SystemClock.elapsedRealtimeNanos(), c.value.copyOf())
        }
    }

    /** Queue one write on the link thread, at least 150 ms after the previous one. */
    private fun send(cmd: ByteArray) {
        val at = maxOf(SystemClock.uptimeMillis(), nextWriteAt)
        nextWriteAt = at + 150
        h.postAtTime({
            val g = gatt ?: return@postAtTime
            val ch = writeCh ?: return@postAtTime
            if (Build.VERSION.SDK_INT >= 33) g.writeCharacteristic(ch, cmd, BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE)
            else @Suppress("DEPRECATION") { ch.writeType = BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE; ch.value = cmd; g.writeCharacteristic(ch) }
        }, at)
    }

    override fun write(cmds: List<ByteArray>) { h.post { cmds.forEach { send(it) } } }

    override fun close() {
        closed = true
        h.post {
            h.removeCallbacksAndMessages(null)
            gatt?.disconnect(); gatt?.close(); gatt = null
            ht.quitSafely()
        }
    }

    companion object {
        val SERVICE: UUID = UUID.fromString("0000ffe5-0000-1000-8000-00805f9a34fb")
        val NOTIFY: UUID = UUID.fromString("0000ffe4-0000-1000-8000-00805f9a34fb")
        val WRITE: UUID = UUID.fromString("0000ffe9-0000-1000-8000-00805f9a34fb")
        val CCCD: UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")
    }
}
