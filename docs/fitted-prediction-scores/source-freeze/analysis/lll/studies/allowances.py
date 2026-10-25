# SPDX-License-Identifier: AGPL-3.0-or-later
"""Durable whole-case prepayment with a serial per-call allowance guard.

All work is charged before the caller receives an active guard. Local counters
record attempted work, not durable completion. A crash loses unused prepayment;
the identity remains started and cannot retry or lend its unused allowance.
"""
import os
import threading


class PrepaidCase:
    def __init__(self, journal, identity, *, require_exact):
        from .journal import Journal
        if (not isinstance(journal, Journal) or identity not in journal.limits
                or type(require_exact) is not bool):
            raise ValueError('frozen journal identity and explicit exact-work policy required')
        self.journal = journal; self.identity = identity; self.require_exact = require_exact
        self.limits = dict(journal.limits[identity])
        self._prepaid = {key: 0 for key in self.limits}
        self._attempted = {key: 0 for key in self.limits}
        self._state = 'not_started'; self._used = False; self._owner = None

    def __enter__(self):
        if self._used:
            raise ValueError('prepaid case cannot restart or retry')
        self._used = True
        try:
            self.journal.start(self.identity)
            for key, amount in self.limits.items():
                if amount:
                    self.journal.reserve(self.identity, key, amount)
                self._prepaid[key] = amount
        except BaseException:
            self._state = 'prepayment_failed'
            raise
        self._owner = (os.getpid(), threading.get_ident())
        self._state = 'active'
        return self

    def _check_owner(self):
        if self._state != 'active' or self._owner != (os.getpid(), threading.get_ident()):
            raise ValueError('active original process/thread owner required')

    def reserve(self, **counts):
        """Guard the next attempt against the already durable full prepayment."""
        self._check_owner()
        if (not counts or any(key not in self.limits or type(amount) is not int or amount < 1
                for key, amount in counts.items())):
            raise ValueError('known positive integer resource charges required')
        if any(self._attempted[key]+amount > self._prepaid[key] for key, amount in counts.items()):
            raise ValueError('prepaid work allowance exceeded')
        # Validate every resource before debiting any local counter.
        for key, amount in counts.items():
            self._attempted[key] += amount

    def __exit__(self, error_type, error, traceback):
        self._check_owner()
        if error_type is not None:
            self._state = 'failed_or_interrupted'
        elif self.require_exact and self._attempted != self._prepaid:
            self._state = 'incomplete_work'
            raise ValueError('case did not attempt all declared exact work; no refund or retry')
        else:
            self._state = 'complete'
        return False

    def snapshot(self):
        return dict(identity=self.identity, state=self._state,
            prepaid=dict(self._prepaid), attempted=dict(self._attempted),
            unused_prepaid={key: amount-self._attempted[key] for key, amount in self._prepaid.items()},
            require_exact=self.require_exact, scientific_qualification=False)


class PrepaidNativeBlock:
    """Process-owned local guard after one durable runner-level prepayment.

    Work left after an exception or ordinary early exit is not refunded.
    This class owns no separate ledger and cannot create a new start identity.
    """
    def __init__(self,*,prepay,check_continue,native_calls,packet_visits,check_interval):
        if (not callable(prepay) or not callable(check_continue) or type(native_calls) is not int
                or native_calls<1 or type(packet_visits) is not int or packet_visits<0
                or type(check_interval) is not int or not 1<=check_interval<=128):
            raise ValueError('complete finite prepayment and cooperative check policy required')
        self.prepay=prepay;self.check_continue=check_continue;self.check_interval=check_interval
        self.limits=dict(native_calls=native_calls,packet_visits=packet_visits)
        self.attempted=dict(native_calls=0,packet_visits=0)
        self.state='not_started';self.owner=None;self.prepaid=dict(native_calls=0,packet_visits=0)

    def __enter__(self):
        if self.state!='not_started':raise ValueError('native block cannot restart')
        self.state='prepayment_failed'
        self.check_continue();self.prepay(**self.limits)
        self.prepaid=dict(self.limits);self.owner=(os.getpid(),threading.get_ident());self.state='active'
        return self

    def _active(self):
        if self.state!='active' or self.owner!=(os.getpid(),threading.get_ident()):
            raise ValueError('active original native block process/thread required')

    def reserve(self,*,native_calls,packet_visits):
        self._active()
        if (type(native_calls) is not int or native_calls!=1
                or type(packet_visits) is not int or packet_visits<0):
            raise ValueError('exactly one native call and its nonnegative packet work required')
        counts=dict(native_calls=native_calls,packet_visits=packet_visits)
        if any(self.attempted[k]+v>self.prepaid[k] for k,v in counts.items()):
            raise ValueError('prepaid native allowance exceeded')
        if self.attempted['native_calls']%self.check_interval==0:self.check_continue()
        for key,value in counts.items():self.attempted[key]+=value

    def __exit__(self,error_type,error,traceback):
        self._active();self.state='complete' if error_type is None else 'failed_or_interrupted'
        return False

    def snapshot(self):
        return dict(state=self.state,prepaid=dict(self.prepaid),attempted=dict(self.attempted),
            unused_prepaid={k:self.prepaid[k]-self.attempted[k] for k in self.prepaid},
            scientific_qualification=False)
