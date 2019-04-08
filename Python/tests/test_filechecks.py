from __future__ import print_function
from sampleclient import log, set_logging_debug
from sampleclient.filechecks import file_exists, file_size_in_bytes, files_must_not_be_more_than

import unittest

set_logging_debug(log)


class FileChecksTestSuite(unittest.TestCase):

    def test_file_exists(self):
        assert file_exists
        assert not file_exists(__file__ + "foo")

    def test_file_size_in_bytes(self):
        assert file_size_in_bytes
        assert file_size_in_bytes(__file__) > 0

    def test_files_must_not_be_more_than(self):
        assert files_must_not_be_more_than

        bytes_over_limit, error_happened = files_must_not_be_more_than([__file__], 1024 * 1024 * 10)
        assert not bytes_over_limit
        assert not error_happened

        bytes_over_limit, error_happened = files_must_not_be_more_than([__file__], limit=1)
        assert bytes_over_limit > 1, bytes_over_limit
        assert error_happened

if __name__ == '__main__':

    unittest.main()
