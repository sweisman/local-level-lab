// SPDX-License-Identifier: AGPL-3.0-or-later
package io.github.sweisman.locallevellab.model

import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt
import kotlin.math.tan

/**
 * The three Earth models (rotating globe, still globe, still flat disc), in local NED (north, east, down), rad/s. This mirrors
 * analysis/lll/models.py and is checked against docs/test_vectors.json.
 * The app only uses it for the live display. Nothing computed here is ever written to a session.
 */
object Transport {
    const val OMEGA_E = 7.2921150e-5
    const val WGS84_A = 6378137.0
    const val WGS84_E2 = 6.69437999014e-3
    const val RAD_TO_DEG_PER_HOUR = 180.0 / Math.PI * 3600.0

    const val MIN_COS_LAT = 1e-3

    enum class Model(val label: String, val kRotSphere: Double, val kCurv: Double, val kDisc: Double) {
        SPHERE_ROTATING("Sphere, rotating", 1.0, 1.0, 0.0),
        SPHERE_STILL("Sphere, still", 0.0, 1.0, 0.0),
        FLAT_STILL("Flat, still", 0.0, 0.0, 1.0),
    }

    /** Meridian and prime-vertical radii of curvature. */
    fun radii(latRad: Double): Pair<Double, Double> {
        val d = 1.0 - WGS84_E2 * sin(latRad) * sin(latRad)
        return Pair(WGS84_A * (1 - WGS84_E2) / (d * sqrt(d)), WGS84_A / sqrt(d))
    }

    fun earthRateSphere(latRad: Double) = doubleArrayOf(OMEGA_E * cos(latRad), 0.0, -OMEGA_E * sin(latRad))

    fun transportRate(latRad: Double, h: Double, vN: Double, vE: Double): DoubleArray {
        val (rm, rn) = radii(latRad)
        return doubleArrayOf(vE / (rn + h), -vN / (rm + h), -vE * tan(latRad) / (rn + h))
    }

    /** Transport on the pole-centred disc: local level circles the centre at −dλ/dt about the
     *  vertical. vE is the GNSS east velocity; the division only recovers the longitude rate. */
    fun transportRateDisc(latRad: Double, h: Double, vE: Double): DoubleArray {
        val (_, rn) = radii(latRad)
        return doubleArrayOf(0.0, 0.0, -vE / ((rn + h) * maxOf(cos(latRad), MIN_COS_LAT)))
    }

    fun predict(model: Model, latRad: Double, h: Double = 0.0, vN: Double = 0.0, vE: Double = 0.0): DoubleArray {
        val es = earthRateSphere(latRad)
        val tr = transportRate(latRad, h, vN, vE)
        val td = transportRateDisc(latRad, h, vE)
        return DoubleArray(3) { model.kRotSphere * es[it] + model.kCurv * tr[it] + model.kDisc * td[it] }
    }

    fun norm(v: DoubleArray) = sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
}
