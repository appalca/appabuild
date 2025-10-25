"""
Setup everything required to build an ImpactModel
"""
from typing import Optional

import bw2data as bd
import bw2io as bi

from appabuild.config.appa_lca import AppaLCAConfig
from appabuild.database.databases import (
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

    if "ecoinvent" in appabuild_config.databases:
        ecoinvent_version = appabuild_config.databases["ecoinvent"].version

        ecoinvent_system_model = appabuild_config.databases["ecoinvent"].system_model
        ecoinvent_replace = appabuild_config.databases["ecoinvent"].replace
        logger.info(
            f"Loading EcoInvent database {ecoinvent_version}-{ecoinvent_system_model}..."
        )
    else:
        ecoinvent_version = None
        ecoinvent_system_model = None
        ecoinvent_replace = None
        logger.warning("No EcoInvent database in LCA conf.")
    return project_setup(
        project_name=appabuild_config.project_name,
        ecoinvent_version=ecoinvent_version,
        ecoinvent_system_model=ecoinvent_system_model,
        ecoinvent_replace=ecoinvent_replace,
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

    impact_model.to_yaml(impact_model_builder.output_path)

    return impact_model


def project_setup(
    project_name: str,
    foreground_name: str,
    foreground_path: str,
    ecoinvent_version: Optional[str] = None,
    ecoinvent_system_model: Optional[str] = None,
    ecoinvent_replace: Optional[bool] = False,
) -> ForegroundDatabase:
    """
    Triggers all Brightway functions and database import necessary to build an Impact
    Model.
    :param project_name: Brightway project name.
    :param foreground_name: how user database is referred to.
    :param foreground_path: path to folder containing user datasets.
    :param ecoinvent_version: #TODO
    :param ecoinvent_system_model: #TODO
    :param ecoinvent_replace: if set to True, EcoInvent and Biosphere DB will be recreated
    """
    bd.projects.set_current(project_name)
    databases = []
    if ecoinvent_version is not None:
        ecoinvent_database = EcoInventDatabase(
            version=ecoinvent_version,
            system_model=ecoinvent_system_model,
            replace=ecoinvent_replace,
        )
        databases.append(ecoinvent_database)

    foreground_database = ForegroundDatabase(
        name=foreground_name,
        path=foreground_path,
    )
    databases += [
        ImpactProxiesDatabase(),
        foreground_database,
    ]

    for external_database in databases:
        external_database.execute_at_startup()

    return foreground_database
