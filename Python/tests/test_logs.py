from __future__ import print_function
from sampleclient import log, set_logging_debug

import unittest


class LogsTestSuite(unittest.TestCase):

    """Basic test cases."""
    def test_log(self):
        assert log
        assert log.level
        set_logging_debug(log)
        assert log.level == 10, log.level

if __name__ == '__main__':

    unittest.main()
