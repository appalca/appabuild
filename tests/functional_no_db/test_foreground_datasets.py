"""
Tests that an error is raised only when required fields are missing in a foreground dataset file.
"""

import os
from copy import deepcopy

import pytest
import yaml
from pydantic import ValidationError

from appabuild.database.databases import ForegroundDatabase
from tests import DATA_DIR


def test_dataset_missing_fields():
    """
    Check an exception is raised for a set of foreground datasets
    with at least one dataset with missing required fields.
    """
    datasets_path = os.path.join(
        DATA_DIR, "foreground_datasets", "invalids", "missing_fields"
    )

    invalid_params_loc = [
        ("name",),
        ("unit",),
        ("exchanges", 0, "name"),
        ("exchanges", 1, "database"),
    ]

    try:
        db = ForegroundDatabase(name="", path=datasets_path)
        db.execute_at_startup()
        pytest.fail(
            "The dataset nvidia_ai_gpu_chip is invalid so foreground database initialization must fail"
        )
    except ValidationError as e:
        for error in e.errors():
            assert error["type"] == "missing"
            assert error["loc"] in invalid_params_loc
            invalid_params_loc.remove(error["loc"])
    assert len(invalid_params_loc) == 0


def test_dataset_with_no_missing():
    """
    Check no exception is raised for a valid set of foreground datasets.
    """
    datasets_path = os.path.join(DATA_DIR, "foreground_datasets", "valids")

    try:
        db = ForegroundDatabase(name="", path=datasets_path)
        db.execute_at_startup()
    except SystemExit:
        pytest.fail("A valid set of foreground datasets must raise no exception")


def test_dataset_parameter_name_reserved():
    """
    Check an exception is raised when one of the parameter has a reserved name.
    """
    datasets_path = os.path.join(
        DATA_DIR, "foreground_datasets", "invalids", "reserved_names"
    )

    invalid_params_loc = [
        ("parameters",),
    ]

    try:
        db = ForegroundDatabase(name="", path=datasets_path)
        db.execute_at_startup()
        pytest.fail(
            "The dataset nvidia_ai_gpu_chip is invalid so foreground database initialization must fail"
        )
    except ValidationError as e:
        for error in e.errors():
            assert error["type"] == "reserved_name"
            assert error["loc"] in invalid_params_loc
            invalid_params_loc.remove(error["loc"])

    assert len(invalid_params_loc) == 0
