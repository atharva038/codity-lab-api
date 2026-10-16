import unittest
from api.payments import create_payment, reset

class PaymentSuccessTests(unittest.TestCase):
    def setUp(self):
        reset()

    def test_creates_payment(self):
        payment = create_payment("account-a", 100, "request-1")
        self.assertEqual(payment["account"], "account-a")
        self.assertEqual(payment["amount"], 100)

    def test_distinct_requests(self):
        first = create_payment("account-a", 100, "request-1")
        second = create_payment("account-b", 200, "request-2")
        self.assertNotEqual(first["id"], second["id"])
        self.assertEqual(second["account"], "account-b")
