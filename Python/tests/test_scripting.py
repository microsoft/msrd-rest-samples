from __future__ import print_function
from sampleclient import log, set_logging_debug
from sampleclient.scripting import is_linux

import unittest


class ScriptingTestSuite(unittest.TestCase):

    """Basic test cases."""
    def test_scripting_islinux(self):
        set_logging_debug(log)

        redhat = {
            "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "osArchitecture": "x64",
            "osBuild": "7.2",
            "osEdition": "Redhat",
            "osRevision": "7.2",
            "osType": "Linux",
            "osBranch": "",
            "icon": "icons/Redhat.png"
        }

        windows_server_2k8 = {
            "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "osArchitecture": "x64",
            "osBuild": "7601",
            "osEdition": "Server 2008 R2",
            "osRevision": "150928-1507",
            "osType": "Windows",
            "osBranch": "",
            "icon": "icons/Windows.png"
        }

        windows_server_datacenter = {
            "id": "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "osArchitecture": "x64",
            "osBuild": "7602",
            "osEdition": "Server 2016 Datacenter",
            "osRevision": "150928-9999",
            "osType": "Windows",
            "osBranch": "",
            "icon": "icons/Windows.png"
        }

        assert is_linux(log, redhat)
        assert not is_linux(log, windows_server_2k8)
        assert not is_linux(log, windows_server_datacenter)

if __name__ == '__main__':

    unittest.main()
