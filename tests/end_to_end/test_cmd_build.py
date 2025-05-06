"""
Test that the command appabuild lca build works correctly with a simple example.
"""

import os
import subprocess

import yaml

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def test_build_command():
    appaconf_file = os.path.join(DATA_DIR, "appalca_conf.yaml")
    conf_file = os.path.join(DATA_DIR, "nvidia_ai_gpu_chip_lca_conf.yaml")
    expected_file = os.path.join(DATA_DIR, "nvidia_ai_gpu_chip_expected.yaml")

    result = subprocess.run(
        [
            "python",
            "-m" "appabuild.cli.main",
            "lca",
            "build",
            appaconf_file,
            conf_file,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    # Check the generated impact model is the same as expected
    with open(expected_file, "r") as stream:
        f1_yaml = yaml.safe_load(stream)

    with open("nvidia_ai_gpu_chip.yaml", "r") as stream:
        f2_yaml = yaml.safe_load(stream)

    os.remove("nvidia_ai_gpu_chip.yaml")

    assert f1_yaml == f2_yaml
