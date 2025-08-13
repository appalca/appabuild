"""
Contains classes to import LCI databases in Brightway project.
Initialize parameters_registry object which must be filled before Impact Model build.
"""

from __future__ import annotations

import abc
import json
import os
import re
from collections import ChainMap
from typing import Dict, List, Optional

import bw2data as bd
import bw2data.backends.proxies as proxies
import bw2io as bi
import yaml
from apparun.parameters import ImpactModelParam
from lca_algebraic import resetParams, setForeground
from lxml.etree import XMLSyntaxError
from pydantic_core import ValidationError

from appabuild.database.bw_databases import BwDatabase
from appabuild.database.serialized_data import SerializedActivity, SerializedExchange
from appabuild.database.user_database_elements import Activity, UserDatabaseContext
from appabuild.exceptions import BwDatabaseError, SerializedDataError
from appabuild.logger import log_validation_error, logger

parameters_registry = {}


class Database:
    """
    Abstract class of a Database. Defines two mandatory methods for import.
    """

    def __init__(self, name: str, path: Optional[str]):
        """
        Initializes a Database from its name and optionally its path.
        :param name: name of the database. Should be consistent with the name used in
        datasets.
        :param path: path of the database on disk.
        """
        self.name = name
        self.path = path

    def execute_at_startup(self) -> None:
        """
        Method to be executed when running Appa Build to import the database. Default
        behavior is to reset all params, and to run import method only if its not
        already present in Brightway project.
        :return:
        """
        resetParams(self.name)
        if self.name not in bd.databases:
            self.import_in_project()

    @abc.abstractmethod
    def import_in_project(self) -> None:
        """
        Import the database in Brightway project.
        :return:
        """
        return


class ImpactProxiesDatabase(Database):
    """
    Impact proxies are datasets used to generate impacts without communicating with
    real biosphere flows and corresponding characterization factors. It can be used to
    easily import datasets from a database not compatible with Brightway by using
    another LCA software to do impact computation, or to use data from literature which
    are often given at the impact level, and not the LCI level.
    One proxy will be created for each LCIA method. Proxy's name is
    "{bw_method_name}_technosphere_proxy".
    """

    def __init__(self):
        Database.__init__(self, name="impact_proxies", path=None)

    # def execute_at_startup(self):
    #     resetParams(self.name)
    #     if self.name not in bd.databases:
    #         # resetParams(self.name)
    #         # del bd.databases[self.name]
    #         self.import_in_project()

    def import_in_project(self) -> None:
        """
        For each LCIA method, one dataset will be created with type biosphere, and
        another one with type technosphere which will have one unit of the corresponding
        biosphere proxy as input exchange. Both are necessary as characterization factor
        has to be connected with a biosphere dataset, and a technosphere dataset is
        necessary to be used by other technosphere datasets.
        A characterization factor of one is then added between each method and the
        corresponding proxy.
        :return:
        """
        logger.info("Loading impact proxies...")
        bw_database = bd.Database(self.name)
        datasets = {}
        for method in bd.methods:
            datasets[self.name, f"{method}_proxy"] = {
                "name": f"Impact proxy for {method}",
                "unit": "unit",
                "exchanges": [],
                "type": "biosphere",
                "location": "GLO",
            }
            datasets[self.name, f"{method}_technosphere_proxy"] = {
                "name": f"Technosphere proxy for {method}",
                "unit": "unit",
                "location": "GLO",
                "production amount": 1,
                "exchanges": [
                    {
                        "type": "biosphere",
                        "amount": 1,
                        "input": [self.name, f"{method}_proxy"],
                    }
                ],
            }
        bw_database.write(datasets)
        for method in bd.methods:
            print(method)
            characterisation_factors = bd.Method(method).load()
            if (
                len(
                    [
                        cf
                        for cf in characterisation_factors
                        if cf[0] == (self.name, f"{method}_proxy")
                    ]
                )
                != 1
            ):
                characterisation_factors.append(((self.name, f"{method}_proxy"), 1))
                bd.Method(method).write(characterisation_factors)
        #
        # proxy_keys = {}
        # # Create proxy activities for each method
        # for method in bd.methods:
        #     # Create “biosphere proxy” activity
        #     act_proxy = proxies.Activity(
        #         database=self.name,
        #         code=f"{method}_proxy",
        #         name=f"Impact proxy for {method}",
        #         unit="unit",
        #         type="biosphere",
        #         location="GLO",
        #     )
        #     act_proxy.save()
        #     proxy_keys[method] = act_proxy.id
        #
        #     # Create “technosphere proxy” activity that points to the biosphere proxy
        #     technosphere_proxy = proxies.Activity(
        #         database=self.name,
        #         code=f"{method}_technosphere_proxy",
        #         name=f"Technosphere proxy for {method}",
        #         unit="unit",
        #         location="GLO",
        #         production_amount=1,
        #     )
        #     # Add one biosphere exchange pointing to the proxy
        #     technosphere_proxy.new_exchange(
        #         type="biosphere", amount=1, input=(self.name, f"{method}_proxy")
        #     )
        #     technosphere_proxy.save()
        #
        # db.process()
        # print(f"Nb elements in database {self.name}: {len(db)}")
        #
        # for method in bd.methods:
        #     characterisation_factors = bd.Method(method).load()
        #     bio_db = bd.Database("ecoinvent-3.9.1-biosphere")
        #     for cf in characterisation_factors:
        #         act = bio_db.get(cf[0])
        #         print(act)

        logger.info("Impact proxies successfully loaded")


class EcoInventDatabase(Database):
    def __init__(self):
        Database.__init__(self, "ecoinvent-3.9.1-cutoff", "")

    def execute_at_startup(self) -> None:
        resetParams(self.name)
        resetParams("biosphere3")
        if self.name not in bd.databases:
            self.import_in_project()

    def import_in_project(self):
        logger.info("Loading Eco Invent database...")
        bi.import_ecoinvent_release(
            version="3.9.1",
            system_model="cutoff",
            username="XXXX",
            password="XXXX",
            biosphere_name="biosphere3",
            biosphere_write_mode="replace",
            namespace_lcia_methods=False,
        )
        logger.info("Eco Invent database successfully loaded")


class ForegroundDatabase(Database):
    """
    Handles foreground data. Use datasets must have .json, .yaml or .yml extension to
    be imported. Dataset uuid is dataset file's name without extension.
    """

    def __init__(self, name, path):
        """
        Initializes a UserDatabase from its name, its path, its reference flow, and
        parameters if any.
        Reference flow has to be specified as import is done in a tree way with
        reference flow as a root.
        :param name: user database name
        :param path: user datasets location

        """
        Database.__init__(self, name, path)
        self.fu_name = ""
        self.parameters = []
        self.context = UserDatabaseContext(
            serialized_activities=[], activities=[], database=BwDatabase(name=name)
        )

    def set_functional_unit(self, fu_name: str, parameters: List[ImpactModelParam]):
        self.fu_name = fu_name
        self.parameters = parameters

    def find_activities_on_disk(self) -> None:
        """
        Scans database's path to import every matching file as a SerializedActivity.
        Results are stored in object's context.
        :return:
        """
        logger.info("Loading foreground datasets...")
        for root, dirs, files in os.walk(self.path):
            for filename in [
                file for file in files if re.match(r".*\.(json|ya?ml)$", file)
            ]:
                logger.info("Loading dataset %s", filename)
                filepath = os.path.join(root, filename)
                if filename.endswith(".json"):
                    dataset_file = open(filepath, "r", encoding="utf8")
                    dataset = json.load(dataset_file)
                else:
                    with open(filepath, "r") as stream:
                        dataset = yaml.safe_load(stream)
                uuid = re.sub(r"\.(json|ya?ml)", "", filename)
                try:
                    serialized_activity = SerializedActivity(
                        **{**dataset, **{"database": self.name, "uuid": uuid}}
                    )

                    # Add warnings about empty fields and
                    # infos about fields with their default value
                    for key, value in serialized_activity.__dict__.items():
                        if type(value) in [list, dict, tuple] and len(value) == 0:
                            logger.warning("The field %s is empty", key)
                        elif key not in dataset:
                            logger.info(
                                "The field %s has its default value %s", key, value
                            )

                except ValidationError as e:
                    log_validation_error(e)
                    raise e
                self.context.serialized_activities.append(serialized_activity)
                logger.info("Dataset %s successfully loaded", filename)
        logger.info("Foreground datasets successfully loaded")

    def execute_at_startup(self):
        if self.name in bd.databases:
            resetParams(self.name)
            del bd.databases[self.name]

        self.find_activities_on_disk()

    def execute_at_build_time(self):
        self.declare_parameters()
        self.import_in_project()

    def import_in_project(self) -> None:
        """
        Import user database in Brightway project. Database is declared as foreground
        for lca_algebraic.
        This method will transform each used dataset from SerializedActivity and
        SerializedExchange to Activity and Exchange objects.
        Parameters are then propagated from the reference flow to the leaf activities.
        :return:
        """
        bw_database = bd.Database(self.name)
        serialized_fu = [
            serialized_activity
            for serialized_activity in self.context.serialized_activities
            if serialized_activity.name == self.fu_name
        ]
        if len(serialized_fu) > 1:
            raise SerializedDataError(
                f"Too many serialized activities matching for fu name {self.fu_name}."
            )
        if len(serialized_fu) < 1:
            raise SerializedDataError(
                f"No serialized activity matching for fu name {self.fu_name}."
            )
        serialized_fu = serialized_fu[0]
        fu = Activity.from_serialized_activity(serialized_fu, context=self.context)
        fu.propagate_parameters(context=self.context)
        fu.propagate_include_in_tree(context=self.context)
        to_write_activities = [
            activity.to_bw_format() for activity in self.context.activities
        ]
        bw_database.write(dict(to_write_activities))
        setForeground(self.name)

    def declare_parameters(self) -> None:
        """
        Initialize each object's parameter as a ImpactModelParam and store it in
        parameters_registry object. parameters_registry is used to build Impact Model's
        parameters section.
        :return:
        """
        for parameter in self.parameters:
            parameters_registry[parameter.name] = parameter
