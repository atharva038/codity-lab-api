import unittest
from api.users import get_user

class StringIdTests(unittest.TestCase):
    def test_string_identifier(self):
        self.assertEqual(get_user("1"), {"name": "Ada"})
