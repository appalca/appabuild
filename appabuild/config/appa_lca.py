"""
Module containing all the classes and methods to load and validate Appa LCA configurations.
"""

from __future__ import annotations

import os
from typing import Dict

import yaml
from pydantic import BaseModel, ValidationError, field_validator
from pydantic_core import PydanticCustomError

from appabuild.logger import log_validation_error, logger


class DatabaseConfig(BaseModel):
    """
    Database entry in an Appa LCA configuration.

    Attributes:
        name: name of the database.
        path: root path of the database elements.
    """

    name: str
    path: str

    @field_validator("path", mode="after")
    @classmethod
    def path_exists(cls, path: str):
        if not os.path.exists(path):
            raise PydanticCustomError("value_error", "Invalid path " + path)
        return path


class AppaLCAConfig(BaseModel):
    """
    An Appa LCA configuration, contains information used to set up a Brightway's
    environment and specify the paths of the background and foreground databases.

    Attributes:
        project_name: name used by Brightway to initialize the environment.
        databases: databases to import, only one foreground database is required and ecoinvent database is optional.
    """

    project_name: str
    databases: Dict[str, DatabaseConfig]

    @field_validator("databases", mode="before")
    @classmethod
    def validate_databases(cls, databases):
        """
        Check that the foreground database is in the databases to import,
        if not raise a PydanticCustomError of type key_error.
        """
        if "foreground" not in databases:
            raise PydanticCustomError(
                "key_error", "Missing field foreground", {"field": "foreground"}
            )
        return databases

    @staticmethod
    def from_yaml(appa_lca_conf_path: str) -> AppaLCAConfig:
        """
        Load an Appa LCA configuration from its yaml file.
        If the configuration is invalid, raise a ValidationError.
        """
        logger.info(
            "Loading Appa LCA configuration from the path %s", appa_lca_conf_path
        )

        with open(appa_lca_conf_path, "r") as file:
            raw_yaml = yaml.safe_load(file)

        try:
            config = AppaLCAConfig(**raw_yaml)
        except ValidationError as e:
            log_validation_error(e)
            raise e

        logger.info("Appa LCA configuration successfully loaded")
        return config
