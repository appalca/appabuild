"""
This test ensure that appabuild --help works
"""

import subprocess


def test_help_command():
    result = subprocess.run(["appabuild", "--help"], capture_output=True, text=True)
    assert result.returncode == 0
