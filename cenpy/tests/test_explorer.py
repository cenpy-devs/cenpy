import unittest
import cenpy
import six.iteritems as diter

class TestExplorer(unittest.Testcase):
    """
    This tests the explorer module
    """
    def setUp(self):
        self.av = cenpy.explorer.available()
        self.avv = cenpy.explorer.available(verbose=True)
    
    def test_available(self):
        self.assertIsInstance(self.av, list)
        self.assertNotEqual(len(self.av), 0)
        for name in self.av:
            self.assertIsInstance(name, unicode)
        
        self.assertIsInstance(self.avv, dict)
        self.assertNotEqual(len(self.avv), 0)
        for k,v in diter(self.avv):
            self.assertIsInstance(k, unicode)
            self.assertNotEqual(len(k), 0) 
            self.assertIsInstance(v, unicode)
            self.assertNotEqual(len(v), 0)

    def test_explain(self):
        explaintext = cenpy.explorer.explain(self.av[0])
        self.assertIsInstance(explaintext, dict)
        self.assertIsInstance(explaintext.keys()[0], unicode)
        self.assertNotEqual(len(explaintext.keys()[0]), 0)
        self.assertIsInstance(explaintext.values()[0], unicode)
        self.assertNotEqual(len(explaintext.values()[0]), 0)
        
        explaintextv = cenpy.explorer.explain(self.av[0], verbose=True)
        self.assertIsInstance(explaintextv, dict)
        self.assertGreaterEqual(len(explaintextv), 2)
    
    def test_fipstable(self):
        AZcounties = ['Apache County',
                     'Cochise County',
                     'Coconino County',
                     'Gila County',
                     'Graham County',
                     'Greenlee County',
                     'La Paz County',
                     'Maricopa County',
                     'Mohave County',
                     'Navajo County',
                     'Pima County',
                     'Pinal County',
                     'Santa Cruz County',
                     'Yavapai County',
                     'Yuma County']
        currcounties = cenpy.explorer.fips_table('county', in_state='AZ')[3].tolist()
        self.assertEqual(currcounties, AZcounties)

if __name__ == '__main__':
    unittest.main()

