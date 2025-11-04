"""
Tests for eco invent validity
"""
import os

import pytest
from requests import HTTPError

from appabuild.database.databases import EcoInventDatabase


def test_no_ecoinvent_version():
    """
    Check an exception is raised when no ecoinvent version is provided.
    """
    os.environ["BW_USER"] = "test"
    os.environ["BW_PASS"] = "test"
    try:
        db = EcoInventDatabase(system_model="cutoff")
        db.execute_at_startup()
        pytest.fail("EcoInvent database requires a version")
    except TypeError as e:
        assert (
            str(e)
            == "EcoInventDatabase.__init__() missing 1 required positional argument: 'version'"
        )


def test_no_ecoinvent_system_model():
    """
    Check an exception is raised when no ecoinvent version is provided.
    """
    os.environ["BW_USER"] = "test"
    os.environ["BW_PASS"] = "test"
    try:
        db = EcoInventDatabase(version="3.11")
        db.execute_at_startup()
        pytest.fail("EcoInvent database requires a system model")
    except TypeError as e:
        assert (
            str(e)
            == "EcoInventDatabase.__init__() missing 1 required positional argument: 'system_model'"
        )


def test_no_ecoinvent_credentials():
    """
    Check an exception is raised when no ecoinvent version is provided.
    """
    try:
        db = EcoInventDatabase(version="3.11", system_model="cutoff")
        db.execute_at_startup()
        pytest.fail("EcoInvent database requires credentials as environment variables")
    except HTTPError as e:
        assert e.response.reason == "Unauthorized"
