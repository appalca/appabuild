"""
This module contains classes to make the interface between serialized data (such as
json and yaml).
Main purposes of those classes are to check serialized data schema and realize
operations on those fields.
Classes of this module are not environment-aware, i.e. they have no information about
LCA context (background databases, functional unit, LCA parameters...).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Union

import numpy
from pydantic import BaseModel, field_validator
from pydantic_core import PydanticCustomError
from ruamel.yaml import YAML

yaml = YAML()


class ActivityIdentifier(BaseModel):
    """
    Contain a set of characteristics to identify an activity. An ActivityIdentifier is
    considered as unresolved is uuid is not defined.
    An unresolved ActivityIdentifier can be defined by its name and location.
    """

    database: str
    uuid: Optional[str] = None
    name: Optional[str] = None
    location: Optional[str] = None

    @property
    def is_unresolved(self) -> bool:
        """
        An ActivityIdentifier is considered as unresolved is uuid is not defined.
        :return: True if object is unresolved.
        """
        return self.uuid is None

    @property
    def code(self) -> str:
        """
        Brightway refers to uuid as 'code'. This property helps to harmonize with
        Activity class's code attribute.
        :return: object's uuid
        """
        return self.uuid

    def to_dict(self):
        """
        Convert self to dict.
        :return: self as a dict
        """
        activity_identifier_as_dict = {
            k: v for k, v in dict(self).items() if v is not None
        }
        return activity_identifier_as_dict


class SerializedActivity(BaseModel):
    """
    SerializedActivity is the easiest way to import user datasets, as Activity
    class can use SerializedActivity objects to create Brightway compatible datasets.
    """

    uuid: str
    "Must be unique in the user database."
    database: str
    "Name of the user database."
    name: str
    """Name of the activity. Should be unique if include_in_tree is True, else, a
    suffix will be generated."""
    type: Optional[str] = None
    "According to Brightway, can be production, technosphere, or biosphere."
    exchanges: List[SerializedExchange]
    "Emissions or consumptions generated when a unit of the activity is used."
    location: Optional[str] = "GLO"
    "Location of the activity. Default value is GLO for global."  # TODO comment c'est utilisé ?
    amount: Optional[float] = 1
    "Amount of output flow generated for given amount of exchanges."  # TODO comment c'est utilisé ?
    unit: str
    "Unit of the amount."
    parameters: Optional[List[str]] = []
    "Optional list of parameters necessary to execute this dataset."
    data_quality: Optional[Dict[str, int]] = None
    "Deprecated."
    comment: Optional[str] = None
    "Free text for any context information about the dataset."
    include_in_tree: Optional[bool] = False
    "If True, activity will become a node in built ImpactModel."
    properties: Optional[Dict[str, Union[str, float, bool]]] = {}
    """Properties will remain on impact model, and can be used by apparun to breakdown
    the results according to life cycle phase, for exemple. Properties can be key/value
    (ex: {"phase": "production"} or flags (ex: {production_phase: True})."""

    @property
    def code(self):
        """
        Brightway refers to uuid as 'code'. This property helps to harmonize with
        Activity class's code attribute.
        :return: object's uuid
        """
        return self.uuid

    def to_dict(self):
        """
        Convert self to dict.
        :return: self as a dict
        """
        exchanges = [exchange.to_dict() for exchange in self.exchanges]
        activity_as_dict = {k: v for k, v in dict(self).items() if v is not None}
        activity_as_dict["exchanges"] = exchanges
        return activity_as_dict

    def to_yaml(self, filepath: str, keep_uuid=False):
        """
        Convert self to yaml file.
        :param filepath: filepath of the yaml file to create.
        :param keep_uuid: specify if uuid has to be included in the yaml
        """
        with open(filepath, "w") as stream:
            as_a_dict = self.to_dict()
            if not keep_uuid:
                as_a_dict.pop("uuid")
            yaml.dump(as_a_dict, stream)

    @field_validator("parameters", mode="after")
    @classmethod
    def check_name(cls, parameters: List[str]) -> List[str]:
        for param in parameters:
            if param in dir(math) or param in dir(numpy):
                raise PydanticCustomError("reserved_name", "", {"name": param})
        return parameters


class SerializedExchange(BaseModel):
    """
    SerializedExchange is the easiest way to import user datasets, as Exchange
    class can use SerializedExchange objects to create Brightway compatible datasets.
    Exchange are connection between an input and an output dataset. Contrarily to
    Brightway, the later is not explicitly indicated and will always be affected to
    the calling Activity.
    """

    database: str
    "Name of the user database."
    name: str
    "Name of the exchange. Can be used to dynamically name ImpactModel node."
    type: Optional[str] = None
    # TODO à virer, non ?
    amount: Optional[Union[float, str]] = None
    """Quantity of input required to generate the output. Can be a fixed quantity or a
    formula."""
    input: Optional[ActivityIdentifier] = None
    "Identifier of the downstream Activity."
    parameters_matching: Optional[Dict[str, Union[float, str, Dict[str, int]]]] = {}
    """
    Name or values of input's parameters can be dynamically changed. Key is the name of
    the input parameter's name to change, and value the replacing variable. A float will
    set the parameter to a fixed value, str will update parameter's name or affect it to
    a formula, and dict is used to fix value of a categorical parameter.
    """
    use_exchange_name: Optional[bool] = False
    """Replace input's name by exchange's name. Useful if an Activity is used several
    times as a node for ImpactModel tree."""
    comment: Optional[str] = None
    "Free text for any context information about the exchange."
    switch: Optional[Switch] = None
    """Used to handle categorical parameters, allowing to map to different exchange
    parameterization depending on parameter's value. In practice, will generate one
    exchange per possible value by one-hot encoding the parameter."""

    def resolve_switch(self) -> List[SerializedExchange]:
        """
        Generates one SerializedExchange per switch option (switch option being possible
        value of corresponding categorical parameter).
        One-hot encoded representation of the parameter is multiplied to exchange's
        quantity, resulting in a exchange being toggled or not depending on the
        categorical parameter's value during execution.
        :return: one SerializedExchange per switch option.
        """
        if self.switch is None:
            return [self]
        resolved_exchanges = []
        for option in self.switch.options:
            resolved_exchange = {**dict(self)}
            resolved_exchange.update(
                {k: v for k, v in dict(option).items() if v is not None}
            )
            switch_dummy = f"{self.switch.name}_" f"{option.name}"
            resolved_exchange["name"] = f"{self.name}_{switch_dummy}"
            resolved_exchange.pop("switch")
            resolved_exchange[
                "amount"
            ] = f"({resolved_exchange['amount']})*{switch_dummy}"
            resolved_exchange = SerializedExchange(**resolved_exchange)
            resolved_exchanges.append(resolved_exchange)
        return resolved_exchanges

    def to_dict(self):
        """
        Convert self to dict.
        :return: self as a dict
        """
        input_as_dict = self.input.to_dict()
        exchange_as_dict = {k: v for k, v in dict(self).items() if v is not None}
        exchange_as_dict["input"] = input_as_dict

        return dict(exchange_as_dict)


class Switch(BaseModel):
    """
    Is used to handle categorical parameters, allowing to map to different exchange
    parameterization depending on parameter's value. In practice, will generate one
    exchange per possible value (=switch option) when resolved by one-hot encoding the
    parameter.
    """

    name: str
    "Name of the corresponding categorical parameter."
    options: List[SwitchOption]
    """One option per possible corresponding categorical parameter value, use to replace
    exchange's attribute values."""


class SwitchOption(BaseModel):
    """
    For each attribute different than None, will replace exchange's attribute value.
    For field description, please refer to SerializedExchange documentation, except for
    name.
    """

    name: str
    "Name of the corresponding categorical parameter's value."
    input: Optional[Dict[str, str]] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    amount: Optional[Union[float, str]] = None
    parameters_matching: Optional[Dict[str, Union[float, str, Dict[str, int]]]] = {}
