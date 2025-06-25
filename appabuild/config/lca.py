"""
Module containing all the classes and methods to load and validate LCA configurations.
"""

from __future__ import annotations

from typing import List, Optional

import yaml
from apparun.expressions import ParamsValuesSet
from apparun.impact_model import ModelMetadata
from apparun.parameters import ImpactModelParam, ImpactModelParams
from pydantic import BaseModel, ValidationError, field_validator
from pydantic_core import PydanticCustomError

from appabuild.logger import log_validation_error, logger


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
    parameters: Optional[List[ImpactModelParam]] = []

    @field_validator("parameters", mode="before")
    @classmethod
    def parse_parameters(cls, parameters: List[dict]) -> List[ImpactModelParam]:
        parsed_parameters = []

        if parameters:
            errors = []
            for idx, parameter in enumerate(parameters):
                if "type" not in parameter:
                    errors.append(
                        {
                            "loc": (idx, "type"),
                            "msg": "",
                            "type": PydanticCustomError(
                                "missing",
                                "Missing field {field} for a parameter",
                                {"field": "type"},
                            ),
                            "input": parameter,
                        }
                    )
                    continue
                elif "default" not in parameter:
                    errors.append(
                        {
                            "loc": (idx, "default"),
                            "msg": "",
                            "type": PydanticCustomError(
                                "missing",
                                "Missing field {field} for a parameter",
                                {"field": "default"},
                            ),
                            "input": parameter,
                        }
                    )
                    continue

                if (
                    parameter["type"] == "enum"
                    and isinstance(parameter["default"], str)
                    or parameter["type"] == "float"
                    and isinstance(parameter["default"], (float, int))
                ):
                    default = parameter["default"]
                else:
                    default = parameter["default"]
                    parameter.pop("default")

                try:
                    parsed_param = ImpactModelParam.from_dict(parameter)
                    parsed_param.default = default
                    parsed_parameters.append(parsed_param)
                except ValidationError as e:
                    for err in e.errors():
                        loc = list(err["loc"])
                        loc.insert(-2, idx)
                        err["loc"] = tuple(loc)
                        errors.append(err)

            if errors:
                raise ValidationError.from_exception_data("", line_errors=errors)

        return parsed_parameters

    @field_validator("parameters", mode="after")
    @classmethod
    def eval_exprs(cls, parameters: List[ImpactModelParam]) -> List[ImpactModelParam]:
        exprs_set = ParamsValuesSet.build(
            {param.name: param.default for param in parameters},
            ImpactModelParams.from_list(parameters),
        )

        values = exprs_set.evaluate()
        for param in parameters:
            param.update_default(values[param.name])

        return parameters

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
