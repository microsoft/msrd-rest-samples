from __future__ import print_function
from sampleclient import log, set_logging_debug, parse_args

import unittest


class CommandsTestSuite(unittest.TestCase):

    """Basic test cases."""
    def test_commands(self):
        assert log
        set_logging_debug(log)
        assert parse_args and callable(parse_args)


if __name__ == '__main__':

    unittest.main()
