"""
This test ensure that appabuild --help works
"""

from typer.testing import CliRunner

from appabuild.cli.main import cli_app

runner = CliRunner()


def test_help():
    result = runner.invoke(cli_app, ["--help"])
    assert result.exit_code == 0


def test_build_help():
    result = runner.invoke(cli_app, ["lca", "build", "--help"])
    assert result.exit_code == 0


def test_validate_foreground_datasets_help():
    result = runner.invoke(cli_app, ["lca", "validate-foreground-datasets", "--help"])
    assert result.exit_code == 0
