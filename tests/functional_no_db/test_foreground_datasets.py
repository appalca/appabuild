"""
Tests that an error is raised only when required fields are missing in a foreground dataset file.
"""

import os
from copy import deepcopy

import pytest
import yaml

from appabuild import setup

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@pytest.fixture()
def setup_conf(request):
    appaconf_file = os.path.join(DATA_DIR, request.param["conf_filename"])

    with open(appaconf_file, "r") as file:
        appaconf = yaml.safe_load(file)

    appaconf_copy = deepcopy(appaconf)
    appaconf["databases"]["foreground"]["path"] = os.path.join(
        DATA_DIR, "{}".format(request.param["folder"])
    )

    with open(appaconf_file, "w") as file:
        yaml.safe_dump(appaconf, file)

    yield

    with open(appaconf_file, "w") as file:
        yaml.safe_dump(appaconf_copy, file)


@pytest.mark.parametrize(
    "setup_conf",
    [{"conf_filename": "valid_appalca_conf.yaml", "folder": "valid_datasets"}],
    indirect=True,
)
def test_dataset_with_no_missing(setup_conf):
    filename = "nvidia_ai_gpu_chip_lca_conf.yaml"
    appaconf_file = os.path.join(DATA_DIR, "valid_appalca_conf.yaml")

    try:
        setup.initialize(appaconf_file)
    except SystemExit:
        pytest.fail(
            "The file {} is valid so foreground database initialization must not fail".format(
                filename
            )
        )


@pytest.mark.parametrize(
    "setup_conf",
    [{"conf_filename": "invalid_appalca_conf.yaml", "folder": "invalid_datasets"}],
    indirect=True,
)
def test_dataset_with_missing(setup_conf):
    filename = "nvidia_ai_gpu_chip_lca_conf.yaml"
    appaconf_file = os.path.join(DATA_DIR, "invalid_appalca_conf.yaml")

    try:
        setup.initialize(appaconf_file)
        pytest.fail(
            "The file {} is invalid so foreground database initialization must fail".format(
                filename
            )
        )
    except SystemExit as system_exit:
        assert system_exit.code == 1
