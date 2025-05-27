"""
This module contains the end-to-end tests for the command graph.
"""

import os
import random

from typer.testing import CliRunner

from appabuild.cli.main import cli_app
from tests import DATA_DIR

runner = CliRunner()


def test_non_existing_path():
    """
    Check that the application exits with the exit code 1 when
    the path of the foreground datasets doesn't exist.
    """
    result = runner.invoke(
        cli_app,
        [
            "lca",
            "graph",
            "non_existing_root_path/",
            "nvidia_ai_gpu_chip",
            "--no-sensitive",
        ],
    )
    assert result.exit_code == 1


def test_no_datasets():
    """
    Check that the application exits with the exit code 1 when
    there is no foreground datasets to load.
    """
    result = runner.invoke(
        cli_app, ["lca", "graph", DATA_DIR, "nvidia_ai_gpu_chip", "--no-sensitive"]
    )
    assert result.exit_code == 1


def test_fu_not_found():
    """
    Check that the application exits with the exit code 1 when
    the functional unit used for the graph can't be found.
    """
    result = runner.invoke(
        cli_app, ["lca", "graph", DATA_DIR, "amd_ai_gpu_chip", "--no-sensitive"]
    )
    assert result.exit_code == 1


def test_invalid_type():
    """
    Check that the application exits with the exit code 2 when
    the option type has an invalid value.
    """
    result = runner.invoke(
        cli_app,
        [
            "lca",
            "graph",
            DATA_DIR,
            "nvidia_ai_gpu_chip",
            "--type",
            "jpeg",
            "--no-sensitive",
        ],
    )
    assert result.exit_code == 2


def test_invalid_height():
    """
    Check that the application exits with the exit code 2 when
    the option height has an invalid value.
    """
    height = random.randint(0, 100) * -1
    result = runner.invoke(
        cli_app,
        [
            "lca",
            "graph",
            DATA_DIR,
            "nvidia_ai_gpu_chip",
            "--height",
            str(height),
            "--no-sensitive",
        ],
    )
    assert result.exit_code == 2


def test_invalid_width():
    """
    Check that the application exits with the exit code 2 when
    the option width has an invalid value.
    """
    width = random.randint(0, 100) * -1
    result = runner.invoke(
        cli_app,
        [
            "lca",
            "graph",
            DATA_DIR,
            "nvidia_ai_gpu_chip",
            "--width",
            str(width),
            "--no-sensitive",
        ],
    )
    assert result.exit_code == 2


def test_sensitive_option():
    """
    Check that no graph is created when
    the input is no for the sensitive option.
    """
    height = random.randint(1, 100)
    width = random.randint(1, 100)
    result = runner.invoke(
        cli_app,
        [
            "lca",
            "graph",
            DATA_DIR,
            "nvidia_ai_gpu_chip",
            "--type",
            "png",
            "--height",
            str(height),
            "--width",
            str(width),
        ],
        input="n\n",
    )
    assert not os.path.exists("./nvidia_ai_gpu_chip.png")
    assert result.exit_code == 0
