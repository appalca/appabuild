"""
Test that the command appabuild lca build works correctly with a simple example.
"""

import os

import yaml
from typer.testing import CliRunner

from appabuild.cli.main import cli_app
from tests import DATA_DIR

runner = CliRunner()


def test_build_command():
    appaconf_file = os.path.join(DATA_DIR, "cmd_build", "appalca_conf.yaml")
    conf_file = os.path.join(DATA_DIR, "cmd_build", "nvidia_ai_gpu_chip_lca_conf.yaml")
    expected_file = os.path.join(
        DATA_DIR, "cmd_build", "nvidia_ai_gpu_chip_expected.yaml"
    )

    result = runner.invoke(
        cli_app,
        [
            "lca",
            "build",
            appaconf_file,
            conf_file,
        ],
    )

    assert result.exit_code == 0

    # Check the generated impact model is the same as expected
    with open(expected_file, "r") as stream:
        expected = yaml.safe_load(stream)

    with open("nvidia_ai_gpu_chip.yaml", "r") as stream:
        value = yaml.safe_load(stream)

    os.remove("nvidia_ai_gpu_chip.yaml")

    assert expected == value, "result file not the same as expected file "
