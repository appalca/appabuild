"""
Module containing all the classes and methods to load and validate LCA configurations.
"""

from __future__ import annotations

from typing import Annotated, Any, List, Optional

import yaml
from apparun.impact_model import ModelMetadata
from apparun.parameters import ImpactModelParam
from pydantic import BaseModel, BeforeValidator, ValidationError
from pydantic_core import PydanticCustomError

from appabuild.logger import log_validation_error, logger


def parse_param(param: dict) -> ImpactModelParam:
    """
    Create an ImpactModelParam from a dict.
    This dict must contain the key type, if not a PydanticCustomError of type key_error is raised.

    :param param: dict containing the elements needed to build an ImpactModelParam.
    :return: constructed ImpactModelParam.
    """
    try:
        return ImpactModelParam.from_dict(param)
    except KeyError:
        raise PydanticCustomError(
            "key_error", "Missing field type for a parameter", {"field": "type"}
        )


class Model(BaseModel):
    """
    Contain information about an impact model, like its metadata, the name of the output file
    or the free parameters needed by the functional unit used in the impact model.

    Attributes:
        name: name of the yaml file corresponding to the impact model (do not include file extension).
        path: output folder for saving impact model.
        compile: if True, precompute the symbolic expressions needed by Appa Run and store them in the impact model.
        metadata: information about the impact model, meant to help the user of it to better understand the LCA leading to the impact model.
        parameters: information about all free parameters needed by the functional unit of the impact model.
    """

    name: str
    path: Optional[str] = "."
    compile: bool
    metadata: Optional[ModelMetadata] = None
    parameters: Optional[
        List[Annotated[ImpactModelParam, BeforeValidator(parse_param)]]
    ] = []

    def dump_parameters(self) -> List[dict]:
        return list(map(lambda p: p.model_dump(), self.parameters))


class FunctionalUnit(BaseModel):
    """
    Information about the functional unit corresponding to the activity that produces the reference flow.
    The functional unit should be stored in the foreground database.

    Attributes:
        name: name of the functional unit to use, make sure that the name is unique.
        database: name of the database (defined in the Appa LCA configuration) the functional unit will be loaded from.
    """

    name: str
    database: str


class Scope(BaseModel):
    """
    Scope of an LCA of the corresponding impact model, define the main characteristics of it.

    Attributes:
        fu: functional unit used in this scope.
        methods: LCIA methods to cover. Appa LCA uses a mapping between short keys and full LCIA method names as available in Brightway.
    """

    fu: FunctionalUnit
    methods: List[str]


class LCAConfig(BaseModel):
    """
    An LCA configuration, contains information about the LCA and its corresponding impact model.
    One LCA configuration is needed per LCA performed.

    Attributes:
        scope: the scope of the LCA.
        model: information about the corresponding impact model.
    """

    scope: Scope
    model: Model

    @staticmethod
    def from_yaml(lca_conf_path: str) -> LCAConfig:
        """
        Load an LCA config from its yaml file.
        If the config is invalid, raise a ValidationError.
        """
        logger.info("Loading LCA config from the path {}".format(lca_conf_path))

        with open(lca_conf_path, "r") as file:
            raw_yaml = yaml.safe_load(file)

        try:
            config = LCAConfig(**raw_yaml)
        except ValidationError as e:
            log_validation_error(e)
            raise e

        logger.info("LCA config successfully loaded")
        return config
