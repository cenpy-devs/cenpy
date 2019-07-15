import unittest
import cenpy


class test_tiger(unittest.TestCase):
    def test_connection(self):
        cenpy.tiger.TigerConnection(cenpy.tiger.available(verbose=-1)[0])


if __name__ == "__main__":
    unittest.main()
