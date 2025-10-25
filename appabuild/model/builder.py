"""
Module containing all required classes and methods to run LCA and build impact models.
Majority of the code is copied and adapted from lca_algebraic package.
"""

from __future__ import annotations

import itertools
import logging
import os
from typing import List, Optional, Set, Tuple

import bw2data as bd
import lca_algebraic as lcaa
from apparun.impact_methods import MethodFullName
from apparun.impact_model import ImpactModel, ModelMetadata
from apparun.impact_tree import ImpactTreeNode
from apparun.parameters import EnumParam, FloatParam, ImpactModelParams
from apparun.tree_node import NodeProperties
from lca_algebraic import ActivityExtended
from lca_algebraic.base_utils import _getDb
from lca_algebraic.params import (
    _getAmountOrFormula,
    _param_registry,
    newEnumParam,
    newFloatParam,
)
from sympy.parsing.sympy_parser import parse_expr

from appabuild.config.lca import LCAConfig
from appabuild.database.databases import ForegroundDatabase
from appabuild.exceptions import (
    BwDatabaseError,
    BwMethodError,
    ForegroundDatabaseError,
    ParameterError,
)
from appabuild.logger import logger


def to_bw_method(method_full_name: MethodFullName) -> Tuple[str, str, str]:
    """
    Find corresponding method as known by Brightway.
    :param method_full_name: method to be found.
    :return: Brightway representation of the method.
    """
    matching_methods = [
        method for method in bd.methods if method_full_name in str(method)
    ]
    try:
        if len(matching_methods) < 1:
            raise BwMethodError(f"Cannot find method {method_full_name}.")
        if len(matching_methods) > 1:
            raise BwMethodError(
                f"Too many methods matching {method_full_name}: {matching_methods}."
            )
    except BwMethodError as e:
        logger.exception(e)
        raise e

    return matching_methods[0]


class ImpactModelBuilder:
    """
    Main purpose of this class is to build Impact Models.
    """

    def __init__(
        self,
        user_database_name: str,
        functional_unit: str,
        methods: list[str],
        output_path: str,
        metadata: Optional[ModelMetadata] = ModelMetadata(),
        parameters: Optional[ImpactModelParams] = None,
    ):
        """
        Initialize the model builder
        :param user_database_name: name of the user database (foreground database)
        :param functional_unit: uuid of the activity producing the reference flow.
        :param methods: list of methods to generate arithmetic models for.
            Expected method format is Appa Run method keys.
        :param metadata: information about the LCA behind the impact model.
            Should contain, or link to all information necessary for the end user's
            proper understanding of the impact model.
        :param parameters: an ImpactModelParam object will have to be created for each
        parameter used in all used datasets. See ImpactModelParam attributes to know
        required fields.
        """
        self.user_database_name = user_database_name
        self.functional_unit = functional_unit
        self.parameters = parameters
        self.methods = methods
        self.metadata = metadata
        self.output_path = output_path
        self.bw_user_database = bd.Database(self.user_database_name)

    @staticmethod
    def from_yaml(lca_config_path: str) -> ImpactModelBuilder:
        """
        Initializes a build with information contained in a YAML config file
        :param lca_config_path: path to the file holding the config.
        :return: the Impact Model Builder
        """
        lca_config = LCAConfig.from_yaml(lca_config_path)

        builder = ImpactModelBuilder(
            lca_config.scope.fu.database,
            lca_config.scope.fu.name,
            lca_config.scope.methods,
            os.path.join(
                lca_config.model.path,
                lca_config.model.name + ".yaml",
            ),
            lca_config.model.metadata,
            ImpactModelParams.from_list(lca_config.model.parameters),
        )
        return builder

    def build_impact_model(
        self, foreground_database: Optional[ForegroundDatabase] = None
    ) -> ImpactModel:
        """
        Build an Impact Model, the model is a represented as a tree with the functional unit as its root
        :param foreground_database: database containing the functional unit
        :return: built impact model.
        """
        if foreground_database is not None:
            foreground_database.set_functional_unit(
                self.functional_unit, self.parameters
            )
            foreground_database.execute_at_build_time()

        functional_unit_bw = self.find_activity_in_bw(self.functional_unit)
        methods_bw = {
            method: to_bw_method(MethodFullName[method]) for method in self.methods
        }

        root_node = ImpactTreeNode(
            name=functional_unit_bw["name"],
            amount=1,
            properties=NodeProperties.from_dict(functional_unit_bw["properties"]),
        )
        self.declare_parameters_in_lcaa()
        self.build_tree_node(root_node)
        free_symbols = set()
        self.compute_node_models(root_node, methods_bw, free_symbols)
        self.check_symbols_are_known_parameters(free_symbols)

        impact_model = ImpactModel(
            tree=root_node, parameters=self.parameters, metadata=self.metadata
        )
        return impact_model

    def check_symbols_are_known_parameters(self, symbols_in_amount: Set[str]):
        # Check if each symbol corresponds to a known parameter

        # TODO move that in a FloatParam method
        params_in_default = [
            parameter.default
            for parameter in self.parameters
            if parameter.type == "float"
            and (
                isinstance(parameter.default, str)
                or isinstance(parameter.default, dict)
            )
        ]
        while (
            len(
                [
                    parameter
                    for parameter in params_in_default
                    if isinstance(parameter, dict)
                ]
            )
            > 0
        ):
            params_in_default_str = [
                parameter
                for parameter in params_in_default
                if isinstance(parameter, str)
            ]
            params_in_default_dict = [
                [value for value in parameter.values()]
                for parameter in params_in_default
                if isinstance(parameter, dict)
            ]
            params_in_default = (
                list(itertools.chain.from_iterable(params_in_default_dict))
                + params_in_default_str
            )
        params_in_default = [
            parameter for parameter in params_in_default if isinstance(parameter, str)
        ]  # there can be int params at this point

        symbols_in_default = set(
            [
                str(symb)
                for symb in list(
                    itertools.chain.from_iterable(
                        [
                            parse_expr(params_in_default).free_symbols
                            for params_in_default in params_in_default
                        ]
                    )
                )
            ]
        )

        free_symbols = symbols_in_amount.union(symbols_in_default)
        for free_symbol in free_symbols:
            try:
                self.parameters.find_corresponding_parameter(free_symbol)
            except ValueError:
                e = (
                    f"ParameterError: {free_symbol} is required in the impact"
                    f" model but is unknown in the config. Please check in the LCA "
                    f"config."
                )
                logger.error(e)
                raise ParameterError(e)

    def declare_parameters_in_lcaa(self):
        """
        Declare used parameters in conf file as a lca_algebraic parameter to enable
        model building (will not be used afterwards)
        """

        for parameter in self.parameters:
            if parameter.name in _param_registry().keys():
                e = f"Parameter {parameter.name} already in lcaa registry."
                logging.error(e)
                raise ParameterError(e)
            if isinstance(parameter, FloatParam):
                newFloatParam(
                    name=parameter.name,
                    default=parameter.default,
                    save=False,
                    dbname=self.user_database_name,
                    min=0.0,
                )
            if isinstance(parameter, EnumParam):
                newEnumParam(
                    name=parameter.name,
                    values=parameter.weights,
                    default=parameter.default,
                    dbname=self.user_database_name,
                )

    def build_tree_node(self, tree_node: ImpactTreeNode):
        act = self.find_activity_in_bw(tree_node.name)
        for exch in act.exchanges():
            input_db, input_code = exch["input"]
            if input_db == self.user_database_name:
                sub_act = _getDb(input_db).get(input_code)
                if tree_node.name_already_in_tree(sub_act.get("name")):
                    e = f"Found recursive activity: {sub_act.get('name')}"
                    logger.exception(e)
                    raise ForegroundDatabaseError(e)
                if sub_act.get("include_in_tree"):
                    amount = _getAmountOrFormula(exch)
                    child_tree_node = tree_node.new_child(
                        name=sub_act["name"],
                        amount=amount,
                        properties=NodeProperties.from_dict(sub_act["properties"]),
                    )
                    self.build_tree_node(child_tree_node)

    def compute_node_models(
        self, tree_node: ImpactTreeNode, methods, free_symbols: Set
    ):
        act = self.find_activity_in_bw(tree_node.name)
        models, param_symbols = lcaa.lca._modelToExpr(
            act, methods=list(methods.values())
        )
        param_symbols = [
            param_symbol
            for param_symbol in param_symbols
            if not param_symbol.endswith("_default")
        ]
        free_symbols.update(set(param_symbols))
        tree_node.models = {
            list(methods.keys())[i]: tree_node.combined_amount * models[i]
            for i in range(len(methods.keys()))
        }
        for child in tree_node.children:
            self.compute_node_models(child, methods, free_symbols)

    def find_activity_in_bw(self, activity_name) -> ActivityExtended:
        """
        Find the bw activity matching the functional unit in the bw database. A single activity
        should be found as it is to be used as the root of the tree.
        """
        act = [i for i in self.bw_user_database if activity_name == i["name"]]
        try:
            if len(act) < 1:
                raise BwDatabaseError(f"Cannot find activity {activity_name} for FU.")
            if len(act) > 1:
                raise BwDatabaseError(f"Too many activities matching {activity_name}.")
        except BwDatabaseError:
            logger.exception("BwDatabaseError")
            raise
        act = act[0]
        return act
