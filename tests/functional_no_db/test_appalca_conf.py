import os

import pytest
import yaml
from pydantic import ValidationError

from appabuild import setup
from appabuild.config.appa_lca import AppaLCAConfig
from tests import DATA_DIR


def test_missing_foreground():
    """
    Check an exception is raised when the field foreground is missing.
    """
    path = os.path.join(
        DATA_DIR, "appalca_confs", "invalids", "missing_foreground.yaml"
    )

    invalid_params_loc = [("databases",)]

    try:
        AppaLCAConfig.from_yaml(path)
        pytest.fail(
            "An AppaLCA config file is not valid when the field foreground is missing"
        )
    except ValidationError as e:
        for error in e.errors():
            assert error["type"] == "key_error"
            assert error["loc"] in invalid_params_loc
            assert error["ctx"]["field"] == "foreground"
            invalid_params_loc.remove(error["loc"])

    assert len(invalid_params_loc) == 0


def test_missing_foreground_path():
    """
    Check an exception is raised when the field foreground has no sub-field path.
    """
    path = os.path.join(
        DATA_DIR, "appalca_confs", "invalids", "missing_foreground_path.yaml"
    )

    invalid_params_loc = [("databases", "foreground", "path")]

    try:
        AppaLCAConfig.from_yaml(path)
        pytest.fail(
            "An AppaLCA config file is not valid when the field foreground is missing its path sub-field"
        )
    except ValidationError as e:
        error = e.errors()[0]
        assert error["type"] == "missing"
        assert error["loc"] in invalid_params_loc
        invalid_params_loc.remove(error["loc"])

    assert len(invalid_params_loc) == 0


def test_not_existing_foreground_path():
    """
    Check an exception is raised when the path for the foreground datasets doesn't exist.
    """
    path = os.path.join(
        DATA_DIR, "appalca_confs", "invalids", "not_existing_foreground_path.yaml"
    )

    invalids_params_loc = [
        ("databases", "foreground", "path"),
    ]

    try:
        AppaLCAConfig.from_yaml(path)
        pytest.fail("The path of foreground doesn't exist")
    except ValidationError as e:
        for error in e.errors():
            assert error["type"] == "value_error"
            assert error["loc"] in invalids_params_loc
            invalids_params_loc.remove(error["loc"])

    assert len(invalids_params_loc) == 0


def test_valid_conf():
    """
    Check no exception is raised for a valid Appa LCA configuration.
    """
    path = os.path.join(DATA_DIR, "appalca_confs", "valids", "valid.yaml")

    try:
        AppaLCAConfig.from_yaml(path)
    except ValidationError:
        pytest.fail("A valid AppaLCA config should not raise any exception")


def test_valid__without_ecoinvent_conf():
    """
    Check no exception is raised for a valid Appa LCA configuration with no ecoinvent field.
    """
    path = os.path.join(
        DATA_DIR, "appalca_confs", "valids", "valid_without_ecoinvent.yaml"
    )

    try:
        AppaLCAConfig.from_yaml(path)
    except ValidationError:
        pytest.fail("A valid AppaLCA config should not raise any exception")
