import tools.entropy
import tools.filter
import os
import shutil
import unittest


class TestEntropyModule(unittest.TestCase):
    """
    Tests for the entropy module

    All the test use a predetermined file adulterado in the unittest_dataset_clean
        
    """

    @classmethod
    def setUpClass(cls):
        if not os.path.exists('unittest_dataset_clean'):
            os.mkdir('unittest_dataset_clean')
        tools.filter.ds_filter('unittest_dataset/adulterado.txt', 'unittest_dataset_clean', apply_limits=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree('unittest_dataset_clean')


if __name__ == '__main__':
    unittest.main(exit=False, verbosity=2)
