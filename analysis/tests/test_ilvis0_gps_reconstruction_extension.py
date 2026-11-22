from lll import ilvis0_gps_reconstruction_extension as extension


def test_extension_charges_the_frozen_position_and_iteration_allowance():
    task = {'position_starts': 6, 'limits': dict(native_calls=0, packet_visits=0,
              bound_calls=1, bound_steps=72)}
    assert extension.position_limits(6) == task['limits']

    class Ledger:
        charged = None

        def charge(self, **limits):
            self.charged = limits

    def evaluate(passed_task, context):
        assert passed_task == task
        assert context.charged == {'bound_calls': 1, 'bound_steps': 72}
        return {'position_starts': 6}

    ledger = Ledger()
    assert extension.evaluate_positions(task, ledger, solve=evaluate) == {'position_starts': 6}
