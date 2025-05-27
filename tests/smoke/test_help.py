"""
This test ensure that appabuild --help works
"""

import subprocess

from typer.testing import CliRunner

from appabuild.cli.main import cli_app

runner = CliRunner()


def test_help_command():
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0
