"""
Setup everything required to build an ImpactModel
"""
from typing import Optional

import brightway2 as bw

from appabuild.config.appa_lca import AppaLCAConfig
from appabuild.database.databases import (
    BiosphereDatabase,
    EcoInventDatabase,
    ForegroundDatabase,
    ImpactProxiesDatabase,
)
from appabuild.logger import logger
from appabuild.model.builder import ImpactModelBuilder


def initialize(appabuild_config_path: str) -> ForegroundDatabase:
    """
    Initialize a Brightway environment (background and foreground databases).
    :param appabuild_config_path: generic information required by Appa Build to be initialized, such
    as location of EcoInvent or name of Brightway project. This config file should
    remain the same for all your LCAs.
    :return: the initialized foreground database
    """

    appabuild_config = AppaLCAConfig.from_yaml(appabuild_config_path)

    ecoinvent_name = (
        appabuild_config.databases["ecoinvent"].name
        if "ecoinvent" in appabuild_config.databases
        else None
    )

    ecoinvent_path = (
        appabuild_config.databases["ecoinvent"].path
        if "ecoinvent" in appabuild_config.databases
        else None
    )

    if ecoinvent_path is None:
        logger.warning(
            "No path given for ecoinvent databases, building the impact model will be done without"
        )
    else:
        logger.info(f"Loading EcoInvent database from {ecoinvent_path}")

    return project_setup(
        project_name=appabuild_config.project_name,
        ecoinvent_name=ecoinvent_name,
        ecoinvent_path=ecoinvent_path,
        foreground_name=appabuild_config.databases["foreground"].name,
        foreground_path=appabuild_config.databases["foreground"].path,
    )


def build(
    lca_config_path: str, foreground_database: Optional[ForegroundDatabase] = None
):
    """
    Build an impact model for the configured functional unit and save it to the disk (to the location configured in the file).
    :param lca_config_path: information about the current LCA, such as functional unit,
    list of methods.
    :param foreground_database: database containing the LCA functional unit
    :return the impact model
    """

    impact_model_builder = ImpactModelBuilder.from_yaml(lca_config_path)

    logger.info("Start building the impact model")
    impact_model = impact_model_builder.build_impact_model(foreground_database)
    logger.info("Impact model successfully built")

    impact_model.to_yaml(
        impact_model_builder.output_path, impact_model_builder.compile_models
    )

    return impact_model


def project_setup(
    project_name: str,
    foreground_name: str,
    foreground_path: str,
    ecoinvent_name: Optional[str] = None,
    ecoinvent_path: Optional[str] = None,
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
    foreground_database = ForegroundDatabase(
        name=foreground_name,
        path=foreground_path,
    )
    databases = [
        BiosphereDatabase(),
        ImpactProxiesDatabase(),
        foreground_database,
    ]

    if ecoinvent_path is not None:
        ecoinvent_database = EcoInventDatabase(name=ecoinvent_name, path=ecoinvent_path)
        databases.append(ecoinvent_database)

    for external_database in databases:
        external_database.execute_at_startup()

    return foreground_database
