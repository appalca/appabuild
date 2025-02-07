"""
Test that the command appabuild lca build works correctly with a simple example.
"""

import os
import subprocess


def compare_files_line_by_line(file1, file2):
    with (
        open(file1, "r") as expected_file,
        open(file2, "r") as result_file,
    ):
        for line1, line2 in zip(expected_file, result_file):
            if line1 != line2:
                return False
    return True


def test_build_command():
    appaconf_file = "test_build/appalca_conf.yaml"
    conf_file = "test_build/nvidia_ai_gpu_chip_lca_conf.yaml"
    expected_file = "test_build/nvidia_ai_gpu_chip_lca_conf.yaml"

    result = subprocess.run(
        [
            "appabuild",
            "lca",
            "build",
            appaconf_file,
            conf_file,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    result = compare_files_line_by_line(expected_file, "nvidia_ai_gpu_chip.yaml")

    os.remove("nvidia_ai_gpu_chip.yaml")

    assert result is True
