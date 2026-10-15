import unittest
from api.users import get_user

class UserTests(unittest.TestCase):
    def test_user(self):
        self.assertEqual(get_user(), {"name": "Ada"})
