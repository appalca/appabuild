"""
Setup everything required to build an ImpactModel
"""
from typing import Optional

import brightway2 as bw
import yaml

from appabuild.database.databases import (
    BiosphereDatabase,
    EcoInventDatabase,
    ImpactProxiesDatabase,
    ForegroundDatabase,
)
from appabuild.model.builder import ImpactModelBuilder


def initialize(appabuild_config_path: str) -> ForegroundDatabase:
    """
    Initialize a Brightway environment (background and foreground databases).
    :param appabuild_config_path: generic information required by Appa Build to be initialized, such
    as location of EcoInvent or name of Brightway project. This config file should
    remain the same for all your LCAs.
    :return: the initialized foreground database
    """
    with open(appabuild_config_path, "r") as stream:
        appabuild_config = yaml.safe_load(stream)

    return project_setup(
        project_name=appabuild_config["project_name"],
        ecoinvent_name=appabuild_config["databases"]["ecoinvent"]["name"],
        ecoinvent_path=appabuild_config["databases"]["ecoinvent"]["path"],
        foreground_name=appabuild_config["databases"]["foreground"]["name"],
        foreground_path=appabuild_config["databases"]["foreground"]["path"],
    )


def do_build(lca_config_path: str, foreground_database: Optional[ForegroundDatabase] = None):
    """
    Build an impact model for the configured functional unit and save it to the disk (to the location configured in the file).
    :param lca_config_path: information about the current LCA, such as functional unit,
    list of methods.
    :param foreground_database: database containing the LCA functional unit
    :return the impact model
    """

    impact_model_builder = ImpactModelBuilder.from_yaml(lca_config_path)

    impact_model = impact_model_builder.build_impact_model(foreground_database)

    impact_model.to_yaml(
        impact_model_builder.output_path,
        impact_model_builder.compile_models
    )

    return impact_model


def project_setup(
        project_name: str,
        ecoinvent_name: str,
        ecoinvent_path: str,
        foreground_name: str,
        foreground_path: str,
) -> ForegroundDatabase:
    """
    Triggers all Brightway functions and database import necessary to build an Impact
    Model.
    :param project_name: Brightway project name.
    :param ecoinvent_name: how EcoInvent is referred to in user datasets.
    :param ecoinvent_path: path to EcoInvent database.
    :param foreground_name: how user database is referred to.
    :param foreground_path: path to folder containing user datasets.
    """
    bw.projects.set_current(project_name)
    databases = [
        BiosphereDatabase(),
        ImpactProxiesDatabase(),
        EcoInventDatabase(name=ecoinvent_name, path=ecoinvent_path),
        ForegroundDatabase(
            name=foreground_name,
            path=foreground_path,
        ),
    ]

    for external_database in databases:
        external_database.execute_at_startup()

    return databases[3]
