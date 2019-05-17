import os
import shutil
import unittest

from tools import utility_functions
import tools.filter


class TestUtilityFunctionsModule(unittest.TestCase):
    """
    Tests for the utilityFunctions module

    All the test use a predetermined file adulterado in the unittest_dataset_filtered

    """

    @classmethod
    def setUpClass(cls):
        if not os.path.exists('unittest_dataset_filtered'):
            os.mkdir('unittest_dataset_filtered')
        tools.filter.ds_filter('unittest_dataset/adulterado.txt', 'unittest_dataset_filtered', cutoff_limits=[50, 250])

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('unittest_dataset_filtered')

    # TODO: add unit-tests for all (most of) the functions created

if __name__ == '__main__':
    unittest.main(exit=False, verbosity=2)
