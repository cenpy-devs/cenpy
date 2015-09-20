import unittest
import cenpy

class test_Remote(unittest.TestCase):
    def test_connection(self):
        cenpy.base.Connection(cenpy.explorer.available()[0])

if __name__ == '__main__':
    unittest.main()
