"""Process-local fake payments. A restart clears all records."""
from threading import Lock

_lock = Lock()
_payments = []
_by_key = {}

def reset():
    with _lock:
        _payments.clear()
        _by_key.clear()

def records():
    with _lock:
        return [dict(payment) for payment in _payments]

def create_payment(account, amount, idempotency_key):
    if amount <= 0:
        raise ValueError("amount must be positive")
    with _lock:
        key = (account, idempotency_key)
        if key in _by_key:
            return dict(_by_key[key])
        payment = {"id": len(_payments) + 1, "account": account, "amount": amount}
        _payments.append(payment)
        _by_key[key] = payment
        return dict(payment)
