package io.github.sweisman.locallevellab.recording

/** Owns the delayed restart so an explicit stop also invalidates already queued callbacks. */
internal class RecoveryLoop(private val post: (Runnable) -> Unit, private val remove: (Runnable) -> Unit) {
    private var pending: Runnable? = null
    val waiting get() = pending != null

    fun clear() {
        pending?.let(remove)
        pending = null
    }

    fun awaitConfiguration(resume: () -> Unit) {
        clear()
        lateinit var task: Runnable
        task = Runnable {
            if (pending === task) {
                pending = null
                resume()
            }
        }
        pending = task
        post(task)
    }
}
