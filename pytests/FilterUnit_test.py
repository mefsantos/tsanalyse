import tools.filter
import unittest
import os
import shutil


class TestCleanModule(unittest.TestCase):
    """Test functions in clean module"""

    def test_dir_nolimit_nokt(self):
        """
        Test the module's entry function with a directory,
        no keep_time or apply_limits used.
        All files that existed originally must still exist, and
        the resulting file should have only one column.
    """
        if not os.path.exists('unittest_dataset_filtered'):
            os.mkdir('unittest_dataset_filtered')
        tools.filter.ds_filter('unittest_dataset', 'unittest_dataset_filtered')
        self.assertEqual(os.listdir('unittest_dataset'), os.listdir('unittest_dataset_filtered'))
        for filename in os.listdir('unittest_dataset'):
            fdclean = open(os.path.join('unittest_dataset_filtered', filename), 'rU')
            first = fdclean.readline()
            self.assertEqual(len(first.split()), 1)
            fdclean.close()
        shutil.rmtree('unittest_dataset_filtered')

    def test_dir_nolimit_kt(self):
        """
        Test the module's entry function with a directory keeping the timestamps,
        no apply_limits used.
        All files that existed originaly must still exist, and
        the resultig file should have exactly two columns.
    """
        if not os.path.exists('unittest_dataset_filtered'):
            os.mkdir('unittest_dataset_filtered')
        tools.filter.ds_filter('unittest_dataset', 'unittest_dataset_filtered', keep_time=True)
        self.assertEqual(os.listdir('unittest_dataset'), os.listdir('unittest_dataset_filtered'))
        for filename in os.listdir('unittest_dataset'):
            fdclean = open(os.path.join('unittest_dataset_filtered', filename), 'rU')
            first = fdclean.readline()
            self.assertEqual(len(first.split()), 2)
            fdclean.close()
        shutil.rmtree('unittest_dataset_filtered')

    def test_dir_limit_nokt(self):
        """
        Test the module's entry function with a directory timestamps are ignored,
        this test uses a particular 'planted' file with two out of bound values
        (one above one below).

        All files must exist, and the 'planted' file must have exactly two lines
        lesser than the original file.
    """
        if not os.path.exists('unittest_dataset_filtered'):
            os.mkdir('unittest_dataset_filtered')
        tools.filter.ds_filter('unittest_dataset', 'unittest_dataset_filtered', False, apply_limits=True)
        self.assertEqual(os.listdir('unittest_dataset'), os.listdir('unittest_dataset_filtered'))
        fdorig = open('unittest_dataset/adulterado.txt')
        fdclean = open('unittest_dataset_filtered/adulterado.txt')
        self.assertEqual(len(fdorig.readlines()) - 2, len(fdclean.readlines()))
        fdorig.close()
        fdclean.close()
        shutil.rmtree('unittest_dataset_filtered')


if __name__ == '__main__':
    unittest.main(exit=False)
