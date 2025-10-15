"""
Module containing all the tests for the LCA config validation.
"""
import os

import pytest
from pydantic import ValidationError

from appabuild import setup
from appabuild.cli.lca import build
from appabuild.config.lca import LCAConfig
from appabuild.exceptions import ParameterError
from tests import DATA_DIR


def test_missing_required_fields():
    """
    Check an exception is raised when at least one required field is missing.
    """
    path = os.path.join(
        DATA_DIR, "lca_confs", "invalids", "missing_required_fields.yaml"
    )

    missing_fields_locs = [
        ("scope", "fu", "name"),
        ("model", "parameters", 1, "default"),
        ("model", "parameters", 2, "weights"),
        ("model", "parameters", 3, "type"),
    ]

    try:
        LCAConfig.from_yaml(path)
        pytest.fail("An LCA config with missing fields is not a valid config")
    except ValidationError as e:
        for error in e.errors():
            assert error["type"] == "missing"
            if error["type"] == "missing":
                assert error["loc"] in missing_fields_locs
                missing_fields_locs.remove(error["loc"])
    assert len(missing_fields_locs) == 0


def test_parameter_empty_name():
    """
    Check an exception is raised when a parameter has an empty name.
    """
    path = os.path.join(DATA_DIR, "lca_confs", "invalids", "parameter_empty_name.yaml")

    invalid_params_loc = [
        ("model", "parameters", 0, "name"),
        ("model", "parameters", 3, "name"),
    ]

    try:
        LCAConfig.from_yaml(path)
        pytest.fail("A parameter can't have an empty name")
    except ValidationError as e:
        for error in e.errors():
            assert error["type"] == "string_type"
            assert error["loc"] in invalid_params_loc


def test_parameter_missing_in_conf():
    """
    Check that an exception is raised if a parameter is missing in the LCA conf.
    """
    appa_conf_file = os.path.join(
        DATA_DIR, "appalca_confs", "valids", "appalca_conf_lca_confs.yaml"
    )
    lca_conf_file = os.path.join(
        DATA_DIR, "lca_confs", "invalids", "parameter_missing_in_conf.yaml"
    )

    foreground_database = setup.initialize(appa_conf_file)
    with pytest.raises(ParameterError):
        setup.build(lca_conf_file, foreground_database)
        os.remove("ai_use_phase.yaml")


def test_parameter_in_default_missing_in_conf():
    """
    Check that an exception is raised if a parameter is missing in the LCA conf.
    """
    appa_conf_file = os.path.join(
        DATA_DIR, "appalca_confs", "valids", "appalca_conf_lca_confs.yaml"
    )
    lca_conf_file = os.path.join(
        DATA_DIR, "lca_confs", "invalids", "parameter_in_default_missing_in_conf.yaml"
    )

    foreground_database = setup.initialize(appa_conf_file)
    with pytest.raises(ParameterError):
        setup.build(lca_conf_file, foreground_database)
        os.remove("ai_use_phase.yaml")


def test_valid():
    """
    Check no exception is raised for a valid LCA configuration.
    """
    path = os.path.join(
        DATA_DIR, "lca_confs", "valids", "nvidia_ai_gpu_chip_lca_conf.yaml"
    )

    try:
        LCAConfig.from_yaml(path)
    except ValidationError:
        pytest.fail("A valid LCA configuration must not raise any error")


def test_valid_parameters_field_empty():
    """
    Check no exception is raised when the field parameters is empty.
    """
    path = os.path.join(DATA_DIR, "lca_confs", "valids", "parameters_field_empty.yaml")

    try:
        LCAConfig.from_yaml(path)
    except ValidationError:
        pytest.fail("The field parameters can be empty")
