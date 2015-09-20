import unittest
import cenpy

class test_Remote(unittest.TestCase):
    def test_connection(self):
        cenpy.base.Connection(cenpy.base.available()[0])
