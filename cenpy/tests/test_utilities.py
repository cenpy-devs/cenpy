import unittest
import pandas as pd
import numpy as np
from cenpy.utilities import _coerce as coerce

class TestUtilities(unittest.TestCase):

    def test_coerce(self):
        df_orig = pd.DataFrame({"ints": [1,2,3], "floats": [0.1, 3.79, 14.9], "strings": ["fst", "sec", "thd"]})

        # Cast castable columns into floats
        df_floats = coerce(df_orig, cast_to = np.float64) # Coerce all columns into floats
        # Make sure that coerce didn't change original data
        self.assertFalse(df_orig.equals(df_floats)) 
        # Correct types of columns after coercion:
        float_dtypes = pd.Series(["float64", "float64", "object"], index = ["ints", "floats", "strings"]) 
        # Make sure that the coerced dtypes are as expected
        self.assertTrue(float_dtypes.equals(df_floats.dtypes))

        # Cast castable columns into strings - 
        # Confusingly enough, pandas calls them "objects" 
        df_objects = coerce(df_orig, cast_to = str)
        # Correct types of columns after coercion:
        object_dtypes = pd.Series(["object", "object", "object"], index = ["ints", "floats", "strings"]) 
        self.assertTrue(object_dtypes.equals(df_objects.dtypes))


if __name__ == "__main__":
    unittest.main()