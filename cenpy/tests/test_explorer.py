import unittest
import cenpy
from six import iteritems as diter
import pandas
import six

if six.PY3:
    testtype = str
else:
    testtype = unicode


class TestExplorer(unittest.TestCase):
    """
    This tests the explorer module
    """

    def setUp(self):
        self.av = cenpy.explorer.available(verbose=False)
        self.avv = cenpy.explorer.available(verbose=True)

    def test_available(self):
        self.assertIsInstance(self.av, list)
        self.assertNotEqual(len(self.av), 0)
        for name in self.av:
            self.assertIsInstance(name, testtype)

        self.assertIsInstance(self.avv, pandas.DataFrame)
        self.assertNotEqual(len(self.avv), 0)
        self.assertEqual(self.avv.columns[0].lower(), "title")

    def test_explain(self):
        explaintext = cenpy.explorer.explain(self.av[0])
        self.assertIsInstance(explaintext, dict)
        for k, v in diter(explaintext):
            self.assertIsInstance(k, testtype)
            self.assertNotEqual(len(k), 0)
            self.assertIsInstance(v, testtype)
            self.assertNotEqual(len(v), 0)

        explaintextv = cenpy.explorer.explain(self.av[0], verbose=True)
        self.assertIsInstance(explaintextv, dict)
        self.assertGreaterEqual(len(explaintextv), 2)

    def test_fipstable(self):
        AZcounties = [
            "Apache County",
            "Cochise County",
            "Coconino County",
            "Gila County",
            "Graham County",
            "Greenlee County",
            "La Paz County",
            "Maricopa County",
            "Mohave County",
            "Navajo County",
            "Pima County",
            "Pinal County",
            "Santa Cruz County",
            "Yavapai County",
            "Yuma County",
        ]
        currcounties = cenpy.explorer.fips_table("county", in_state="AZ")[3].tolist()
        self.assertEqual(currcounties, AZcounties)


if __name__ == "__main__":
    unittest.main()
