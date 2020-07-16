import unittest
import pandas
import numpy
from cenpy.utilities import _coerce as coerce
from cenpy.utilities import _replace_missing as replace_missing

class TestUtilities(unittest.TestCase):

    def test_coerce(self):
        # Make sure coerce works on Series and doesn't change them
        ser_orig = pandas.Series([3,4,5])
        ser_floats = coerce(ser_orig, cast_to = numpy.float64)
        self.assertFalse(ser_orig.equals(ser_floats))

        # Make sure coerce changes what columns it can and doesn't alter
        # original data
        df_orig = pandas.DataFrame({"ints": [1,2,3],
                                    "floats": [0.1, 3.79, 14.9],
                                    "strings": ["fst", "sec", "thd"]})
        df_floats = coerce(df_orig, cast_to = numpy.float64)
        # Correct types of columns after coercion:
        float_dtypes = pandas.Series(["float64", "float64", "object"],
                                     index = ["ints", "floats", "strings"])
        # Make sure that the coerced dtypes are as expected
        self.assertFalse(df_orig.equals(df_floats)) 
        self.assertTrue(float_dtypes.equals(df_floats.dtypes))

        # Cast castable columns into strings - 
        # Confusingly enough, pandas calls them "objects" 
        df_objects = coerce(df_orig, cast_to = str)
        object_dtypes = pandas.Series(["object", "object", "object"],
                                      index = ["ints", "floats", "strings"]) 
        self.assertTrue(object_dtypes.equals(df_objects.dtypes))

        # Make sure an error gets raised if a non-Series/DataFrame object is used
        arr = numpy.zeros((2,2))
        self.assertRaises(TypeError, coerce, arr)


    def test_replace_missing(self):
        df_orig = pandas.DataFrame({"ints": [-888888888,2,3],
                                    "floats": [-555555555, 3.79, -333333333]})
        df_replaced = replace_missing(df_orig)
        # Correct output after replacing missing values
        df_correct = pandas.DataFrame({"ints": [numpy.nan,2,3],
                                       "floats": [numpy.nan, 3.79, numpy.nan]})
        self.assertTrue(df_replaced.equals(df_correct))

        # Make sure an error is raised if non-Series/DataFrame types are used
        arr = numpy.zeros((2,2))
        self.assertRaises(TypeError, replace_missing, arr)


if __name__ == "__main__":
    unittest.main()