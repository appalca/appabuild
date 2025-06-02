"""
Tests for eco invent validity
"""
import os

import pytest

from appabuild.database.databases import EcoInventDatabase
from appabuild.exceptions import BwDatabaseError
from tests import DATA_DIR


def test_not_existing_path():
    """
    Check an exception is raised when the path for the eco invent datasets doesn't exist.
    """
    path = os.path.join(DATA_DIR, "imaginary_path")

    try:
        db = EcoInventDatabase(path=path, name="name")
        db.execute_at_startup()
        pytest.fail("An eco invent database can't be loaded from an non-existing path")
    except BwDatabaseError as e:
        assert e.exception_type == "eco_invent_invalid_path"


def test_empty_dataset():
    """
    Check an exception is raised when there is no dataset to load.
    """
    path = os.path.join(DATA_DIR, "eco_invent", "invalids", "no_datasets")

    try:
        db = EcoInventDatabase(path=path, name="name")
        db.execute_at_startup()
        pytest.fail("An eco invent database can't be loaded if there is no datasets")
    except BwDatabaseError as e:
        assert e.exception_type == "eco_invent_invalid_path"


def test_invalid_dataset():
    """
    Check an exception is raised when one of the dataset is invalid.
    """
    path = os.path.join(DATA_DIR, "eco_invent", "invalids", "invalid_datasets")

    try:
        db = EcoInventDatabase(path=path, name="name")
        db.execute_at_startup()
        pytest.fail(
            "An eco invent database can't be loaded if at least one dataset is invalid"
        )
    except BwDatabaseError as e:
        assert e.exception_type == "eco_invent_invalid_dataset"


def test_incomplete_dataset():
    """
    Check an exception is raised when one of the dataset is incomplete.
    """
    path = os.path.join(DATA_DIR, "eco_invent", "invalids", "incomplete_datasets")

    try:
        db = EcoInventDatabase(path=path, name="name")
        db.execute_at_startup()
        pytest.fail(
            "An eco invent database can't be loaded if at least one dataset is incomplete"
        )
    except BwDatabaseError as e:
        assert e.exception_type == "eco_invent_invalid_dataset"
