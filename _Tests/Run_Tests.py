import unittest
import os

# Test without overage
if __name__ == "__main__":
    test_dir = os.path.abspath('.')
    # create TestLoader
    test_loader = unittest.TestLoader()
    # collect all testfiles
    test_suite = test_loader.discover(test_dir, pattern='Test_*.py')
    # create testrunner
    test_runner = unittest.TextTestRunner()
    # run all tests
    test_runner.run(test_suite)
