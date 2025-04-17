"""
This test ensure that appabuild --help works
"""

import subprocess


def test_help_command():
    result = subprocess.run(
        ["python", "-m", "appabuild.cli.main", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
