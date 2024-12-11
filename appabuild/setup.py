"""
Setup everything required to build an ImpactModel
"""
import brightway2 as bw

from appabuild.database.databases import (
    BiosphereDatabase,
    EcoInventDatabase,
    ImpactProxiesDatabase,
    UserDatabase,
)


def project_setup(
    project_name: str,
    ecoinvent_name: str,
    ecoinvent_path: str,
    foreground_name: str,
    foreground_path: str,
    fu_name: str,
    parameters: dict,
):
    """
    Triggers all Brightway functions and database import necessary to build an Impact
    Model.
    :param project_name: Brightway project name.
    :param ecoinvent_name: how EcoInvent is referred to in user datasets.
    :param ecoinvent_path: path to EcoInvent database.
    :param foreground_name: how user database is referred to.
    :param foreground_path: path to folder containing user datasets.
    :param fu_name: name of the functional unit, i.e. activity producing the reference
    flow.
    :param parameters: an ImpactModelParam object will have to be created for each
    parameter used in all used datasets. See ImpactModelParam attributes to know
    required fields.
    :return:
    """
    bw.projects.set_current(project_name)
    databases = [
        BiosphereDatabase(),
        ImpactProxiesDatabase(),
        EcoInventDatabase(name=ecoinvent_name, path=ecoinvent_path),
        UserDatabase(
            name=foreground_name,
            path=foreground_path,
            fu_name=fu_name,
            parameters=parameters,
        ),
    ]

    for external_database in databases:
        external_database.execute_at_startup()
