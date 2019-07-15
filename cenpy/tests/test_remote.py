import unittest
import cenpy


class test_remote(unittest.TestCase):
    def test_connection(self):
        cenpy.remote.APIConnection(cenpy.explorer.available(verbose=False)[0])


if __name__ == "__main__":
    unittest.main()
