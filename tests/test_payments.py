import unittest
from concurrent.futures import ThreadPoolExecutor
from api.payments import create_payment, records, reset

class PaymentTests(unittest.TestCase):
    def setUp(self):
        reset()

    def test_duplicate_request_creates_one_record(self):
        first = create_payment("fake-customer", 100, "retry-1")
        second = create_payment("fake-customer", 100, "retry-1")
        self.assertEqual(first, second)
        self.assertEqual(len(records()), 1)

    def test_keys_are_scoped_to_account(self):
        create_payment("fake-a", 100, "retry-1")
        create_payment("fake-b", 100, "retry-1")
        self.assertEqual(len(records()), 2)

    def test_concurrent_duplicates_create_one_record(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            payments = list(pool.map(
                lambda _: create_payment("fake-a", 100, "retry-1"), range(32)))
        self.assertTrue(all(p == payments[0] for p in payments))
        self.assertEqual(len(records()), 1)
